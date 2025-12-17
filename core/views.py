from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import Job, Candidatura, UserProfile, Pergunta, Resposta, Avaliacao
from .forms import CadastroForm
import datetime

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
            
    return render(request, 'landing.html')

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
    elif perfil.status == 'reprovado':
        return render(request, 'reprovado.html', {'perfil': perfil})

    # --- LÓGICA DO DASHBOARD ---
    
    # 1. Identificar vagas já candidatadas
    ids_candidaturas = Candidatura.objects.filter(modelo=perfil).values_list('job_id', flat=True)
    
    # 2. Vagas Disponíveis (Abertas e Não Candidatadas)
    vagas_disponiveis = Job.objects.filter(status='aberto').exclude(id__in=ids_candidaturas).order_by('-criado_em')

    # 3. Histórico de Atividades
    meus_eventos = Candidatura.objects.filter(modelo=perfil).order_by('-data_candidatura')

    # 4. Cálculo de Progresso (Gamificação)
    # Começa com 50% (Cadastro Básico).
    # +25% se tiver foto de rosto
    # +25% se tiver foto de corpo
    progresso = 50 
    if perfil.foto_rosto: progresso += 25
    if perfil.foto_corpo: progresso += 25
    
    # Trava em 100%
    progresso = min(progresso, 100)
    
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
    if request.user.is_superuser:
        job = get_object_or_404(Job, id=job_id)
        dias = job.dias.all()
        return render(request, 'job_detail.html', {'job': job, 'dias': dias, 'ja_candidatou': False})

    try:
        perfil = request.user.userprofile
        if perfil.status != 'aprovado':
            return redirect('lista_vagas')
            
        job = get_object_or_404(Job, id=job_id)
        dias = job.dias.all()
        ja_candidatou = Candidatura.objects.filter(job=job, modelo=perfil).exists()

        return render(request, 'job_detail.html', {
            'job': job, 
            'dias': dias,
            'ja_candidatou': ja_candidatou
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

            try:
                send_mail(
                    'Cadastro Recebido - OpenCasting',
                    f'Olá {perfil.nome_completo}!\n\nRecebemos seu cadastro. Nossa equipe vai analisar seus dados.\n\nAtt,\nEquipe OpenCasting',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except: pass

            messages.success(request, f"Bem-vinda, {perfil.nome_completo}! Aguarde a análise.")
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
        
        # Limpa campos sensíveis do form
        if 'email' in form.fields: del form.fields['email']
        if 'password' in form.fields: del form.fields['password']
        if 'confirm_password' in form.fields: del form.fields['confirm_password']
        
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('lista_vagas')
    else:
        form = CadastroForm(instance=perfil)
        if 'email' in form.fields: del form.fields['email']
        if 'password' in form.fields: del form.fields['password']
        if 'confirm_password' in form.fields: del form.fields['confirm_password']

    return render(request, 'editar_perfil.html', {'form': form})

# --- 7. PERFIL PÚBLICO ---
def perfil_publico(request, uuid):
    perfil = get_object_or_404(UserProfile, uuid=uuid)
    avaliacoes = perfil.avaliacoes.all().order_by('-data')
    return render(request, 'publico_perfil.html', {
        'perfil': perfil, 
        'avaliacoes': avaliacoes, 
        'nota_media': perfil.nota_media()
    })

# --- 8. AVALIAR ---
def avaliar_promotor(request, uuid):
    perfil = get_object_or_404(UserProfile, uuid=uuid)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        nota = request.POST.get('nota')
        comentario = request.POST.get('comentario')
        if nome and nota:
            Avaliacao.objects.create(promotor=perfil, cliente_nome=nome, nota=int(nota), comentario=comentario)
            return render(request, 'avaliacao_sucesso.html', {'perfil': perfil})
    return render(request, 'publico_avaliar.html', {'perfil': perfil})

# --- 9. INSTITUCIONAL (QUEM SOMOS) - NOVO ---
def quem_somos(request):
    return render(request, 'quem_somos.html')