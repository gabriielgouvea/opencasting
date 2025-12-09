from django.db import models
from django.contrib.auth.models import User

# --- 1. PERFIL DA MODELO (Dados Pessoais) ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=20)
    data_nascimento = models.DateField(null=True, blank=True)
    
    # Medidas
    altura = models.DecimalField(max_digits=3, decimal_places=2, help_text="Ex: 1.75")
    manequim = models.CharField(max_length=10, help_text="Ex: 38, 40")
    calcado = models.CharField(max_length=10, help_text="Ex: 37, 39")
    
    # Fotos (Usaremos Cloudinary depois, por enquanto salva local)
    foto_rosto = models.ImageField(upload_to='modelos/rosto/', blank=True)
    foto_corpo = models.ImageField(upload_to='modelos/corpo/', blank=True)

    def __str__(self):
        return self.nome_completo

# --- 2. O TRABALHO (JOB) ---
class Job(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Casting Aberto'),
        ('analise', 'Em Análise'),
        ('finalizado', 'Finalizado'),
    ]

    titulo = models.CharField(max_length=200, help_text="Ex: Promotor(a) Blitz")
    local = models.CharField(max_length=200, help_text="Ex: Rodovia Hélio Smidt - Guarulhos/SP")
    descricao = models.TextField(help_text="Descrição geral do trabalho")
    
    # Detalhes Específicos (Baseado no seu print)
    uniforme = models.TextField(default="Calça preta e tênis branco", help_text="O que precisa vestir")
    infos_extras = models.TextField(blank=True, help_text="Alimentação, Transporte, etc.")
    data_pagamento = models.DateField(help_text="Quando o cachê cai?")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.local}"

# --- 3. DIÁRIAS DO TRABALHO (A Tabela de Datas/Horas) ---
# Isso resolve o print que mostrava vários dias (sex 12, sab 13)
class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    valor = models.DecimalField(max_digits=8, decimal_places=2, help_text="Valor deste dia específico")

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