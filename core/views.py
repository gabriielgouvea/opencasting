from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Job, Candidatura, UserProfile, Pergunta, Resposta
from .forms import CadastroForm

# --- 1. MURAL DE VAGAS (Home) ---
def lista_vagas(request):
    # Mostra apenas vagas abertas, ordenadas da mais recente para a mais antiga
    jobs = Job.objects.filter(status='aberto').order_by('-criado_em')
    return render(request, 'job_list.html', {'jobs': jobs})

# --- 2. DETALHES DA VAGA ---
def detalhe_vaga(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    dias = job.dias.all() # Pega os dias e valores
    
    # Verifica se a pessoa já se candidatou (para bloquear o botão)
    ja_candidatou = False
    if request.user.is_authenticated:
        # Tenta verificar se o usuário tem um perfil de modelo
        if hasattr(request.user, 'userprofile'):
            ja_candidatou = Candidatura.objects.filter(job=job, modelo=request.user.userprofile).exists()

    return render(request, 'job_detail.html', {
        'job': job, 
        'dias': dias,
        'ja_candidatou': ja_candidatou
    })

# --- 3. AÇÃO DE SE CANDIDATAR ---
@login_required
def candidatar_vaga(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    try:
        # Pega o perfil da modelo logada
        perfil = request.user.userprofile
        
        # Tenta criar a candidatura
        Candidatura.objects.create(job=job, modelo=perfil)
        messages.success(request, "Candidatura realizada com sucesso! Boa sorte 🍀")
        
    except AttributeError:
        messages.error(request, "Erro: Seu perfil de modelo não está completo.")
    except Exception:
        messages.warning(request, "Você já se candidatou para esta vaga.")
    
    return redirect('detalhe_vaga', job_id=job.id)

# --- 4. CADASTRO DE MODELO (Wizard com Perguntas Dinâmicas) ---
def cadastro(request):
    if request.user.is_authenticated:
        return redirect('lista_vagas') # Se já estiver logada, manda pra home

    # Busca as perguntas ativas no banco para exibir no formulário
    perguntas_extras = Pergunta.objects.filter(ativa=True)

    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Validação de E-mail Único
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            if User.objects.filter(username=email).exists():
                messages.error(request, "Este e-mail já está cadastrado.")
                return render(request, 'cadastro.html', {'form': form, 'perguntas_extras': perguntas_extras})

            # 2. Cria o Usuário de Login
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            
            # 3. Cria o Perfil da Modelo
            perfil = form.save(commit=False)
            perfil.user = user
            perfil.save()

            # 4. SALVA AS RESPOSTAS DAS PERGUNTAS DINÂMICAS
            # O loop varre todas as perguntas ativas e procura a resposta no formulário enviado
            for pergunta in perguntas_extras:
                # No HTML, o campo tem o nome "pergunta_ID" (ex: pergunta_1)
                resposta_texto = request.POST.get(f'pergunta_{pergunta.id}')
                
                if resposta_texto:
                    Resposta.objects.create(
                        perfil=perfil,
                        pergunta=pergunta,
                        texto_resposta=resposta_texto
                    )
            
            # 5. Loga a pessoa e redireciona
            login(request, user)
            messages.success(request, f"Bem-vinda, {perfil.nome_completo}! Seu cadastro foi criado.")
            return redirect('lista_vagas')
    else:
        form = CadastroForm()

    return render(request, 'cadastro.html', {
        'form': form, 
        'perguntas_extras': perguntas_extras
    })