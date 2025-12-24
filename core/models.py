import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg


class CpfBanido(models.Model):
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF (banido)")
    motivo = models.CharField(max_length=200, blank=True, null=True, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Banido em")

    class Meta:
        verbose_name = "CPF Banido"
        verbose_name_plural = "CPFs Banidos"

    def __str__(self):
        return self.cpf

# ==============================================================================
# 1. PERFIL DO PROMOTOR (BASE DE TALENTOS)
# ==============================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, 
        verbose_name="Conta de Acesso",
        help_text="Vínculo com o login (e-mail e senha) do sistema."
    )
    
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, 
        verbose_name="ID Público",
        help_text="Código único usado para gerar os links de compartilhamento."
    )

    # --- 1. DADOS DE ACESSO E DOCUMENTOS ---
    nome_completo = models.CharField(max_length=100, verbose_name="Nome Completo")
    
    instagram = models.CharField(
        max_length=50, blank=True, null=True, 
        verbose_name="Instagram (Opcional)", 
        help_text="Ex: @seu.perfil"
    )

    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG / RNE")

    # --- 2. DADOS PESSOAIS ---
    whatsapp = models.CharField(max_length=20, verbose_name="Telefone (WhatsApp)", help_text="Formato: (11) 99999-9999")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    
    GENERO_CHOICES = [
        ('feminino', 'Feminino'),
        ('masculino', 'Masculino'),
        ('nao_binario', 'Não-binário'),
        ('outros', 'Outros'),
        ('prefiro_nao_dizer', 'Prefiro não dizer'),
    ]
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, blank=True, null=True, verbose_name="Gênero")

    ETNIA_CHOICES = [
        ('branca', 'Branca'),
        ('preta', 'Preta'),
        ('parda', 'Parda'),
        ('amarela', 'Amarela (Asiáticos/Orientais)'),
        ('indigena', 'Indígena'),
        ('outra', 'Outra'),
    ]
    etnia = models.CharField(max_length=20, choices=ETNIA_CHOICES, blank=True, null=True, verbose_name="Cor/Etnia")

    is_pcd = models.BooleanField(default=False, verbose_name="É PCD (Pessoa com Deficiência)?")
    descricao_pcd = models.CharField(max_length=200, blank=True, null=True, verbose_name="Qual deficiência? (Se PCD)")

    # --- 3. NACIONALIDADE E IDIOMAS ---
    NACIONALIDADE_CHOICES = [
        ('brasileira', 'Brasileira 🇧🇷'),
        ('americana', 'Americana 🇺🇸'),
        ('espanhola', 'Espanhola 🇪🇸'),
        ('francesa', 'Francesa 🇫🇷'),
        ('italiana', 'Italiana 🇮🇹'),
        ('japonesa', 'Japonesa 🇯🇵'),
        ('chinesa', 'Chinesa 🇨🇳'),
        ('alemama', 'Alemã 🇩🇪'),
        ('outra', 'Outra'),
    ]
    nacionalidade = models.CharField(max_length=20, choices=NACIONALIDADE_CHOICES, default='brasileira', verbose_name="Nacionalidade")

    NIVEL_IDIOMA = [
        ('basico', 'Básico'),
        ('intermediario', 'Intermediário'),
        ('fluente', 'Fluente/Nativo'),
    ]
    nivel_ingles = models.CharField(max_length=15, choices=NIVEL_IDIOMA, blank=True, null=True, verbose_name="Inglês")
    nivel_espanhol = models.CharField(max_length=15, choices=NIVEL_IDIOMA, blank=True, null=True, verbose_name="Espanhol")
    nivel_frances = models.CharField(max_length=15, choices=NIVEL_IDIOMA, blank=True, null=True, verbose_name="Francês")
    outros_idiomas = models.CharField(max_length=200, blank=True, null=True, verbose_name="Outros Idiomas", help_text="Ex: Japonês Fluente, Alemão Básico")

    # --- 4. ENDEREÇO ---
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")
    
    # --- 5. MEDIDAS E APARÊNCIA ---
    altura = models.DecimalField(max_digits=3, decimal_places=2, help_text="Ex: 1.70", null=True, blank=True, verbose_name="Altura (m)")
    peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Peso (kg)")
    
    manequim = models.CharField(max_length=10, blank=True, null=True, verbose_name="Manequim")
    calcado = models.CharField(max_length=10, blank=True, null=True, verbose_name="Calçado")
    
    TAMANHO_CAMISETA = [('PP','PP'), ('P','P'), ('M','M'), ('G','G'), ('GG','GG'), ('XG','XG')]
    tamanho_camiseta = models.CharField(max_length=5, choices=TAMANHO_CAMISETA, blank=True, null=True, verbose_name="Tamanho de Camiseta")

    OLHOS_CHOICES = [
        ('castanho_escuro', 'Castanho Escuro'),
        ('castanho_claro', 'Castanho Claro'),
        ('azul', 'Azul'),
        ('verde', 'Verde'),
        ('mel', 'Mel'),
        ('preto', 'Preto'),
        ('heterocromia', 'Heterocromia'),
    ]
    olhos = models.CharField(max_length=20, choices=OLHOS_CHOICES, blank=True, null=True, verbose_name="Cor dos Olhos")

    CABELO_TIPO_CHOICES = [
        ('liso', 'Liso'),
        ('ondulado', 'Ondulado'),
        ('cacheado', 'Cacheado'),
        ('crespo', 'Crespo'),
        ('black_power', 'Black Power'),
        ('dread', 'Dreadlocks'),
        ('trancas', 'Tranças'),
    ]
    cabelo_tipo = models.CharField(max_length=20, choices=CABELO_TIPO_CHOICES, blank=True, null=True, verbose_name="Tipo de Cabelo")

    CABELO_TAM_CHOICES = [
        ('curto', 'Curto'),
        ('medio', 'Médio'),
        ('longo', 'Longo'),
        ('careca', 'Careca/Raspado'),
    ]
    cabelo_comprimento = models.CharField(max_length=20, choices=CABELO_TAM_CHOICES, blank=True, null=True, verbose_name="Comprimento do Cabelo")

    # --- 6. PROFISSIONAL ---
    EXPERIENCIA_CHOICES = [
        ('sem_experiencia', 'Não tenho experiência (Começando agora)'),
        ('pouca', 'Tenho, mas pouca'),
        ('media', 'Tenho experiência'),
        ('muita', 'Sim, há bastante tempo (Expert)'),
    ]
    experiencia = models.CharField(max_length=20, choices=EXPERIENCIA_CHOICES, default='sem_experiencia', verbose_name="Experiência")

    areas_atuacao = models.TextField(blank=True, null=True, verbose_name="Áreas de Interesse")
    
    DISPONIBILIDADE_CHOICES = [
        ('total', 'Todos os dias (Incluindo Finais de Semana)'),
        ('seg_sex', 'Segunda a Sexta'),
        ('fds', 'Somente Finais de Semana'),
        ('noite', 'Somente Período Noturno'),
        ('freelancer', 'Dias Aleatórios / Sem data fixa'),
    ]
    disponibilidade = models.CharField(max_length=20, choices=DISPONIBILIDADE_CHOICES, blank=True, null=True, verbose_name="Disponibilidade")

    # --- 7. DADOS BANCÁRIOS ---
    banco = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nome do Banco")
    TIPO_CONTA_CHOICES = [('corrente', 'Conta Corrente'), ('poupanca', 'Conta Poupança')]
    tipo_conta = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, blank=True, null=True, verbose_name="Tipo de Conta")
    agencia = models.CharField(max_length=10, blank=True, null=True, verbose_name="Agência")
    conta = models.CharField(max_length=20, blank=True, null=True, verbose_name="Conta e Dígito")
    
    TIPO_CHAVE_CHOICES = [('cpf', 'CPF'), ('email', 'E-mail'), ('telefone', 'Telefone'), ('aleatoria', 'Chave Aleatória')]
    tipo_chave_pix = models.CharField(max_length=20, choices=TIPO_CHAVE_CHOICES, blank=True, null=True, verbose_name="Tipo de Chave PIX")
    chave_pix = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave PIX")

    # --- 8. FOTOS & STATUS CRM ---
    foto_rosto = models.ImageField(upload_to='modelos/rosto/', blank=True, null=True, verbose_name="Foto de Rosto")
    foto_corpo = models.ImageField(upload_to='modelos/corpo/', blank=True, null=True, verbose_name="Foto de Corpo")

    STATUS_CHOICES = [
        ('pendente', '🟡 Pendente (Em Análise)'),
        ('aprovado', '🟢 Aprovado'),
        ('reprovado', '🔴 Reprovado (Bloqueado)'),
        ('correcao', '🔵 Necessita Ajuste'),
    ]
    
    MOTIVOS_REPROVACAO = [
        ('fotos_ruins', 'Fotos fora do padrão (Escuras/Selfie/Espelho)'),
        ('dados_incompletos', 'Dados incompletos ou incorretos'),
        ('documentos', 'Documentos/Informações ilegíveis ou inconsistentes'),
        ('menor_idade', 'Menor de idade / inconsistência de idade'),
        ('perfil', 'Perfil não compatível no momento'),
        ('outros', 'Outros (Ver observação)'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    motivo_reprovacao = models.CharField(max_length=50, choices=MOTIVOS_REPROVACAO, blank=True, null=True, verbose_name="Motivo (Se reprovado)")
    observacao_admin = models.TextField(blank=True, null=True, verbose_name="Mensagem para a Modelo")
    data_reprovacao = models.DateTimeField(blank=True, null=True, verbose_name="Data da Reprovação")
    bloqueado_ate = models.DateField(blank=True, null=True, verbose_name="Bloqueado até")

    # Termos
    termo_uso_imagem = models.BooleanField(default=False, verbose_name="Aceito uso de imagem")
    termo_comunicacao = models.BooleanField(default=False, verbose_name="Aceito receber comunicações")

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Cadastrado em")

    class Meta:
        verbose_name = "Promotor / Talento"
        verbose_name_plural = "📂 Base de Promotores"

    def __str__(self):
        return f"{self.nome_completo} ({self.get_status_display()})"

    # --- MÉTODOS AUXILIARES ---
    def nota_media(self):
        media = self.avaliacoes.aggregate(Avg('nota'))['nota__avg']
        return round(media, 1) if media else 0

    def total_jobs(self):
        return self.candidatura_set.filter(status='aprovado').count()

    # --- AUTOMAÇÃO DE E-MAIL AO SALVAR ---
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                antigo = UserProfile.objects.get(pk=self.pk)
                if antigo.status != 'aprovado' and self.status == 'aprovado':
                    send_mail(
                        'OpenCasting: Cadastro Aprovado! 🎉',
                        f'Olá {self.nome_completo}, seu perfil foi aprovado.',
                        settings.DEFAULT_FROM_EMAIL, [self.user.email], fail_silently=True
                    )
            except Exception: pass
        super().save(*args, **kwargs)

# ==============================================================================
# 2. OUTROS MODELOS DO SISTEMA
# ==============================================================================
class Avaliacao(models.Model):
    promotor = models.ForeignKey(UserProfile, related_name='avaliacoes', on_delete=models.CASCADE)
    cliente_nome = models.CharField(max_length=100, verbose_name="Empresa/Cliente")
    nota = models.IntegerField(choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')])
    comentario = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

class Pergunta(models.Model):
    texto = models.CharField(max_length=200)
    ativa = models.BooleanField(default=True)
    def __str__(self): return self.texto

class Resposta(models.Model):
    perfil = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.CharField(max_length=200)

class Job(models.Model):
    STATUS_CHOICES = [('aberto', 'Casting Aberto'), ('analise', 'Em Análise'), ('finalizado', 'Finalizado')]
    titulo = models.CharField(max_length=200, verbose_name="Título da Vaga")
    local = models.CharField(max_length=200, verbose_name="Local", blank=True, null=True) # CORRIGIDO PARA MIGRAÇÃO
    descricao = models.TextField(verbose_name="Descrição", blank=True, null=True) # CORRIGIDO PARA MIGRAÇÃO
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    criado_em = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.titulo

class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)

class Candidatura(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    modelo = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pendente')
    data_candidatura = models.DateTimeField(auto_now_add=True)

class ConfiguracaoSite(models.Model):
    titulo_site = models.CharField(max_length=100, default="OpenCasting")
    email_contato = models.EmailField(default="suporte@opencasting.com")
    def save(self, *args, **kwargs): self.pk=1; super().save(*args, **kwargs)
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj