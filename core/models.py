from django.db import models
from django.contrib.auth.models import User

# --- 1. PERFIL DA MODELO ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Dados Pessoais
    nome_completo = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=20)
    data_nascimento = models.DateField(null=True, blank=True)
    
    # Endereço (Novo!)
    cep = models.CharField(max_length=9, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    
    # Medidas (Fixas)
    altura = models.DecimalField(max_digits=3, decimal_places=2, help_text="Ex: 1.70")
    manequim = models.CharField(max_length=10)
    calcado = models.CharField(max_length=10)
    
    # Fotos
    foto_rosto = models.ImageField(upload_to='modelos/rosto/', blank=True, null=True)
    foto_corpo = models.ImageField(upload_to='modelos/corpo/', blank=True, null=True)

    def __str__(self):
        return self.nome_completo

# --- 2. SISTEMA DE PERGUNTAS DINÂMICAS ---
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

# Tabela para as datas e valores de cada dia do Job
class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.data} - R$ {self.valor}"

# --- 4. CANDIDATURA (O Match) ---
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
        unique_together = ('job', 'modelo') # Impede de se candidatar 2x no mesmo job

    def __str__(self):
        return f"{self.modelo} -> {self.job} ({self.status})"