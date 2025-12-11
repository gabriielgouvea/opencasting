from django.db import models
from django.contrib.auth.models import User

# --- 1. PERFIL DA MODELO ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # --- DADOS PESSOAIS ---
    nome_completo = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=20)
    data_nascimento = models.DateField(null=True, blank=True)
    
    # --- ENDEREÇO ---
    cep = models.CharField(max_length=9, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    
    # --- MEDIDAS ---
    altura = models.DecimalField(max_digits=3, decimal_places=2, help_text="Ex: 1.70")
    manequim = models.CharField(max_length=10)
    calcado = models.CharField(max_length=10)
    
    # --- DADOS DE PAGAMENTO ---
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    
    # Opção 1: Transferência
    banco = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nome do Banco")
    
    TIPO_CONTA_CHOICES = [
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
    ]
    tipo_conta = models.CharField(max_length=20, choices=TIPO_CONTA_CHOICES, blank=True, null=True, verbose_name="Tipo de Conta")
    
    agencia = models.CharField(max_length=10, blank=True, null=True)
    conta = models.CharField(max_length=20, blank=True, null=True)
    
    # Opção 2: PIX
    TIPO_CHAVE_CHOICES = [
        ('cpf', 'CPF'),
        ('email', 'E-mail'),
        ('telefone', 'Telefone'),
        ('aleatoria', 'Chave Aleatória'),
    ]
    tipo_chave_pix = models.CharField(max_length=20, choices=TIPO_CHAVE_CHOICES, blank=True, null=True)
    chave_pix = models.CharField(max_length=100, blank=True, null=True)

    # --- FOTOS (Vai pro Cloudinary automaticamente) ---
    foto_rosto = models.ImageField(upload_to='modelos/rosto/', blank=True, null=True)
    foto_corpo = models.ImageField(upload_to='modelos/corpo/', blank=True, null=True)

    # --- SISTEMA DE APROVAÇÃO ---
    STATUS_CHOICES = [
        ('pendente', '🟡 Pendente (Em Análise)'),
        ('aprovado', '🟢 Aprovado'),
        ('reprovado', '🔴 Reprovado'),
    ]
    
    MOTIVOS_REPROVACAO = [
        ('fotos_ruins', 'Fotos fora do padrão (Escuras/Selfie/Espelho)'),
        ('dados_incompletos', 'Dados incompletos ou incorretos'),
        ('perfil', 'Perfil não compatível no momento'),
        ('outros', 'Outros (Ver observação)'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    motivo_reprovacao = models.CharField(max_length=50, choices=MOTIVOS_REPROVACAO, blank=True, null=True, verbose_name="Motivo (Se reprovado)")
    observacao_admin = models.TextField(blank=True, null=True, verbose_name="Mensagem para a Modelo")

    def __str__(self):
        return f"{self.nome_completo} ({self.get_status_display()})"

# --- 2. PERGUNTAS DINÂMICAS ---
class Pergunta(models.Model):
    TIPO_CHOICES = [
        ('texto', 'Texto Curto'),
        ('sim_nao', 'Sim ou Não'),
    ]
    texto = models.CharField(max_length=200, help_text="Ex: Possui veículo próprio?")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sim_nao')
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.texto

class Resposta(models.Model):
    perfil = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.perfil} - {self.pergunta}: {self.texto_resposta}"

# --- 3. JOBS E VAGAS ---
class Job(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Casting Aberto'),
        ('analise', 'Em Análise'),
        ('finalizado', 'Finalizado'),
    ]

    titulo = models.CharField(max_length=200)
    local = models.CharField(max_length=200)
    descricao = models.TextField()
    uniforme = models.TextField(default="Calça preta e tênis branco")
    infos_extras = models.TextField(blank=True)
    data_pagamento = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.data} - R$ {self.valor}"

# --- 4. CANDIDATURA ---
class Candidatura(models.Model):
    STATUS_CANDIDATURA = [
        ('pendente', 'Aguardando Aprovação'),
        ('aprovado', 'Aprovado ✅'),
        ('reprovado', 'Não selecionado ❌'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    modelo = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CANDIDATURA, default='pendente')
    data_candidatura = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'modelo')

    def __str__(self):
        return f"{self.modelo} -> {self.job} ({self.status})"