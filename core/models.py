import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg

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

    # --- DADOS PESSOAIS ---
    nome_completo = models.CharField(max_length=100, verbose_name="Nome Completo")
    whatsapp = models.CharField(max_length=20, verbose_name="WhatsApp", help_text="Formato: (11) 99999-9999")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    
    # [NOVO] Instagram (Opcional)
    instagram = models.CharField(
        max_length=50, blank=True, null=True, 
        verbose_name="Instagram", 
        help_text="Ex: @seu.perfil"
    )

    # [NOVO] Termos de Aceite (Obrigatórios)
    termo_uso_imagem = models.BooleanField(
        'Aceito o uso de imagem', 
        default=False,
        help_text="Autoriza o uso de fotos e vídeos para divulgação."
    )
    termo_comunicacao = models.BooleanField(
        'Aceito receber comunicações', 
        default=False,
        help_text="Autoriza contato via WhatsApp/E-mail sobre vagas."
    )
    
    # --- ENDEREÇO ---
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")
    
    # --- MEDIDAS ---
    altura = models.DecimalField(
        max_digits=3, decimal_places=2, 
        verbose_name="Altura (m)",
        help_text="Exemplo: 1.70",
        null=True, blank=True
    )
    manequim = models.CharField(max_length=10, verbose_name="Manequim", help_text="Ex: P, M, G, 38, 40...", null=True, blank=True)
    calcado = models.CharField(max_length=10, verbose_name="Calçado", help_text="Ex: 36, 37, 40...", null=True, blank=True)
    
    # --- DADOS BANCÁRIOS ---
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    
    banco = models.CharField(max_length=50, blank=True, null=True, verbose_name="Banco")
    TIPO_CONTA_CHOICES = [('corrente', 'Conta Corrente'), ('poupanca', 'Conta Poupança')]
    tipo_conta = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, blank=True, null=True, verbose_name="Tipo de Conta")
    agencia = models.CharField(max_length=10, blank=True, null=True, verbose_name="Agência")
    conta = models.CharField(max_length=20, blank=True, null=True, verbose_name="Conta e Dígito")
    
    TIPO_CHAVE_CHOICES = [('cpf', 'CPF'), ('email', 'E-mail'), ('telefone', 'Telefone'), ('aleatoria', 'Chave Aleatória')]
    tipo_chave_pix = models.CharField(max_length=20, choices=TIPO_CHAVE_CHOICES, blank=True, null=True, verbose_name="Tipo de Chave PIX")
    chave_pix = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave PIX")

    # --- FOTOS ---
    foto_rosto = models.ImageField(
        upload_to='modelos/rosto/', blank=True, null=True, 
        verbose_name="Foto de Rosto (Close)",
        help_text="Esta foto será usada na carteirinha digital e nas miniaturas."
    )
    foto_corpo = models.ImageField(
        upload_to='modelos/corpo/', blank=True, null=True, 
        verbose_name="Foto de Corpo Inteiro",
        help_text="Foto para avaliação de perfil completo."
    )

    # --- CENTRAL DE DECISÃO ---
    STATUS_CHOICES = [
        ('pendente', '🟡 Pendente (Em Análise)'),
        ('aprovado', '🟢 Aprovado (Liberado)'),
        ('reprovado', '🔴 Reprovado (Bloqueado)'),
    ]
    
    MOTIVOS_REPROVACAO = [
        ('fotos_ruins', 'Fotos fora do padrão (Escuras/Selfie/Espelho)'),
        ('dados_incompletos', 'Dados incompletos ou incorretos'),
        ('perfil', 'Perfil não compatível no momento'),
        ('outros', 'Outros (Ver observação)'),
    ]

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pendente',
        verbose_name="Situação do Cadastro",
        help_text="ℹ️ <b>IMPORTANTE:</b> Se você marcar como 'Aprovado', o promotor receberá um e-mail de boas-vindas e poderá ver as vagas no site."
    )
    motivo_reprovacao = models.CharField(
        max_length=50, choices=MOTIVOS_REPROVACAO, blank=True, null=True, 
        verbose_name="Motivo da Reprovação",
        help_text="Selecione um motivo apenas se estiver reprovando o cadastro."
    )
    observacao_admin = models.TextField(
        blank=True, null=True, 
        verbose_name="Mensagem para o Promotor",
        help_text="Escreva aqui o que o promotor precisa corrigir. Essa mensagem será enviada por e-mail."
    )
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Cadastrado em")

    class Meta:
        verbose_name = "Promotor / Talento"
        verbose_name_plural = "📂 Base de Promotores"

    def __str__(self):
        return f"{self.nome_completo}"

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
                # Envia e-mail se mudar para APROVADO
                if antigo.status != 'aprovado' and self.status == 'aprovado':
                    send_mail(
                        'OpenCasting: Cadastro Aprovado! 🎉',
                        f'Olá {self.nome_completo},\n\nParabéns! Seu perfil foi aprovado.\n\nAcesse agora: https://gabrielgouvea.pythonanywhere.com/login/',
                        settings.DEFAULT_FROM_EMAIL,
                        [self.user.email],
                        fail_silently=True
                    )
                # Envia e-mail se mudar para REPROVADO
                elif antigo.status != 'reprovado' and self.status == 'reprovado':
                    send_mail(
                        'OpenCasting: Atualização do Cadastro',
                        f'Olá {self.nome_completo},\n\nPrecisamos de ajustes no seu perfil.\nMotivo: {self.get_motivo_reprovacao_display()}\nObs: {self.observacao_admin}',
                        settings.DEFAULT_FROM_EMAIL,
                        [self.user.email],
                        fail_silently=True
                    )
            except Exception:
                pass
        super().save(*args, **kwargs)

# ==============================================================================
# 2. AVALIAÇÕES DE CLIENTES
# ==============================================================================
class Avaliacao(models.Model):
    promotor = models.ForeignKey(UserProfile, related_name='avaliacoes', on_delete=models.CASCADE)
    cliente_nome = models.CharField(max_length=100, verbose_name="Empresa/Cliente")
    nota = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name="Nota")
    comentario = models.TextField(verbose_name="Opinião")
    data = models.DateTimeField(auto_now_add=True, verbose_name="Data")

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

    def __str__(self):
        return f"{self.cliente_nome} ({self.nota}★)"

# ==============================================================================
# 3. QUESTIONÁRIO (PERGUNTAS E RESPOSTAS)
# ==============================================================================
class Pergunta(models.Model):
    TIPO_CHOICES = [('texto', 'Texto Curto'), ('sim_nao', 'Sim ou Não')]
    texto = models.CharField(max_length=200, verbose_name="Pergunta")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sim_nao', verbose_name="Tipo")
    ativa = models.BooleanField(default=True, verbose_name="Ativa no Cadastro?")

    class Meta:
        verbose_name = "Pergunta do Formulário"
        verbose_name_plural = "⚙️ Perguntas do Cadastro"

    def __str__(self): return self.texto

class Resposta(models.Model):
    perfil = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.CharField(max_length=200, verbose_name="Resposta")
    
    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"

    def __str__(self): return self.texto_resposta

# ==============================================================================
# 4. GESTÃO DE VAGAS (JOBS)
# ==============================================================================
class Job(models.Model):
    STATUS_CHOICES = [('aberto', 'Casting Aberto'), ('analise', 'Em Análise (Fechado)'), ('finalizado', 'Finalizado')]
    
    titulo = models.CharField(max_length=200, verbose_name="Título da Vaga", help_text="Ex: Promotor para Blitz Dr. Peanut")
    local = models.CharField(max_length=200, verbose_name="Local", help_text="Cidade, Bairro ou Endereço principal")
    descricao = models.TextField(verbose_name="Descrição", help_text="Descreva as funções e o perfil desejado.")
    uniforme = models.TextField(default="Calça preta e tênis branco", verbose_name="Uniforme")
    infos_extras = models.TextField(blank=True, verbose_name="Infos Extras", help_text="Instruções adicionais (horário de chegada, etc).")
    data_pagamento = models.DateField(verbose_name="Data do Pagamento")
    
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='aberto',
        verbose_name="Status da Vaga",
        help_text="<b>Aberto:</b> Visível para todos os promotores.<br><b>Em Análise:</b> Ninguém mais pode se candidatar.<br><b>Finalizado:</b> Evento concluído."
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Vaga / Job"
        verbose_name_plural = "💼 Vagas e Jobs"

    def __str__(self): return self.titulo

class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField(verbose_name="Data do Evento")
    hora_inicio = models.TimeField(verbose_name="Início")
    hora_fim = models.TimeField(verbose_name="Fim")
    valor = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Cachê (R$)")
    
    class Meta:
        verbose_name = "Dia de Trabalho"
        verbose_name_plural = "Dias e Cachês"

    def __str__(self): return f"{self.data} - R$ {self.valor}"

# ==============================================================================
# 5. CANDIDATURAS
# ==============================================================================
class Candidatura(models.Model):
    STATUS_CANDIDATURA = [
        ('pendente', 'Aguardando Análise'), 
        ('aprovado', '✅ Selecionado para o Job'), 
        ('reprovado', '❌ Não Selecionado')
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="Vaga")
    modelo = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Candidato")
    status = models.CharField(
        max_length=20, choices=STATUS_CANDIDATURA, default='pendente',
        verbose_name="Situação",
        help_text="Se 'Selecionado', o promotor verá a confirmação no painel dele."
    )
    data_candidatura = models.DateTimeField(auto_now_add=True, verbose_name="Data de Inscrição")

    class Meta:
        unique_together = ('job', 'modelo')
        verbose_name = "Candidatura"
        verbose_name_plural = "📝 Candidaturas Recebidas"

    def __str__(self): return f"{self.modelo} -> {self.job}"