from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Job, Candidatura, UserProfile, Pergunta, Resposta, Avaliacao, Apresentacao
from .forms import CadastroForm
import datetime
import math

from pathlib import Path
from django.templatetags.static import static
from django.utils.encoding import iri_to_uri


def _get_landing_gallery_items(max_items: int = 18):
    base_dir = Path(settings.BASE_DIR)
    static_dir = base_dir / 'static' / 'images' / 'promotores'

    # Fallback para o diretório original, caso o static não exista (dev).
    fallback_dir = base_dir / 'imagens_promotores_paginainicial'

    image_dir = static_dir if static_dir.exists() else fallback_dir
    if not image_dir.exists():
        return []

    exts = {'.jpg', '.jpeg', '.png', '.webp'}
    filenames = sorted(
        [p.name for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    )

    client_names = [
        'Mercado Livre',
        'Assaí Atacadista',
        'L’Oréal',
        'Google',
        'Disney+',
        'Uber',
        'Vivo',
        'Petz',
        'Asics',
        'Oxxo',
        'Nubank',
        'Logitech',
    ]

    role_names = [
        'Equipe',
        'Promoção',
        'Recepção',
        'Captação de leads',
        'Ativação de marca',
    ]

    items = []
    for idx, name in enumerate(filenames[:max_items]):
        # Se veio do fallback_dir, ainda assim geramos URL de static (se o deploy usar copy, funciona).
        raw_url = (
            static(f'images/promotores/{name}')
            if image_dir == static_dir
            else f'/imagens_promotores_paginainicial/{name}'
        )
        image_url = iri_to_uri(raw_url)
        items.append(
            {
                'image_url': image_url,
                'client_name': client_names[idx % len(client_names)],
                'role_name': role_names[idx % len(role_names)],
            }
        )
    return items

# --- 1. HOME (LANDING PAGE) ---
def home(request):
    if request.user.is_superuser:
        return redirect('lista_vagas')

    if request.user.is_authenticated:
        try:
            if request.user.userprofile.status == 'aprovado':
                return redirect('lista_vagas')
        except UserProfile.DoesNotExist:
            pass 
            
    context = {
        'landing_gallery': _get_landing_gallery_items(max_items=18),
    }
    return render(request, 'landing.html', context)


def quem_somos(request):
    return render(request, 'quem_somos.html')


def privacidade(request):
    return render(request, 'privacidade.html')


def _idade_em_anos(data_nascimento):
    if not data_nascimento:
        return None
    try:
        hoje = timezone.now().date()
        anos = hoje.year - data_nascimento.year
        if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
            anos -= 1
        return max(0, anos)
    except Exception:
        return None


def _instagram_normalizado(instagram_raw: str | None):
    raw = (instagram_raw or '').strip()
    if not raw:
        return (None, None)

    text = raw
    if raw.startswith('http://') or raw.startswith('https://'):
        return (text, raw)

    handle = raw
    if handle.startswith('@'):
        handle = handle[1:]
    handle = handle.strip().lstrip('/')
    if not handle:
        return (text, None)

    url = f"https://instagram.com/{handle}"
    return (text, url)


def apresentacao_publica(request, uuid):
    ap = get_object_or_404(Apresentacao, uuid=uuid)
    if ap.expira_em and ap.expira_em <= timezone.now():
        return render(request, 'apresentacao_expirada.html')

    itens_qs = ap.itens.select_related('promotor').all().order_by('ordem', 'id')

    itens = []
    for it in itens_qs:
        p = it.promotor

        foto_rosto_url = None
        foto_corpo_url = None
        try:
            foto_rosto_url = p.foto_rosto.url if getattr(p, 'foto_rosto', None) else None
        except Exception:
            foto_rosto_url = None
        try:
            foto_corpo_url = p.foto_corpo.url if getattr(p, 'foto_corpo', None) else None
        except Exception:
            foto_corpo_url = None

        ig_text, ig_url = _instagram_normalizado(getattr(p, 'instagram', None))

        itens.append(
            {
                'nome': getattr(p, 'nome_completo', '') or '',
                'idade': _idade_em_anos(getattr(p, 'data_nascimento', None)),
                'altura': str(getattr(p, 'altura', '') or '').replace(',', '.'),
                'manequim': getattr(p, 'manequim', None),
                'calcado': getattr(p, 'calcado', None),
                'cidade': getattr(p, 'cidade', None),
                'uf': getattr(p, 'estado', None),
                'instagram': ig_text,
                'instagram_url': ig_url,
                'foto_rosto_url': foto_rosto_url,
                'foto_corpo_url': foto_corpo_url,
            }
        )

    return render(request, 'apresentacao_publica.html', {'itens': itens, 'apresentacao': ap})

# --- 2. DASHBOARD / MURAL DE VAGAS ---
@login_required(login_url='/login/')
def lista_vagas(request):
    # Admin: Vê lista simples
    if request.user.is_superuser:
        jobs = Job.objects.all().order_by('-criado_em')
        return render(request, 'job_list.html', {'jobs': jobs, 'is_admin': True})

    # Modelo: Verifica Perfil
    try:
        perfil = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('cadastro')

    # Redireciona se não aprovado
    if perfil.status == 'pendente':
        return render(request, 'aguardando_aprovacao.html')
    elif perfil.status == 'correcao':
        messages.warning(request, "Seu cadastro precisa de ajustes antes de seguir.")
        return redirect('editar_perfil')
    elif perfil.status == 'reprovado':
        hoje = timezone.now().date()
        # Se existe bloqueio e já expirou, volta para pendente automaticamente
        if getattr(perfil, 'bloqueado_ate', None) and perfil.bloqueado_ate <= hoje:
            perfil.status = 'pendente'
            perfil.bloqueado_ate = None
            perfil.save()
            messages.info(request, "Você já pode tentar novamente. Atualize seu cadastro.")
            return redirect('editar_perfil')

        dias_restantes = None
        if getattr(perfil, 'bloqueado_ate', None) and perfil.bloqueado_ate > hoje:
            dias_restantes = (perfil.bloqueado_ate - hoje).days
        return render(request, 'reprovado.html', {'perfil': perfil, 'dias_restantes': dias_restantes})

    # --- LÓGICA DO DASHBOARD ---
    
    # 1. Identificar vagas já candidatadas
    ids_candidaturas = Candidatura.objects.filter(modelo=perfil).values_list('job_id', flat=True)
    
    # 2. Vagas Disponíveis (Abertas e Não Candidatadas)
    vagas_disponiveis_qs = Job.objects.filter(status='aberto').exclude(id__in=ids_candidaturas).order_by('-criado_em')

    # 3. Histórico de Atividades
    meus_eventos = Candidatura.objects.filter(modelo=perfil).order_by('-data_candidatura')

    # 4. Cálculo de Progresso (Gamificação)
    progresso = 50 
    if perfil.foto_rosto: progresso += 25
    if perfil.foto_corpo: progresso += 25
    progresso = min(progresso, 100)
    
    def _haversine_km(lat1, lon1, lat2, lon2):
        r = 6371.0
        p1 = math.radians(float(lat1))
        p2 = math.radians(float(lat2))
        dp = math.radians(float(lat2) - float(lat1))
        dl = math.radians(float(lon2) - float(lon1))
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def _parse_csv_set(raw: str):
        raw = (raw or '').strip()
        if not raw:
            return set()
        return {p.strip() for p in raw.replace('\n', ',').split(',') if p and p.strip()}

    def _parse_areas(raw: str):
        # Aceita tokens ou labels legados; ignora "Outros: ..."
        raw = (raw or '').strip()
        if not raw:
            return set()
        raw = raw.split('Outros:', 1)[0]
        parts = [p.strip() for p in raw.split(',') if p and p.strip()]
        allowed = {k for (k, _lbl) in UserProfile.AREAS_ATUACAO_CHOICES}
        label_to_value = {str(lbl).casefold(): val for val, lbl in UserProfile.AREAS_ATUACAO_CHOICES}
        out = set()
        for part in parts:
            if part in allowed:
                out.add(part)
                continue
            mapped = label_to_value.get(str(part).casefold())
            if mapped:
                out.add(mapped)
        return out

    def _idioma_rank(val: str | None) -> int:
        order = {'basico': 1, 'intermediario': 2, 'fluente': 3}
        return order.get(val or '', 0)

    def _fit_info(job: Job, perfil: UserProfile):
        total = 0
        passed = 0

        # Tipo de serviço
        job_serv = _parse_areas(job.tipo_servico)
        if job_serv:
            total += 1
            perfil_serv = _parse_areas(perfil.areas_atuacao)
            if perfil_serv.intersection(job_serv):
                passed += 1

        # Experiência
        if getattr(job, 'requer_experiencia', False):
            total += 1
            if (perfil.experiencia or '') != 'sem_experiencia':
                passed += 1

        # Sexo/Gênero
        generos = _parse_csv_set(job.generos_aceitos)
        if generos:
            total += 1
            if (perfil.genero or '') in generos:
                passed += 1

        # Etnia
        etnias = _parse_csv_set(job.etnias_aceitas)
        if etnias:
            total += 1
            if (perfil.etnia or '') in etnias:
                passed += 1

        # Cor dos olhos
        olhos = _parse_csv_set(getattr(job, 'olhos_aceitos', '') or '')
        if olhos:
            total += 1
            if (perfil.olhos or '') in olhos:
                passed += 1

        # Tipo de cabelo
        cabelo_tipos = _parse_csv_set(getattr(job, 'cabelo_tipos_aceitos', '') or '')
        if cabelo_tipos:
            total += 1
            if (perfil.cabelo_tipo or '') in cabelo_tipos:
                passed += 1

        # Comprimento do cabelo
        cabelo_comps = _parse_csv_set(getattr(job, 'cabelo_comprimentos_aceitos', '') or '')
        if cabelo_comps:
            total += 1
            if (getattr(perfil, 'cabelo_comprimento', None) or '') in cabelo_comps:
                passed += 1

        # Inglês mínimo
        if job.nivel_ingles_min:
            total += 1
            if _idioma_rank(perfil.nivel_ingles) >= _idioma_rank(job.nivel_ingles_min):
                passed += 1

        if total == 0:
            return {
                'status': 'good',
                'message': 'Sem exigências obrigatórias — seu perfil pode se candidatar.',
                'passed': 0,
                'total': 0,
            }

        if passed == total:
            return {
                'status': 'good',
                'message': 'Seu perfil atende aos requisitos.',
                'passed': passed,
                'total': total,
            }

        missing = total - passed
        if missing <= 1 or (passed / total) >= 0.7:
            return {
                'status': 'almost',
                'message': 'Seu perfil atende a quase todos requisitos.',
                'passed': passed,
                'total': total,
            }

        return {
            'status': 'bad',
            'message': 'Seu perfil não atende aos requisitos.',
            'passed': passed,
            'total': total,
        }

    vagas_disponiveis = list(vagas_disponiveis_qs.prefetch_related('dias'))
    perfil_lat = getattr(perfil, 'latitude', None)
    perfil_lon = getattr(perfil, 'longitude', None)

    for job in vagas_disponiveis:
        # Distância
        job.distance_km = None
        if perfil_lat is not None and perfil_lon is not None and getattr(job, 'latitude', None) is not None and getattr(job, 'longitude', None) is not None:
            try:
                job.distance_km = round(_haversine_km(perfil_lat, perfil_lon, job.latitude, job.longitude), 1)
            except Exception:
                job.distance_km = None

        # Próximo dia/horário (para destaque)
        try:
            job.next_dia = job.dias.order_by('data').first()
        except Exception:
            job.next_dia = None

        # Compatibilidade
        job.fit = _fit_info(job, perfil)

        # Labels de tipo de serviço para exibição
        try:
            choice_map = dict(UserProfile.AREAS_ATUACAO_CHOICES)
            job.tipo_servico_labels = [choice_map.get(t, t) for t in sorted(_parse_areas(job.tipo_servico))]
        except Exception:
            job.tipo_servico_labels = []

    context = {
        'perfil': perfil,
        'vagas_disponiveis': vagas_disponiveis,
        'meus_eventos': meus_eventos,
        'progresso': progresso,
        'nota_media': perfil.nota_media(),
        'total_jobs': perfil.total_jobs(),
        'total_avaliacoes': perfil.avaliacoes.count(),
        'is_admin': False
    }
    
    return render(request, 'job_list.html', context)

# --- 3. DETALHES DA VAGA ---
@login_required(login_url='/login/')
def detalhe_vaga(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    def _haversine_km(lat1, lon1, lat2, lon2):
        r = 6371.0
        p1 = math.radians(float(lat1))
        p2 = math.radians(float(lat2))
        dp = math.radians(float(lat2) - float(lat1))
        dl = math.radians(float(lon2) - float(lon1))
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def _parse_csv_set(raw: str):
        raw = (raw or '').strip()
        if not raw:
            return set()
        return {p.strip() for p in raw.replace('\n', ',').split(',') if p and p.strip()}

    def _parse_areas(raw: str):
        raw = (raw or '').strip()
        if not raw:
            return set()
        raw = raw.split('Outros:', 1)[0]
        parts = [p.strip() for p in raw.split(',') if p and p.strip()]
        allowed = {k for (k, _lbl) in UserProfile.AREAS_ATUACAO_CHOICES}
        label_to_value = {str(lbl).casefold(): val for val, lbl in UserProfile.AREAS_ATUACAO_CHOICES}
        out = set()
        for part in parts:
            if part in allowed:
                out.add(part)
                continue
            mapped = label_to_value.get(str(part).casefold())
            if mapped:
                out.add(mapped)
        return out

    def _idioma_rank(val: str | None) -> int:
        order = {'basico': 1, 'intermediario': 2, 'fluente': 3}
        return order.get(val or '', 0)

    def _fit_info(job: Job, perfil: UserProfile):
        total = 0
        passed = 0

        job_serv = _parse_areas(job.tipo_servico)
        if job_serv:
            total += 1
            perfil_serv = _parse_areas(perfil.areas_atuacao)
            if perfil_serv.intersection(job_serv):
                passed += 1

        if getattr(job, 'requer_experiencia', False):
            total += 1
            if (perfil.experiencia or '') != 'sem_experiencia':
                passed += 1

        generos = _parse_csv_set(job.generos_aceitos)
        if generos:
            total += 1
            if (perfil.genero or '') in generos:
                passed += 1

        etnias = _parse_csv_set(job.etnias_aceitas)
        if etnias:
            total += 1
            if (perfil.etnia or '') in etnias:
                passed += 1

        olhos = _parse_csv_set(getattr(job, 'olhos_aceitos', '') or '')
        if olhos:
            total += 1
            if (perfil.olhos or '') in olhos:
                passed += 1

        cabelo_tipos = _parse_csv_set(getattr(job, 'cabelo_tipos_aceitos', '') or '')
        if cabelo_tipos:
            total += 1
            if (perfil.cabelo_tipo or '') in cabelo_tipos:
                passed += 1

        cabelo_comps = _parse_csv_set(getattr(job, 'cabelo_comprimentos_aceitos', '') or '')
        if cabelo_comps:
            total += 1
            if (getattr(perfil, 'cabelo_comprimento', None) or '') in cabelo_comps:
                passed += 1

        if job.nivel_ingles_min:
            total += 1
            if _idioma_rank(perfil.nivel_ingles) >= _idioma_rank(job.nivel_ingles_min):
                passed += 1

        if total == 0:
            return {
                'status': 'good',
                'message': 'Sem exigências obrigatórias — seu perfil pode se candidatar.',
                'passed': 0,
                'total': 0,
            }

        if passed == total:
            return {
                'status': 'good',
                'message': 'Seu perfil atende aos requisitos.',
                'passed': passed,
                'total': total,
            }

        missing = total - passed
        if missing <= 1 or (passed / total) >= 0.7:
            return {
                'status': 'almost',
                'message': 'Seu perfil atende a quase todos requisitos.',
                'passed': passed,
                'total': total,
            }

        return {
            'status': 'bad',
            'message': 'Seu perfil não atende aos requisitos.',
            'passed': passed,
            'total': total,
        }

    dias = job.dias.all().order_by('data')

    # Admin: só exibe detalhe
    if request.user.is_superuser:
        return render(request, 'job_detail.html', {
            'job': job,
            'dias': dias,
            'ja_candidatou': False,
        })

    try:
        perfil = request.user.userprofile
        if perfil.status != 'aprovado':
            return redirect('lista_vagas')
            
        dias = job.dias.all()
        ja_candidatou = Candidatura.objects.filter(job=job, modelo=perfil).exists()

        # Requisitos para exibição (somente os selecionados)
        requirements = []
        try:
            choice_map = dict(UserProfile.AREAS_ATUACAO_CHOICES)
            serv_labels = [choice_map.get(t, t) for t in sorted(_parse_areas(job.tipo_servico))]
            outros_txt = (getattr(job, 'tipo_servico_outros', '') or '').strip()
            if outros_txt:
                serv_labels.append(outros_txt)
            if serv_labels:
                requirements.append(('Tipo de serviço', ', '.join(serv_labels)))
        except Exception:
            pass

        if getattr(job, 'requer_experiencia', False):
            requirements.append(('Experiência', 'Precisa ter experiência'))

        generos = sorted(_parse_csv_set(job.generos_aceitos))
        if generos:
            gen_labels = {'masculino': 'Masculino', 'feminino': 'Feminino'}
            requirements.append(('Sexo', ', '.join([gen_labels.get(g, g) for g in generos])))

        etnias = sorted(_parse_csv_set(job.etnias_aceitas))
        if etnias:
            et_map = dict(UserProfile.ETNIA_CHOICES)
            requirements.append(('Cor/Etnia', ', '.join([et_map.get(e, e) for e in etnias])))

        olhos = sorted(_parse_csv_set(getattr(job, 'olhos_aceitos', '') or ''))
        if olhos:
            o_map = dict(UserProfile.OLHOS_CHOICES)
            requirements.append(('Cor dos olhos', ', '.join([o_map.get(o, o) for o in olhos])))

        cabelo_tipos = sorted(_parse_csv_set(getattr(job, 'cabelo_tipos_aceitos', '') or ''))
        if cabelo_tipos:
            c_map = dict(UserProfile.CABELO_TIPO_CHOICES)
            requirements.append(('Tipo de cabelo', ', '.join([c_map.get(c, c) for c in cabelo_tipos])))

        cabelo_comps = sorted(_parse_csv_set(getattr(job, 'cabelo_comprimentos_aceitos', '') or ''))
        if cabelo_comps:
            cc_map = dict(UserProfile.CABELO_TAM_CHOICES)
            requirements.append(('Comprimento do cabelo', ', '.join([cc_map.get(c, c) for c in cabelo_comps])))

        if job.nivel_ingles_min:
            requirements.append(('Inglês', f"Mínimo: {job.get_nivel_ingles_min_display()}"))

        comps = (job.competencias or '').strip()
        if comps:
            requirements.append(('Competências', comps))

        # Distância e compatibilidade
        distance_km = None
        if getattr(perfil, 'latitude', None) is not None and getattr(perfil, 'longitude', None) is not None and getattr(job, 'latitude', None) is not None and getattr(job, 'longitude', None) is not None:
            try:
                distance_km = round(_haversine_km(perfil.latitude, perfil.longitude, job.latitude, job.longitude), 1)
            except Exception:
                distance_km = None

        fit = _fit_info(job, perfil)

        return render(request, 'job_detail.html', {
            'job': job,
            'dias': dias,
            'ja_candidatou': ja_candidatou,
            'perfil': perfil,
            'distance_km': distance_km,
            'fit': fit,
            'requirements': requirements,
        })
    except UserProfile.DoesNotExist:
        return redirect('cadastro')

# --- 4. CANDIDATAR ---
@login_required
def candidatar_vaga(request, job_id):
    if request.user.is_superuser:
        messages.info(request, "Administradores não se candidatam.")
        return redirect('detalhe_vaga', job_id=job_id)

    job = get_object_or_404(Job, id=job_id)
    try:
        perfil = request.user.userprofile
        if perfil.status != 'aprovado':
            messages.error(request, "Seu cadastro não está aprovado.")
            return redirect('lista_vagas')

        Candidatura.objects.create(job=job, modelo=perfil)
        messages.success(request, "Candidatura realizada com sucesso! Boa sorte 🍀")
    except Exception:
        messages.warning(request, "Você já se candidatou para esta vaga.")
    
    return redirect('detalhe_vaga', job_id=job.id)

# --- 5. CADASTRO ---
def cadastro(request):
    if request.user.is_superuser: return redirect('lista_vagas')
    if request.user.is_authenticated:
        try:
            request.user.userprofile
            return redirect('lista_vagas')
        except UserProfile.DoesNotExist: pass 

    perguntas_extras = Pergunta.objects.filter(ativa=True)

    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            if User.objects.filter(username=email).exists():
                messages.error(request, "Este e-mail já está cadastrado.")
                return render(request, 'cadastro.html', {'form': form, 'perguntas_extras': perguntas_extras})

            user = User.objects.create_user(username=email, email=email, password=password)
            perfil = form.save(commit=False)
            perfil.user = user
            perfil.status = 'pendente'
            perfil.save()
            
            for pergunta in perguntas_extras:
                resposta = request.POST.get(f'pergunta_{pergunta.id}')
                if resposta: Resposta.objects.create(perfil=perfil, pergunta=pergunta, texto_resposta=resposta)

            login(request, user)
            saudacao = "Bem-vindo(a)"
            if perfil.genero == 'feminino':
                saudacao = "Bem-vinda"
            elif perfil.genero == 'masculino':
                saudacao = "Bem-vindo"
            messages.success(request, f"{saudacao}, {perfil.nome_completo}! Aguarde a análise.")
            return redirect('lista_vagas')
    else:
        form = CadastroForm()

    return render(request, 'cadastro.html', {'form': form, 'perguntas_extras': perguntas_extras})

# --- 6. EDITAR PERFIL ---
@login_required
def editar_perfil(request):
    if request.user.is_superuser: return redirect('lista_vagas')
    try:
        perfil = request.user.userprofile
    except UserProfile.DoesNotExist: return redirect('cadastro')

    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            obj = form.save(commit=False)
            # Se estava em correção, ao salvar volta para pendente (reanálise)
            if obj.status == 'correcao':
                obj.status = 'pendente'
                obj.motivo_reprovacao = None
                obj.observacao_admin = None
                obj.data_reprovacao = None
                if hasattr(obj, 'bloqueado_ate'):
                    obj.bloqueado_ate = None
            obj.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('lista_vagas')
    else:
        form = CadastroForm(instance=perfil)

    return render(request, 'editar_perfil.html', {'form': form, 'perfil': perfil})

# --- 7. PERFIL PÚBLICO ---
def perfil_publico(request, uuid):
    perfil = get_object_or_404(UserProfile, uuid=uuid)
    avaliacoes = perfil.avaliacoes.all().order_by('-data')
    return render(request, 'publico_perfil.html', {
        'perfil': perfil, 
        'avaliacoes': avaliacoes, 
        'nota_media': perfil.nota_media()
    })

# --- 8. AVALIAR PROMOTOR (NOVA LÓGICA INTEGRADA) ---
def avaliar_promotor(request, uuid):
    perfil = get_object_or_404(UserProfile, uuid=uuid)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        nota = request.POST.get('nota')
        comentario = request.POST.get('comentario')
        if nome and nota:
            Avaliacao.objects.create(
                promotor=perfil, 
                cliente_nome=nome, 
                nota=int(nota), 
                comentario=comentario
            )
            # Renderiza uma página de sucesso simples ou redireciona
            return render(request, 'avaliacao_sucesso.html', {'perfil': perfil})
            
    return render(request, 'publico_avaliar.html', {'perfil': perfil})



@login_required
def api_search_promoters(request):
    term = request.GET.get('q', '').strip()
    
    # Base QuerySet: Apenas aprovados
    qs = UserProfile.objects.filter(status='aprovado')

    if term:
        # Se tiver busca, filtra por nome ou CPF
        qs = qs.filter(Q(nome_completo__icontains=term) | Q(cpf__icontains=term))
    
    # Limita e ordena (traz os 50 primeiros em ordem alfabética para facilitar a busca visual)
    qs = qs.order_by('nome_completo')

    # --- FILTROS EXTENDIDOS (Popup) ---
    f_genero = request.GET.get('genero', '').strip()
    if f_genero:
        qs = qs.filter(genero=f_genero)

    f_etnia = request.GET.get('etnia', '').strip()
    if f_etnia:
        qs = qs.filter(etnia=f_etnia)
        
    f_cabelo_tipo = request.GET.get('cabelo_tipo', '').strip()
    if f_cabelo_tipo:
        qs = qs.filter(cabelo_tipo=f_cabelo_tipo)
        
    f_cabelo_comprimento = request.GET.get('cabelo_comprimento', '').strip()
    if f_cabelo_comprimento:
        qs = qs.filter(cabelo_comprimento=f_cabelo_comprimento)

    f_olhos = request.GET.get('olhos', '').strip()
    if f_olhos:
        qs = qs.filter(olhos=f_olhos)
        
    f_cidade = request.GET.get('cidade', '').strip()
    if f_cidade:
        qs = qs.filter(cidade__icontains=f_cidade)

    f_estado = request.GET.get('estado', '').strip()
    if f_estado:
        qs = qs.filter(estado__iexact=f_estado)

    # Limita (traz os 50 primeiros)
    qs = qs[:50]

    results = []
    today = datetime.date.today()
    for p in qs:
        foto = p.foto_rosto.url if p.foto_rosto else None
        
        # Calcular Idade
        idade = None
        if p.data_nascimento:
            idade = today.year - p.data_nascimento.year - ((today.month, today.day) < (p.data_nascimento.month, p.data_nascimento.day))
        
        results.append({
            'id': p.pk, 
            'text': p.nome_completo, 
            'foto': foto, 
            'cidade': p.cidade, 
            'uf': p.estado,
            'genero': p.get_genero_display() if p.genero else None,
            'altura': str(p.altura).replace('.', ',') if p.altura else None,
            'idade': idade
        })
    return JsonResponse({'results': results})
