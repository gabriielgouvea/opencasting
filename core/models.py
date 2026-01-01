import uuid
import re
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta


class CpfBanido(models.Model):
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF (banido)")
    motivo = models.CharField(max_length=200, blank=True, null=True, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Banido em")

    class Meta:
        verbose_name = "CPF Banido"
        verbose_name_plural = "CPFs Banidos"

    def __str__(self):
        return self.cpf


def _only_digits(value: str) -> str:
    return re.sub(r'\D+', '', str(value or ''))


class Cliente(models.Model):
    REGIME_TRIBUTARIO_CHOICES = (
        ('simples', 'Simples Nacional'),
        ('presumido', 'Lucro Presumido'),
        ('real', 'Lucro Real'),
        ('mei', 'MEI'),
        ('outro', 'Outro/Não informado'),
    )

    # Aceita máscara no input do admin (ex: 12.345.678/0001-90),
    # mas salvamos somente dígitos.
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    razao_social = models.CharField(max_length=255, verbose_name='Razão social')
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nome fantasia')
    data_abertura = models.DateField(blank=True, null=True, verbose_name='Data de abertura')
    situacao_cadastral = models.CharField(max_length=80, blank=True, null=True, verbose_name='Situação cadastral')
    natureza_juridica = models.CharField(max_length=255, blank=True, null=True, verbose_name='Natureza jurídica')
    cnae_principal = models.CharField(max_length=20, blank=True, null=True, verbose_name='CNAE principal')
    cnae_principal_descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Descrição do CNAE')

    inscricao_estadual = models.CharField(max_length=40, blank=True, null=True, verbose_name='Inscrição estadual')
    inscricao_municipal = models.CharField(max_length=40, blank=True, null=True, verbose_name='Inscrição municipal')
    regime_tributario = models.CharField(
        max_length=20,
        choices=REGIME_TRIBUTARIO_CHOICES,
        default='outro',
        verbose_name='Regime tributário',
    )

    email_nfe = models.EmailField(blank=True, null=True, verbose_name='E-mail para NF')
    telefone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefone')

    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name='CEP')
    logradouro = models.CharField(max_length=120, blank=True, null=True, verbose_name='Logradouro')
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número')
    complemento = models.CharField(max_length=80, blank=True, null=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=80, blank=True, null=True, verbose_name='Bairro')
    cidade = models.CharField(max_length=80, blank=True, null=True, verbose_name='Cidade')
    uf = models.CharField(max_length=2, blank=True, null=True, verbose_name='UF')

    contato_nome = models.CharField(max_length=120, blank=True, null=True, verbose_name='Contato (nome)')
    contato_cargo = models.CharField(max_length=120, blank=True, null=True, verbose_name='Contato (cargo)')

    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ('razao_social', 'id')

    def __str__(self) -> str:
        return self.nome_fantasia or self.razao_social

    @property
    def cnpj_formatado(self) -> str:
        d = _only_digits(self.cnpj)
        if len(d) != 14:
            return self.cnpj
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"

    def save(self, *args, **kwargs):
        self.cnpj = _only_digits(self.cnpj)
        self.cep = (self.cep or '').strip() or None
        if self.cep:
            self.cep = self.cep.replace(' ', '')
        self.uf = (self.uf or '').strip().upper() or None
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        cnpj_digits = _only_digits(self.cnpj)
        if cnpj_digits and len(cnpj_digits) != 14:
            from django.core.exceptions import ValidationError

            raise ValidationError({'cnpj': 'CNPJ deve conter 14 dígitos.'})
        self.cnpj = cnpj_digits


class Orcamento(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orcamentos',
        verbose_name='Cliente (opcional)',
    )
    data_evento = models.DateField(blank=True, null=True, verbose_name='Data do evento')
    validade_dias = models.PositiveIntegerField(default=30, verbose_name='Orçamento válido por (dias)')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ('-criado_em', '-id')

    def __str__(self) -> str:
        base = f"Orçamento #{self.pk or 'novo'}"
        if self.cliente_id:
            return f"{base} - {self.cliente}"
        return base

    @property
    def total_geral(self) -> Decimal:
        total = Decimal('0')
        for item in self.itens.all():
            total += (item.total or Decimal('0'))
        return total

    @property
    def valido_ate(self):
        try:
            return (self.criado_em + timedelta(days=int(self.validade_dias or 0))).date()
        except Exception:
            return None


class OrcamentoItem(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Orçamento',
    )
    funcao = models.CharField(max_length=120, verbose_name='Função')
    quantidade = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    carga_horaria_horas = models.PositiveIntegerField(default=8, verbose_name='Carga horária (h)')
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Valor da diária (R$)')
    diarias = models.PositiveIntegerField(default=1, verbose_name='Diárias')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Total (R$)')
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Item do orçamento'
        verbose_name_plural = 'Itens do orçamento'
        ordering = ('ordem', 'id')

    def __str__(self) -> str:
        return f"{self.funcao} ({self.quantidade}x)"

    def save(self, *args, **kwargs):
        qty = int(self.quantidade or 0)
        days = int(self.diarias or 0)
        daily = self.valor_diaria or Decimal('0')
        try:
            self.total = (Decimal(qty) * Decimal(days) * Decimal(daily)).quantize(Decimal('0.01'))
        except Exception:
            self.total = Decimal('0.00')
        super().save(*args, **kwargs)

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

    # Coordenadas (para distância até trabalhos). Preenchimento best-effort via geocoding.
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Longitude")
    
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

    AREAS_ATUACAO_CHOICES = [
        ('recepcao', 'Recepção'),
        ('degustacao', 'Degustação'),
        ('bartender', 'Bartender'),
        ('garcom', 'Garçom/Garçonete'),
        ('modelo', 'Modelo'),
        ('seguranca', 'Segurança'),
        ('mascote', 'Mascote'),
        ('controle_acesso', 'Controle de Acesso'),
        ('limpeza', 'Limpeza'),
        ('dj', 'DJ'),
        ('fotografo', 'Fotógrafo'),
        ('apresentador', 'Apresentador/Locutor'),
        ('outros', 'Outros (Descrever abaixo)'),
    ]

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
                        'Casting Certo: Cadastro Aprovado! 🎉',
                        f'Olá {self.nome_completo}, seu perfil foi aprovado.',
                        settings.DEFAULT_FROM_EMAIL, [self.user.email], fail_silently=True
                    )
            except Exception: pass

        # Geocoding (best-effort): tenta preencher lat/lng quando estiverem vazios.
        # Mantém silencioso para não quebrar o fluxo caso o serviço externo falhe.
        if (self.latitude is None or self.longitude is None) and any([self.endereco, self.bairro, self.cidade, self.estado, self.cep]):
            try:
                from geopy.geocoders import Nominatim

                parts = [
                    (self.endereco or '').strip(),
                    (self.numero or '').strip(),
                    (self.bairro or '').strip(),
                    (self.cidade or '').strip(),
                    (self.estado or '').strip(),
                    (self.cep or '').strip(),
                    'Brasil',
                ]
                query = ', '.join([p for p in parts if p])
                if query:
                    geolocator = Nominatim(user_agent='casting-certo')
                    location = geolocator.geocode(query, timeout=5)
                    if location:
                        self.latitude = round(float(location.latitude), 6)
                        self.longitude = round(float(location.longitude), 6)
            except Exception:
                pass
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

    titulo = models.CharField(max_length=200, verbose_name="Título do Trabalho")
    empresa = models.CharField(max_length=120, blank=True, null=True, verbose_name="Empresa")

    # Endereço do trabalho
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF")

    # Campo legado
    local = models.CharField(max_length=200, verbose_name="Local (legado)", blank=True, null=True)

    # Tipo de serviço (usa as mesmas opções do cadastro)
    tipo_servico = models.TextField(blank=True, null=True, verbose_name="Tipo de Serviço")
    tipo_servico_outros = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Outros (descrever)",
    )

    # Pagamento e descrição
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data prevista de pagamento")
    descricao = models.TextField(verbose_name="Descrição (opcional)", blank=True, null=True)
    uniforme_fornecido = models.BooleanField(default=False, verbose_name="Uniforme fornecido pela empresa?")
    uniforme = models.TextField(blank=True, null=True, verbose_name="Uniforme (legado)")

    # Requisitos (opcionais: se vazio, não aparece para o promotor)
    requer_experiencia = models.BooleanField(default=False, verbose_name="Precisa de experiência?")
    generos_aceitos = models.TextField(blank=True, null=True, verbose_name="Sexo/Gênero (aceitos)")
    etnias_aceitas = models.TextField(blank=True, null=True, verbose_name="Cor/Etnia (aceitas)")
    olhos_aceitos = models.TextField(blank=True, null=True, verbose_name="Cor dos olhos (aceitas)")
    cabelo_tipos_aceitos = models.TextField(blank=True, null=True, verbose_name="Tipo de cabelo (aceitos)")
    cabelo_comprimentos_aceitos = models.TextField(blank=True, null=True, verbose_name="Comprimento do cabelo (aceitos)")
    nivel_ingles_min = models.CharField(max_length=15, blank=True, null=True, choices=UserProfile.NIVEL_IDIOMA, verbose_name="Inglês mínimo")

    # Competências (tags)
    competencias = models.TextField(blank=True, null=True, verbose_name="Competências")

    # Coordenadas do trabalho (para distância). Preenchimento best-effort via geocoding.
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Longitude")
    geocodificado_em = models.DateTimeField(blank=True, null=True, verbose_name="Geocodificado em")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Trabalho"
        verbose_name_plural = "Trabalhos"

    def __str__(self):
        return self.titulo

    def endereco_formatado(self) -> str:
        parts = [
            (self.endereco or '').strip(),
            (self.numero or '').strip(),
            (self.bairro or '').strip(),
            (self.cidade or '').strip(),
            (self.estado or '').strip(),
        ]
        s = ', '.join([p for p in parts if p])
        return s or (self.local or '').strip()

    def save(self, *args, **kwargs):
        # Geocoding (best-effort): tenta preencher lat/lng uma vez, quando estiverem vazios.
        if (self.latitude is None or self.longitude is None) and any([self.endereco, self.bairro, self.cidade, self.estado, self.cep, self.local]):
            try:
                from geopy.geocoders import Nominatim

                parts = [
                    (self.endereco or '').strip() or (self.local or '').strip(),
                    (self.numero or '').strip(),
                    (self.bairro or '').strip(),
                    (self.cidade or '').strip(),
                    (self.estado or '').strip(),
                    (self.cep or '').strip(),
                    'Brasil',
                ]
                query = ', '.join([p for p in parts if p])
                if query:
                    geolocator = Nominatim(user_agent='casting-certo')
                    location = geolocator.geocode(query, timeout=5)
                    if location:
                        self.latitude = round(float(location.latitude), 6)
                        self.longitude = round(float(location.longitude), 6)
                        self.geocodificado_em = timezone.now()
            except Exception:
                pass

        super().save(*args, **kwargs)

class JobDia(models.Model):
    job = models.ForeignKey(Job, related_name='dias', on_delete=models.CASCADE)
    data = models.DateField()
    hora_inicio = models.TimeField(blank=True, null=True, verbose_name="Hora início")
    hora_fim = models.TimeField(blank=True, null=True, verbose_name="Hora fim")
    valor = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "Dia do Trabalho"
        verbose_name_plural = "Dias do Trabalho"

class Candidatura(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    modelo = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pendente')
    data_candidatura = models.DateTimeField(auto_now_add=True)

class ConfiguracaoSite(models.Model):
    titulo_site = models.CharField(max_length=100, default="Casting Certo", verbose_name="Nome do Site")

    # Contatos (Rodapé)
    email_contato = models.EmailField(default="contato@opencasting.com.br", verbose_name="E-mail de Contato")
    telefone_contato = models.CharField(max_length=30, blank=True, null=True, default="(11) 99999-9999", verbose_name="Telefone / WhatsApp")
    endereco_contato = models.CharField(max_length=120, blank=True, null=True, default="Alphaville, Barueri - SP", verbose_name="Endereço (Rodapé)")

    instagram_link = models.URLField(blank=True, null=True, verbose_name="Link do Instagram")

    texto_sobre_curto = models.TextField(
        blank=True,
        null=True,
        default="Conectamos as melhores marcas aos profissionais mais qualificados.",
        verbose_name="Resumo (Rodapé)",
        help_text="Texto curto que aparece no rodapé/coluna institucional.",
    )

    # Páginas institucionais
    titulo_quem_somos = models.CharField(max_length=60, default="Quem Somos", verbose_name="Título - Quem Somos")
    texto_quem_somos = models.TextField(
        blank=True,
        null=True,
        default=(
            "A Casting Certo é uma agência focada em conectar marcas e talentos com agilidade e transparência.\n\n"
            "Trabalhamos com uma base de profissionais verificados para eventos, ações promocionais e ativações de marca.\n\n"
            "Nossa missão é simplificar a seleção e elevar o padrão de entrega em campo."
        ),
        verbose_name="Texto - Quem Somos",
    )

    titulo_servicos = models.CharField(max_length=60, default="Serviços", verbose_name="Título - Serviços")
    texto_servicos = models.TextField(
        blank=True,
        null=True,
        default=(
            "Oferecemos soluções completas para seleção e gestão de equipes para eventos.\n\n"
            "• Casting e recrutamento\n"
            "• Triagem e aprovação de talentos\n"
            "• Gestão de disponibilidade\n"
            "• Acompanhamento e avaliações\n"
        ),
        verbose_name="Texto - Serviços",
    )

    titulo_privacidade = models.CharField(max_length=60, default="Privacidade", verbose_name="Título - Privacidade")
    texto_privacidade = models.TextField(
        blank=True,
        null=True,
        default=(
            "Nós respeitamos sua privacidade. Utilizamos os dados cadastrados apenas para fins de seleção, contato e gestão de oportunidades.\n\n"
            "Você pode solicitar atualização ou exclusão dos seus dados entrando em contato pelos canais oficiais da agência."
        ),
        verbose_name="Texto - Privacidade",
    )

    def __str__(self):
        return "Contatos"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Contatos"
        verbose_name_plural = "Contatos"
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class ContatoSite(models.Model):
    TIPO_CHOICES = (
        ('email', 'E-mail'),
        ('telefone', 'Telefone'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    )

    TELEFONE_TIPO_CHOICES = (
        ('telefone', 'Somente telefone'),
        ('whatsapp', 'Somente WhatsApp'),
        ('ambos', 'Telefone e WhatsApp'),
    )

    configuracao = models.ForeignKey(
        ConfiguracaoSite,
        related_name='contatos',
        on_delete=models.CASCADE,
        verbose_name='Configuração',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    valor = models.CharField(max_length=255, verbose_name='Valor')
    telefone_tipo = models.CharField(
        max_length=20,
        choices=TELEFONE_TIPO_CHOICES,
        blank=True,
        null=True,
        verbose_name='Tipo do número',
        help_text='Usado apenas quando o tipo for Telefone.',
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ('ordem', 'id')

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.valor}"


def _apresentacao_default_expira_em():
    return timezone.now() + timedelta(days=7)


class Apresentacao(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Link')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    expira_em = models.DateTimeField(default=_apresentacao_default_expira_em, verbose_name='Expira em')
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='apresentacoes_criadas',
        verbose_name='Criado por',
    )

    class Meta:
        verbose_name = 'Apresentação'
        verbose_name_plural = 'Apresentações'

    def __str__(self):
        return f"Apresentação {self.uuid}"

    def is_expirada(self) -> bool:
        try:
            return bool(self.expira_em and self.expira_em <= timezone.now())
        except Exception:
            return False


class ApresentacaoItem(models.Model):
    apresentacao = models.ForeignKey(Apresentacao, related_name='itens', on_delete=models.CASCADE)
    promotor = models.ForeignKey(UserProfile, related_name='apresentacoes', on_delete=models.CASCADE)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Item da apresentação'
        verbose_name_plural = 'Itens da apresentação'
        ordering = ('ordem', 'id')

    def __str__(self):
        return f"{self.promotor.nome_completo}"