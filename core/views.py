from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Job, Candidatura, UserProfile, Pergunta, Resposta
from .forms import CadastroForm

# --- 1. HOME (LANDING PAGE) ---
def home(request):
    # Se for Admin, vai direto para as vagas
    if request.user.is_superuser:
        return redirect('lista_vagas')

    # Se for modelo logada e aprovada, vai para o dashboard
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.status == 'aprovado':
                return redirect('lista_vagas')
        except UserProfile.DoesNotExist:
            pass # Se não tem perfil, fica na home (ou vai pro cadastro se clicar no botão)
            
    return render(request, 'landing.html')

# --- 2. MURAL DE VAGAS (COM TRAVA DE STATUS) ---
@login_required(login_url='/login/')
def lista_vagas(request):
    # >>> ADMIN: VÊ TUDO <<<
    if request.user.is_superuser:
        jobs = Job.objects.all().order_by('-criado_em')
        return render(request, 'job_list.html', {'jobs': jobs})

    # >>> MODELO: CHECAGEM DE STATUS <<<
    try:
        perfil = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('cadastro') # Sem perfil -> Cadastro

    # Roteamento baseado no status
    if perfil.status == 'pendente':
        return render(request, 'aguardando_aprovacao.html')
    
    elif perfil.status == 'reprovado':
        return render(request, 'reprovado.html', {'perfil': perfil})

    # Se status == 'aprovado', mostra as vagas
    jobs = Job.objects.filter(status='aberto').order_by('-criado_em')
    return render(request, 'job_list.html', {'jobs': jobs})

# --- 3. DETALHES DA VAGA ---
@login_required(login_url='/login/')
def detalhe_vaga(request, job_id):
    # Admin entra direto
    if request.user.is_superuser:
        job = get_object_or_404(Job, id=job_id)
        dias = job.dias.all()
        return render(request, 'job_detail.html', {'job': job, 'dias': dias, 'ja_candidatou': False})

    # Modelo: verifica status
    try:
        perfil = request.user.userprofile
        if perfil.status == 'pendente':
            return render(request, 'aguardando_aprovacao.html')
        elif perfil.status == 'reprovado':
            return render(request, 'reprovado.html', {'perfil': perfil})
            
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

# --- 4. AÇÃO DE SE CANDIDATAR ---
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
        
    except AttributeError:
        messages.error(request, "Complete seu perfil antes de se candidatar.")
    except Exception:
        messages.warning(request, "Você já se candidatou para esta vaga.")
    
    return redirect('detalhe_vaga', job_id=job.id)

# --- 5. CADASTRO ---
def cadastro(request):
    if request.user.is_superuser:
        return redirect('lista_vagas')

    if request.user.is_authenticated:
        try:
            request.user.userprofile
            return redirect('lista_vagas')
        except UserProfile.DoesNotExist:
            pass

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
            perfil.status = 'pendente' # Garante que nasce pendente
            perfil.save()
            
            for pergunta in perguntas_extras:
                resposta_texto = request.POST.get(f'pergunta_{pergunta.id}')
                if resposta_texto:
                    Resposta.objects.create(perfil=perfil, pergunta=pergunta, texto_resposta=resposta_texto)

            login(request, user)
            messages.success(request, f"Bem-vinda, {perfil.nome_completo}! Aguarde a análise do seu cadastro.")
            return redirect('lista_vagas')
    else:
        form = CadastroForm()

    return render(request, 'cadastro.html', {'form': form, 'perguntas_extras': perguntas_extras})

# --- 6. EDITAR PERFIL ---
@login_required
def editar_perfil(request):
    if request.user.is_superuser:
        messages.info(request, "Admins editam dados pelo Painel Administrativo.")
        return redirect('lista_vagas')

    try:
        perfil = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('cadastro')

    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES, instance=perfil)
        # Remove campos sensíveis da edição
        if 'email' in form.fields: del form.fields['email']
        if 'password' in form.fields: del form.fields['password']
        if 'confirm_password' in form.fields: del form.fields['confirm_password']
        
        if form.is_valid():
            # Se foi reprovado e editou, volta para pendente para nova análise?
            # Opcional: perfil.status = 'pendente' 
            # perfil.motivo_reprovacao = None
            form.save()
            messages.success(request, "Dados atualizados com sucesso!")
            return redirect('lista_vagas')
    else:
        form = CadastroForm(instance=perfil)
        if 'email' in form.fields: del form.fields['email']
        if 'password' in form.fields: del form.fields['password']
        if 'confirm_password' in form.fields: del form.fields['confirm_password']

    return render(request, 'editar_perfil.html', {'form': form})