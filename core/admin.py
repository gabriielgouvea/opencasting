"""
OPENCASTING CRM - SISTEMA DE GESTÃO DE TALENTOS V6.0
------------------------------------------------------------------
Versão: 6.0 - Compatibilidade Total Jazzmin & Estabilidade de URL
Finalidade: Backend para Listagem Inteligente e Gestão de Promotores.
Desenvolvido para: Gabriel Gouvêa com suporte de IA.
"""

import re
import os
import mimetypes
import base64
from io import BytesIO
from decimal import Decimal
from datetime import timedelta
from datetime import date
from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse, FileResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

# Importação dos Modelos do Sistema OpenCasting
from .models import (
    UserProfile, 
    CpfBanido,
    Cliente,
    Orcamento,
    OrcamentoItem,
    Job, 
    JobDia, 
    Candidatura, 
    Pergunta, 
    Resposta, 
    Avaliacao, 
    ConfiguracaoSite,
    ContatoSite,
    Apresentacao,
    ApresentacaoItem,
)

import requests


@admin.action(description='Gerar link de apresentação (7 dias)')
def gerar_link_apresentacao(modeladmin, request, queryset):
    selected_ids = request.POST.getlist(ACTION_CHECKBOX_NAME) or []
    by_id = {str(obj.pk): obj for obj in queryset}

    # Regra: o link só pode ser gerado com aprovados.
    # Se a lista estiver em pendentes/reprovados e o usuário marcar, nós ignoramos e avisamos.
    aprovados_ids = set(
        UserProfile.objects.filter(pk__in=[int(x) for x in selected_ids if str(x).isdigit()], status='aprovado')
        .values_list('pk', flat=True)
    )

    nao_aprovados = 0
    ordem_promotores: list[UserProfile] = []

    # Mantém ordem do POST
    for pk in selected_ids:
        obj = by_id.get(str(pk))
        if not obj:
            continue
        if obj.pk not in aprovados_ids:
            nao_aprovados += 1
            continue
        ordem_promotores.append(obj)

    # Fallback: se por algum motivo não vierem IDs (ou seleção vazia), usa o queryset
    if not ordem_promotores:
        for obj in queryset:
            if getattr(obj, 'status', None) == 'aprovado':
                ordem_promotores.append(obj)
            else:
                nao_aprovados += 1

    if not ordem_promotores:
        messages.error(request, 'Selecione pelo menos 1 promotor APROVADO para gerar o link.')
        return

    ap = Apresentacao.objects.create(
        criado_por=getattr(request, 'user', None) if getattr(request, 'user', None) and request.user.is_authenticated else None,
        expira_em=timezone.now() + timedelta(days=7),
    )

    for ordem, obj in enumerate(ordem_promotores):
        ApresentacaoItem.objects.create(apresentacao=ap, promotor=obj, ordem=ordem)

    link = request.build_absolute_uri(reverse('apresentacao_publica', kwargs={'uuid': ap.uuid}))
    if nao_aprovados:
        messages.warning(request, f'{nao_aprovados} selecionado(s) não estavam aprovados e foram ignorados.')
    messages.success(request, format_html('Link gerado (expira em 7 dias): <a href="{}" target="_blank">{}</a>', link, link))


class UserProfileAdminForm(forms.ModelForm):
    areas_atuacao = forms.MultipleChoiceField(
        label='Áreas de Interesse',
        choices=UserProfile.AREAS_ATUACAO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._areas_outros_text = None

        raw = (getattr(self.instance, 'areas_atuacao', None) or '').strip()
        if not raw:
            return

        # Preserva possíveis textos livres de "Outros: ..." sem perder ao salvar.
        # O valor costuma ser salvo como: "recepcao, degustacao, outros, Outros: ...".
        match = re.search(r'\boutros\s*:\s*', raw, flags=re.IGNORECASE)
        known_part = raw
        if match:
            known_part = raw[:match.start()].strip().rstrip(',').strip()
            self._areas_outros_text = raw[match.start():].strip()

        parts = [t.strip() for t in known_part.split(',') if t and t.strip()]
        allowed = {k for (k, _label) in UserProfile.AREAS_ATUACAO_CHOICES}
        value_to_label = dict(UserProfile.AREAS_ATUACAO_CHOICES)
        label_to_value = {str(lbl).casefold(): val for val, lbl in UserProfile.AREAS_ATUACAO_CHOICES}

        initial: list[str] = []
        unknown: list[str] = []

        for part in parts:
            if part in allowed:
                initial.append(part)
                continue

            mapped = label_to_value.get(str(part).casefold())
            if mapped:
                initial.append(mapped)
                continue

            unknown.append(part)

        # Se existirem valores legados/desconhecidos, preserva como "Outros: ..." e marca 'outros'.
        if unknown:
            if not self._areas_outros_text:
                self._areas_outros_text = f"Outros: {', '.join(unknown)}"
            if 'outros' not in initial:
                initial.append('outros')

        # Importante: como o ModelForm populou self.initial com a string original,
        # precisamos substituir por lista para o CheckboxSelectMultiple marcar corretamente.
        self.initial['areas_atuacao'] = list(dict.fromkeys(initial))

    def clean_areas_atuacao(self):
        selected = self.cleaned_data.get('areas_atuacao') or []
        selected = [s.strip() for s in selected if s and str(s).strip()]
        selected = list(dict.fromkeys(selected))

        parts = []
        if selected:
            parts.append(', '.join(selected))

        # Mantém "Outros: ..." somente quando o usuário marcar "outros".
        if 'outros' in selected and self._areas_outros_text:
            parts.append(self._areas_outros_text)

        return ', '.join([p for p in parts if p])

    class Meta:
        model = UserProfile
        fields = '__all__'


def _split_csv(value: str) -> list[str]:
    raw = (value or '').strip()
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r'[,;|]+', raw) if p and p.strip()]
    return list(dict.fromkeys(parts))


def _join_csv(values: list[str]) -> str:
    cleaned = [str(v).strip() for v in (values or []) if v and str(v).strip()]
    return ', '.join(list(dict.fromkeys(cleaned)))


class TagInputWidget(forms.TextInput):
    def __init__(self, suggestions: list[str] | None = None, attrs=None):
        attrs = attrs or {}
        attrs.setdefault('data-tag-input', '1')
        if suggestions:
            attrs.setdefault('data-suggestions', '|'.join(suggestions))
        super().__init__(attrs=attrs)


class JobAdminForm(forms.ModelForm):
    tipo_servico = forms.MultipleChoiceField(
        label='Tipo de serviço',
        choices=UserProfile.AREAS_ATUACAO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Selecione uma ou mais áreas (as mesmas do cadastro).',
    )

    tipo_servico_outros = forms.CharField(
        label='Outros (descrever abaixo)',
        required=False,
        widget=forms.TextInput(attrs={'data-oc-outros': '1'}),
    )

    requer_experiencia = forms.ChoiceField(
        label='Precisa de experiência?',
        choices=[('nao', 'Não'), ('sim', 'Sim')],
        required=True,
        widget=forms.RadioSelect,
        initial='nao',
    )

    uniforme_fornecido = forms.ChoiceField(
        label='Uniforme fornecido pela empresa?',
        choices=[('nao', 'Não'), ('sim', 'Sim')],
        required=True,
        widget=forms.RadioSelect,
        initial='nao',
    )

    generos_aceitos = forms.MultipleChoiceField(
        label='Sexo (aceitos)',
        choices=[
            ('masculino', 'Masculino'),
            ('feminino', 'Feminino'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Se não marcar nada, não será exigido.',
    )

    etnias_aceitas = forms.MultipleChoiceField(
        label='Cor/Etnia (aceitas)',
        choices=UserProfile.ETNIA_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Se não marcar nada, não será exigido.',
    )

    olhos_aceitos = forms.MultipleChoiceField(
        label='Cor dos olhos (aceitas)',
        choices=UserProfile.OLHOS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Se não marcar nada, não será exigido.',
    )

    cabelo_tipos_aceitos = forms.MultipleChoiceField(
        label='Tipo de cabelo (aceitos)',
        choices=UserProfile.CABELO_TIPO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Se não marcar nada, não será exigido.',
    )

    cabelo_comprimentos_aceitos = forms.MultipleChoiceField(
        label='Comprimento do cabelo (aceitos)',
        choices=UserProfile.CABELO_TAM_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Se não marcar nada, não será exigido.',
    )

    competencias = forms.CharField(
        label='Competências (tags)',
        required=False,
        help_text='Digite e aperte Enter para adicionar. Separe por vírgula também funciona.',
        widget=TagInputWidget(
            suggestions=[
                'Comunicativo',
                'Sorridente',
                'Proativo',
                'Pontual',
                'Responsável',
                'Alto',
                'Musculoso',
            ]
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.initial['tipo_servico'] = _split_csv(getattr(self.instance, 'tipo_servico', '') or '')
            self.initial['generos_aceitos'] = _split_csv(getattr(self.instance, 'generos_aceitos', '') or '')
            self.initial['etnias_aceitas'] = _split_csv(getattr(self.instance, 'etnias_aceitas', '') or '')

            self.initial['olhos_aceitos'] = _split_csv(getattr(self.instance, 'olhos_aceitos', '') or '')
            self.initial['cabelo_tipos_aceitos'] = _split_csv(getattr(self.instance, 'cabelo_tipos_aceitos', '') or '')
            self.initial['cabelo_comprimentos_aceitos'] = _split_csv(getattr(self.instance, 'cabelo_comprimentos_aceitos', '') or '')

            self.initial['requer_experiencia'] = 'sim' if bool(getattr(self.instance, 'requer_experiencia', False)) else 'nao'
            self.initial['uniforme_fornecido'] = 'sim' if bool(getattr(self.instance, 'uniforme_fornecido', False)) else 'nao'

    def clean_tipo_servico(self):
        return _join_csv(self.cleaned_data.get('tipo_servico') or [])

    def clean_tipo_servico_outros(self):
        val = (self.cleaned_data.get('tipo_servico_outros') or '').strip()
        selected = self.cleaned_data.get('tipo_servico') or []
        if 'outros' in selected:
            return val
        return ''

    def clean_requer_experiencia(self):
        return (self.cleaned_data.get('requer_experiencia') == 'sim')

    def clean_uniforme_fornecido(self):
        return (self.cleaned_data.get('uniforme_fornecido') == 'sim')

    def clean_generos_aceitos(self):
        return _join_csv(self.cleaned_data.get('generos_aceitos') or [])

    def clean_etnias_aceitas(self):
        return _join_csv(self.cleaned_data.get('etnias_aceitas') or [])

    def clean_olhos_aceitos(self):
        return _join_csv(self.cleaned_data.get('olhos_aceitos') or [])

    def clean_cabelo_tipos_aceitos(self):
        return _join_csv(self.cleaned_data.get('cabelo_tipos_aceitos') or [])

    def clean_cabelo_comprimentos_aceitos(self):
        return _join_csv(self.cleaned_data.get('cabelo_comprimentos_aceitos') or [])

    def clean_competencias(self):
        raw = (self.cleaned_data.get('competencias') or '').strip()
        if not raw:
            return ''
        parts = [p.strip() for p in re.split(r'[,;|\n\r]+', raw) if p and p.strip()]
        return _join_csv(parts)

    class Meta:
        model = Job
        fields = '__all__'

    class Media:
        js = ('core/js/admin_job_tags.js', 'core/js/admin_job_enhancements.js',)
        css = {
            'all': ('core/css/admin_job_tags.css',)
        }


class ContatoSiteInlineForm(forms.ModelForm):
    class Meta:
        model = ContatoSite
        fields = ('tipo', 'valor', 'telefone_tipo')
        widgets = {
            'telefone_tipo': forms.RadioSelect,
        }
        labels = {
            'valor': 'Contato',
            'telefone_tipo': 'Esse número é…',
        }
        help_texts = {
            'valor': 'Para Instagram/Facebook, cole o link. Para telefone, pode ser com DDD (ex: (11) 91234-5678).',
            'telefone_tipo': 'Escolha como o número será usado (aparece só quando o tipo for Telefone).',
        }

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        telefone_tipo = cleaned.get('telefone_tipo')

        if tipo == 'telefone':
            # Em alguns cenários (tema/admin custom), o radio pode não vir no POST.
            # Não bloqueia o salvamento: assume o padrão mais comum.
            if not telefone_tipo:
                cleaned['telefone_tipo'] = 'ambos'
        else:
            cleaned['telefone_tipo'] = None

        return cleaned


class ContatoSiteInline(admin.StackedInline):
    model = ContatoSite
    form = ContatoSiteInlineForm
    extra = 0
    ordering = ('ordem', 'id')
    exclude = ('ordem',)
    fields = ('tipo', 'valor', 'telefone_tipo')


def _safe_filename(value: str, fallback: str = 'arquivo') -> str:
    base = (value or '').strip() or fallback
    base = re.sub(r'[\\/:*?"<>|\r\n]+', ' ', base)
    base = re.sub(r'\s+', ' ', base).strip()
    if len(base) > 80:
        base = base[:80].rstrip()
    return base

# Desregistra o User padrão para evitar duplicidade no Jazzmin
try:
    admin.site.unregister(User)
except:
    pass

# ==============================================================================
# 1. UTILITÁRIOS E HELPERS DE CONVERSÃO NUMÉRICA
# ==============================================================================

def clean_number(val):
    """Sanitiza strings numéricas para filtros de banco de dados."""
    if not val:
        return None
    try:
        return float(str(val).replace(',', '.').strip())
    except (ValueError, TypeError):
        return None

# ==============================================================================
# 2. GHOST FILTERS (VERSÃO ESTABILIZADA PARA JAZZMIN)
# ==============================================================================

class GhostFilter(admin.SimpleListFilter):
    """
    Filtros virtuais que permitem a injeção de parâmetros de faixa (Ranges)
    pelo JavaScript. Retornamos uma lista vazia para o Jazzmin não tentar
    gerar links de URL que quebram o sistema (Could not reverse url).
    """
    def lookups(self, request, model_admin):
        return [] # Mantém a URL limpa e evita erros de reverse link

    def queryset(self, request, queryset):
        return queryset


class AreasAtuacaoFilter(admin.SimpleListFilter):
    title = 'Área de Atuação'
    parameter_name = 'area_atuacao'

    def lookups(self, request, model_admin):
        return UserProfile.AREAS_ATUACAO_CHOICES

    def queryset(self, request, queryset):
        raw = (self.value() or '').strip()
        if not raw:
            return queryset

        # Aceita múltiplas áreas via URL: ?area_atuacao=bartender,degustacao
        tokens = [t.strip() for t in re.split(r'[,;|]+', raw) if t and t.strip()]
        if not tokens:
            return queryset

        field = 'areas_atuacao'

        # O campo é salvo como string com tokens separados por vírgula, ex:
        # "recepcao, degustacao, bartender" e opcionalmente ", Outros: ..."
        # Fazemos match por token com limites (início / ", ") para reduzir falsos positivos.
        def token_match_q(token):
            return (
                Q(**{f"{field}__iexact": token}) |
                Q(**{f"{field}__istartswith": f"{token},"}) |
                Q(**{f"{field}__istartswith": f"{token}, "}) |
                Q(**{f"{field}__icontains": f", {token},"}) |
                Q(**{f"{field}__icontains": f", {token}, "}) |
                Q(**{f"{field}__iendswith": f", {token}"})
            )

        combined_q = Q()
        for token in tokens:
            combined_q |= token_match_q(token)

        return queryset.filter(combined_q)

# Definições de parâmetros para a Sidebar Dinâmica (Ranges)
class IdadeMinFilter(GhostFilter): title = 'Idade Mín'; parameter_name = 'idade_min'
class IdadeMaxFilter(GhostFilter): title = 'Idade Máx'; parameter_name = 'idade_max'
class AlturaMinFilter(GhostFilter): title = 'Altura Mín'; parameter_name = 'altura_min'
class AlturaMaxFilter(GhostFilter): title = 'Altura Máx'; parameter_name = 'altura_max'
class PesoMinFilter(GhostFilter): title = 'Peso Mín'; parameter_name = 'peso_min'
class PesoMaxFilter(GhostFilter): title = 'Peso Máx'; parameter_name = 'peso_max'
class SapatoMinFilter(GhostFilter): title = 'Sapato Mín'; parameter_name = 'sapato_min'
class SapatoMaxFilter(GhostFilter): title = 'Sapato Máx'; parameter_name = 'sapato_max'

# ==============================================================================
# 3. AÇÕES DE CRM EM MASSA (AÇÕES DE GESTÃO)
# ==============================================================================

@admin.action(description='✅ Aprovar Talentos Selecionados')
def aprovar_modelos_massa(modeladmin, request, queryset):
    updated = queryset.update(status='aprovado')
    messages.success(request, f"{updated} talentos aprovados com sucesso.")

@admin.action(description='❌ Reprovar em Massa (Popup Inteligente)')
def reprovar_modelos_massa(modeladmin, request, queryset):
    """Ação que recebe parâmetros injetados via JavaScript para reprovação."""
    motivo = request.POST.get('motivo_massa', 'outros')
    obs = request.POST.get('obs_massa', '')
    queryset.update(status='reprovado', motivo_reprovacao=motivo, observacao_admin=obs, data_reprovacao=timezone.now())
    messages.warning(request, "Lote de talentos atualizado para REPROVADO.")

@admin.action(description='🗑️ Excluir Permanentemente')
def excluir_modelos_massa(modeladmin, request, queryset):
    queryset.delete()
    messages.error(request, "Registros selecionados foram removidos definitivamente.")

# ==============================================================================
# 4. ADMINISTRAÇÃO DA EQUIPE INTERNA (STAFF GESTOR)
# ==============================================================================

@admin.register(User)
class EquipeAdmin(BaseUserAdmin):
    """Configuração da visualização da equipe interna de gestão."""
    list_display = ('nome_visual', 'email', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    def nome_visual(self, obj): return obj.get_full_name() or obj.username
    nome_visual.short_description = "Nome do Gestor"

# ==============================================================================
# 5. GESTÃO DE TALENTOS (USERPROFILE ADMIN - O MOTOR DA AGÊNCIA)
# ==============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Controlador Master da Base de Promotores.
    Focado em triagem absoluta e filtros de alta precisão.
    """
    # A linha abaixo foi comentada para evitar conflito com o Jazzmin.
    # O Jazzmin gerencia a lista automaticamente e garante que os filtros sejam renderizados.
    # change_list_template = "admin/change_list.html"
    change_form_template = "admin/core/userprofile/change_form.html"

    form = UserProfileAdminForm
    
    # Remove contador nativo para dar lugar à barra de botões customizada
    actions_selection_counter = False
    
    class Media:
        css = { 'all': ('css/admin_custom.css',) }
        js = ('js/admin_custom.js',)

    # 1. LISTAGEM COM NOME E STATUS ACOPLADO (PONTO 1)
    list_display = (
        'exibir_foto', 
        'nome_com_status', 
        'whatsapp_link', 
        'acoes_rapidas'
    )
    
    list_display_links = ('nome_com_status',)
    
    # 2. SISTEMA DE FILTROS TOTAIS (PONTOS 2 E 3 - ESTABILIZADO)
    # Importante: Apenas ChoiceFields e GhostFilters para não travar o Jazzmin
    list_filter = (
        'status', 'genero', 'etnia', 'nacionalidade', 
        'is_pcd', 'cabelo_tipo', 'cabelo_comprimento', 'olhos',
        'tamanho_camiseta', 'nivel_ingles', 'disponibilidade', 'experiencia',
        AreasAtuacaoFilter,
        IdadeMinFilter, IdadeMaxFilter, 
        AlturaMinFilter, AlturaMaxFilter,
        PesoMinFilter, PesoMaxFilter,
        SapatoMinFilter, SapatoMaxFilter
    )
    
    search_fields = ('nome_completo', 'cpf', 'whatsapp')
    actions = [aprovar_modelos_massa, reprovar_modelos_massa, excluir_modelos_massa, gerar_link_apresentacao]
    
    readonly_fields = ('preview_rosto', 'preview_corpo', 'data_reprovacao')

    # --------------------------------------------------------------------------
    # LÓGICA DE FILTRAGEM POR FAIXA (RANGES DE PESO E SAPATO)
    # --------------------------------------------------------------------------
    def get_queryset(self, request):
        """Interceptor de busca que processa as faixas numéricas da URL."""
        qs = super().get_queryset(request)
        p = request.GET

        # Filtro de Idade
        if p.get('idade_min'): 
            try:
                idade_min = int(p.get('idade_min'))
                data_limite = date.today().replace(year=date.today().year - idade_min)
                qs = qs.filter(data_nascimento__lte=data_limite)
            except (ValueError, TypeError):
                pass
        
        if p.get('idade_max'): 
            try:
                idade_max = int(p.get('idade_max'))
                data_limite = date.today().replace(year=date.today().year - idade_max - 1)
                qs = qs.filter(data_nascimento__gt=data_limite)
            except (ValueError, TypeError):
                pass

        # Função auxiliar para aplicar faixas numéricas
        def apply_range(queryset, p_min, p_max, db_field):
            v_min = clean_number(p.get(p_min))
            v_max = clean_number(p.get(p_max))
            if v_min is not None: 
                queryset = queryset.filter(**{f"{db_field}__gte": v_min})
            if v_max is not None: 
                queryset = queryset.filter(**{f"{db_field}__lte": v_max})
            return queryset

        # Processamento das Faixas Solicitadas
        qs = apply_range(qs, 'altura_min', 'altura_max', 'altura')
        qs = apply_range(qs, 'peso_min', 'peso_max', 'peso')
        qs = apply_range(qs, 'sapato_min', 'sapato_max', 'calcado')

        # ------------------------------------------------------------------
        # SUPORTE A MULTI-SELEÇÃO (via JS na sidebar)
        #
        # A UI customizada envia parâmetros no formato: <campo>__in=val1,val2
        # Mantemos os list_filter padrão do Django/Jazzmin (que usam __exact)
        # e aplicamos aqui apenas quando __in estiver presente.
        # ------------------------------------------------------------------
        multi_fields = (
            'genero',
            'etnia',
            'nacionalidade',
            'is_pcd',
            'cabelo_tipo',
            'cabelo_comprimento',
            'olhos',
            'tamanho_camiseta',
            'nivel_ingles',
            'disponibilidade',
            'experiencia',
        )

        def split_multi(raw):
            return [t.strip() for t in re.split(r'[,;|]+', (raw or '')) if t and t.strip()]

        for field in multi_fields:
            raw = p.get(f'{field}__in')
            if not raw:
                continue

            vals = split_multi(raw)
            if not vals:
                continue

            if field == 'is_pcd':
                parsed = []
                for v in vals:
                    vnorm = (v or '').strip().lower()
                    if vnorm in ('1', 'true', 't', 'sim', 's', 'yes', 'y'):
                        parsed.append(True)
                    elif vnorm in ('0', 'false', 'f', 'nao', 'não', 'n', 'no'):
                        parsed.append(False)
                if parsed:
                    qs = qs.filter(**{f'{field}__in': parsed})
            else:
                qs = qs.filter(**{f'{field}__in': vals})

        return qs

    # --- NAVEGAÇÃO: APROVADOS / PENDENTES ---
    def changelist_view(self, request, extra_context=None):
        """Por padrão, a Base de Promotores abre em APROVADOS.

        Também suporta o parâmetro legado ?status=... (dashboard antigo) convertendo
        para o parâmetro padrão do Django Admin (?status__exact=...).
        """
        try:
            params = request.GET
            # Legado: /admin/core/userprofile/?status=pendente
            if 'status' in params and 'status__exact' not in params:
                q = params.copy()
                q['status__exact'] = q.get('status')
                q.pop('status', None)
                return redirect(f"{request.path}?{q.urlencode()}")

            # Default: se não informou status, abre apenas APROVADOS
            if 'status__exact' not in params:
                q = params.copy()
                q['status__exact'] = 'aprovado'
                return redirect(f"{request.path}?{q.urlencode()}")
        except Exception:
            pass

        return super().changelist_view(request, extra_context=extra_context)

    def aprovados_view(self, request):
        return redirect('/admin/core/userprofile/?status__exact=aprovado')

    def pendentes_view(self, request):
        return redirect('/admin/core/userprofile/?status__exact=pendente')

    def correcao_view(self, request):
        return redirect('/admin/core/userprofile/?status__exact=correcao')

    # --- MÉTODOS VISUAIS (INTERFACE) ---

    def nome_com_status(self, obj):
        return format_html(
            '<span class="oc-nome" style="font-weight:700; color:#2c3e50;">{}</span>',
            obj.nome_completo.upper(),
        )
    nome_com_status.short_description = "Promotor"

    def exibir_foto(self, obj):
        if obj.foto_rosto:
            return format_html('<img src="{}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:2px solid #eee;">', obj.foto_rosto.url)
        return format_html('<div style="width:48px; height:48px; border-radius:50%; background:#f5f5f5; display:flex; align-items:center; justify-content:center;"><i class="fas fa-user text-muted"></i></div>')
    exibir_foto.short_description = "Avatar"

    def whatsapp_link(self, obj):
        if obj.whatsapp:
            num = re.sub(r'\D', '', str(obj.whatsapp))
            # Exibe o número (como pedido) e mantém o link do WhatsApp
            return format_html(
                '<a href="https://wa.me/55{}" target="_blank" style="color:#25D366; font-weight:800; font-size:12px;">'
                '<i class="fab fa-whatsapp"></i> {}</a>',
                num,
                str(obj.whatsapp),
            )
        return "---"
    whatsapp_link.short_description = "Contato"

    def acoes_rapidas(self, obj): 
        return format_html(f'<a href="/admin/core/userprofile/{obj.id}/change/" class="btn btn-sm btn-info" style="border-radius:20px; font-weight:bold; padding:3px 18px;"><i class="fas fa-search"></i> ABRIR</a>')
    acoes_rapidas.short_description = "Gestão"

    # --- LÓGICA DE URLs E PROCESSAMENTO ---

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Páginas (atalhos) da Base
            path('aprovados/', self.admin_site.admin_view(self.aprovados_view), name='userprofile_aprovados'),
            path('pendentes/', self.admin_site.admin_view(self.pendentes_view), name='userprofile_pendentes'),
            path('aguardando-ajuste/', self.admin_site.admin_view(self.correcao_view), name='userprofile_correcao'),

            # Ações por objeto
            path('<int:object_id>/aprovar/', self.admin_site.admin_view(self.aprovar_view), name='userprofile_aprovar'),
            path('<int:object_id>/reprovar/', self.admin_site.admin_view(self.reprovar_view), name='userprofile_reprovar'),
            path('<int:object_id>/excluir/', self.admin_site.admin_view(self.excluir_view), name='userprofile_excluir'),
            path('<int:object_id>/voltar-analise/', self.admin_site.admin_view(self.voltar_analise_view), name='userprofile_voltar_analise'),
            path('<int:object_id>/banir-cpf/', self.admin_site.admin_view(self.banir_cpf_view), name='userprofile_banir_cpf'),
            path('<int:object_id>/enviar-senha/', self.admin_site.admin_view(self.enviar_senha_view), name='userprofile_enviar_senha'),
            path('<int:object_id>/gerar-link-senha/', self.admin_site.admin_view(self.gerar_link_senha_view), name='userprofile_gerar_link_senha'),
            path('<int:object_id>/download-foto-rosto/', self.admin_site.admin_view(self.download_foto_rosto_view), name='userprofile_download_foto_rosto'),
            path('<int:object_id>/download-foto-corpo/', self.admin_site.admin_view(self.download_foto_corpo_view), name='userprofile_download_foto_corpo'),
            # Tenta baixar as duas (sem ZIP). Alguns navegadores podem bloquear múltiplos downloads automáticos.
            path('<int:object_id>/download-fotos/', self.admin_site.admin_view(self.download_fotos_view), name='userprofile_download_fotos'),
            path('<int:object_id>/download-pdf/', self.admin_site.admin_view(self.download_pdf_view), name='userprofile_download_pdf'),
        ]
        return custom_urls + urls

    def _download_image_field(self, request, p: UserProfile, field_file, label: str):
        def field_ext(ff) -> str:
            try:
                _, ext = os.path.splitext(ff.name or '')
                ext = (ext or '').strip()
                if not ext:
                    return '.jpg'
                if len(ext) > 10:
                    return '.jpg'
                return ext
            except Exception:
                return '.jpg'

        if not field_file or not getattr(field_file, 'name', None):
            messages.warning(request, f'Este promotor não possui {label.lower()} cadastrada.')
            return redirect(request.META.get('HTTP_REFERER', '..'))

        nome = _safe_filename(p.nome_completo, fallback=f'promotor-{p.pk}')
        ext = field_ext(field_file)
        filename = f'{label} - {nome}{ext}'

        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or 'application/octet-stream'

        try:
            return FileResponse(field_file.open('rb'), as_attachment=True, filename=filename, content_type=content_type)
        except TypeError:
            resp = FileResponse(field_file.open('rb'), as_attachment=True)
            resp['Content-Disposition'] = f'attachment; filename="{filename}"'
            resp['Content-Type'] = content_type
            return resp

    def download_foto_rosto_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        return self._download_image_field(request, p, p.foto_rosto, 'Foto rosto')

    def download_foto_corpo_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        return self._download_image_field(request, p, p.foto_corpo, 'Foto corpo')

    def download_fotos_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)

        has_rosto = bool(p.foto_rosto and getattr(p.foto_rosto, 'name', None))
        has_corpo = bool(p.foto_corpo and getattr(p.foto_corpo, 'name', None))

        if not has_rosto and not has_corpo:
            messages.warning(request, 'Este promotor não possui fotos cadastradas.')
            return redirect(request.META.get('HTTP_REFERER', '..'))

        # Se tiver só uma, baixa direto
        if has_rosto and not has_corpo:
            return self._download_image_field(request, p, p.foto_rosto, 'Foto rosto')
        if has_corpo and not has_rosto:
            return self._download_image_field(request, p, p.foto_corpo, 'Foto corpo')

        # Se tiver as duas: tenta baixar ambas via iframes (sem ZIP).
        # Observação: alguns navegadores exigem permissão para múltiplos downloads.
        url_rosto = reverse('admin:userprofile_download_foto_rosto', args=[p.pk])
        url_corpo = reverse('admin:userprofile_download_foto_corpo', args=[p.pk])
        html = f"""
<!doctype html>
<html lang='pt-br'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width,initial-scale=1' />
    <title>Baixando fotos...</title>
    <style>
      body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial; padding:24px;}}
      .box{{max-width:640px;margin:0 auto;border:1px solid #ddd;border-radius:16px;padding:18px;}}
      h1{{font-size:18px;margin:0 0 6px 0;}}
      p{{margin:0 0 12px 0;color:#444;}}
      a{{display:inline-block;margin-right:12px;}}
    </style>
  </head>
  <body>
    <div class='box'>
      <h1>Baixando fotos do promotor...</h1>
      <p>Se o navegador bloquear múltiplos downloads, use os links abaixo:</p>
      <p>
        <a href='{url_rosto}'>Baixar foto rosto</a>
        <a href='{url_corpo}'>Baixar foto corpo</a>
      </p>
    </div>
    <iframe src='{url_rosto}' style='display:none' aria-hidden='true'></iframe>
    <iframe src='{url_corpo}' style='display:none' aria-hidden='true'></iframe>
  </body>
</html>
"""
        return HttpResponse(html)

    def download_pdf_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)

        # Import local para não quebrar o admin caso a dependência ainda não esteja instalada.
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        except Exception:
            messages.error(request, 'Dependência de PDF não instalada (reportlab).')
            return redirect(request.META.get('HTTP_REFERER', '..'))

        cfg = None
        try:
            cfg = ConfiguracaoSite.load()
        except Exception:
            cfg = None

        agencia_nome = (getattr(cfg, 'titulo_site', None) or 'Casting Certo').strip()
        agencia_email = (getattr(cfg, 'email_contato', None) or '').strip()

        now = timezone.localtime(timezone.now())
        created = None
        try:
            created = timezone.localtime(p.criado_em) if p.criado_em else None
        except Exception:
            created = None

        nome_promotor = _safe_filename(p.nome_completo, fallback=f'promotor-{p.pk}')
        pdf_name = f'Ficha - {nome_promotor}.pdf'

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=1.6*cm,
            bottomMargin=1.6*cm,
            title=f'Ficha - {p.nome_completo}',
            author=agencia_nome,
        )

        styles = getSampleStyleSheet()
        h1 = styles['Heading1']
        h2 = styles['Heading2']
        body = styles['BodyText']

        story = []
        story.append(Paragraph(agencia_nome, h1))
        if agencia_email:
            story.append(Paragraph(f'Contato: {agencia_email}', body))
        story.append(Paragraph(f'Gerado em: {now.strftime("%d/%m/%Y %H:%M")}', body))
        story.append(Spacer(1, 0.35*cm))

        story.append(Paragraph('Ficha do Promotor', h2))
        story.append(Paragraph(f'Nome: <b>{p.nome_completo}</b>', body))
        story.append(Paragraph(f'UUID: {p.uuid}', body))
        if created:
            story.append(Paragraph(f'Cadastrado em: {created.strftime("%d/%m/%Y %H:%M")}', body))
        story.append(Spacer(1, 0.4*cm))

        # Foto (rosto) se possível
        try:
            if p.foto_rosto and getattr(p.foto_rosto, 'name', None):
                p.foto_rosto.open('rb')
                img_bytes = p.foto_rosto.read()
                try:
                    p.foto_rosto.close()
                except Exception:
                    pass
                if img_bytes:
                    img = Image(BytesIO(img_bytes))
                    img.drawWidth = 5.2*cm
                    img.drawHeight = 5.2*cm
                    story.append(img)
                    story.append(Spacer(1, 0.25*cm))
        except Exception:
            pass

        def disp(getter, fallback='---'):
            try:
                v = getter()
                return v if v not in (None, '') else fallback
            except Exception:
                return fallback

        def val(x, fallback='---'):
            return x if x not in (None, '') else fallback

        # Monta tabela de dados
        rows = []
        rows.append(['Status', disp(p.get_status_display)])
        rows.append(['CPF', val(p.cpf)])
        rows.append(['WhatsApp', val(p.whatsapp)])
        rows.append(['Instagram', val(p.instagram)])
        rows.append(['Gênero', disp(p.get_genero_display)])
        rows.append(['Cor/Etnia', disp(p.get_etnia_display)])
        rows.append(['Nacionalidade', disp(p.get_nacionalidade_display)])
        rows.append(['PCD', 'Sim' if bool(p.is_pcd) else 'Não'])
        if p.is_pcd:
            rows.append(['Descrição PCD', val(p.descricao_pcd)])
        rows.append(['Altura', (str(p.altura) + ' m') if p.altura else '---'])
        rows.append(['Peso', (str(p.peso) + ' kg') if p.peso else '---'])
        rows.append(['Camiseta', disp(p.get_tamanho_camiseta_display)])
        rows.append(['Olhos', disp(p.get_olhos_display)])
        rows.append(['Cabelo (tipo)', disp(p.get_cabelo_tipo_display)])
        rows.append(['Cabelo (compr.)', disp(p.get_cabelo_comprimento_display)])
        rows.append(['Experiência', disp(p.get_experiencia_display)])
        rows.append(['Disponibilidade', disp(p.get_disponibilidade_display)])
        rows.append(['Áreas de atuação', val(p.areas_atuacao)])

        endereco = ', '.join([str(v).strip() for v in [p.endereco, p.numero, p.bairro, p.cidade, p.estado, p.cep] if v])
        if endereco:
            rows.append(['Endereço', endereco])

        table = Table(rows, colWidths=[5.2*cm, 11.2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#DDDDDD')),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#DDDDDD')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.35*cm))
        story.append(Paragraph('Este documento foi gerado automaticamente pela plataforma.', body))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
        return resp

    def enviar_senha_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        if p.user.email:
            form = PasswordResetForm({'email': p.user.email})
            if form.is_valid(): form.save(request=request); messages.success(request, "E-mail enviado.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def aprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id); p.status = 'aprovado'; p.save()
        messages.success(request, f"{p.nome_completo} aprovado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def reprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)

        # Espera POST vindo do popup
        if request.method != 'POST':
            messages.error(request, "A reprovação deve ser enviada pelo formulário.")
            return redirect(request.META.get('HTTP_REFERER', '..'))

        motivo = (request.POST.get('motivo') or 'outros').strip()
        obs = (request.POST.get('observacao') or '').strip()
        permitir_ajuste_raw = (request.POST.get('permitir_ajuste') or '1').strip().lower()
        permitir_ajuste = permitir_ajuste_raw in ['1', 'true', 'on', 'yes', 'sim']
        dias_bloqueio_raw = (request.POST.get('dias_bloqueio') or '').strip()

        p.motivo_reprovacao = motivo
        p.observacao_admin = obs
        p.data_reprovacao = timezone.now()

        # 1) Pode ajustar: vai para CORRECAO e recebe e-mail com link de edição
        if permitir_ajuste:
            p.status = 'correcao'
            p.bloqueado_ate = None
            p.save()

            try:
                if p.user and p.user.email:
                    link_edicao = request.build_absolute_uri(reverse('editar_perfil'))
                    assunto = 'Casting Certo: Ajustes necessários no seu cadastro'
                    texto = (
                        f"Olá {p.nome_completo},\n\n"
                        f"Identificamos que seu cadastro precisa de ajustes para seguir para análise.\n"
                        f"Motivo: {p.get_motivo_reprovacao_display()}\n\n"
                        f"Para corrigir, acesse: {link_edicao}\n"
                    )
                    if obs:
                        texto += f"\nMensagem da agência: {obs}\n"
                    html = (
                        f"<p>Olá <strong>{p.nome_completo}</strong>,</p>"
                        f"<p>Seu cadastro precisa de ajustes para seguir para análise.</p>"
                        f"<p><strong>Motivo:</strong> {p.get_motivo_reprovacao_display()}</p>"
                        + (f"<p><strong>Mensagem da agência:</strong> {obs}</p>" if obs else "")
                        + f"<p><a href=\"{link_edicao}\" style=\"display:inline-block;padding:12px 18px;border-radius:999px;background:#009688;color:#fff;text-decoration:none;font-weight:800;\">Corrigir cadastro</a></p>"
                    )
                    send_mail(
                        assunto,
                        texto,
                        settings.DEFAULT_FROM_EMAIL,
                        [p.user.email],
                        fail_silently=True,
                        html_message=html,
                    )
            except Exception:
                pass

        # 2) Não pode ajustar agora: reprovado + bloqueio por N dias
        else:
            dias_bloqueio = None
            try:
                dias_bloqueio = int(dias_bloqueio_raw)
            except (TypeError, ValueError):
                dias_bloqueio = None

            if not dias_bloqueio or dias_bloqueio < 1:
                dias_bloqueio = 90

            p.status = 'reprovado'
            p.bloqueado_ate = (timezone.now().date() + timedelta(days=dias_bloqueio))
            p.save()

            try:
                if p.user and p.user.email:
                    assunto = 'Casting Certo: Atualização do seu cadastro'
                    texto = (
                        f"Olá {p.nome_completo},\n\n"
                        f"Analisamos seu cadastro e, no momento, não foi possível aprovar.\n"
                        f"Motivo: {p.get_motivo_reprovacao_display()}\n\n"
                        f"Você poderá tentar novamente em {dias_bloqueio} dias.\n"
                    )
                    if obs:
                        texto += f"\nMensagem da agência: {obs}\n"
                    send_mail(
                        assunto,
                        texto,
                        settings.DEFAULT_FROM_EMAIL,
                        [p.user.email],
                        fail_silently=True,
                    )
            except Exception:
                pass

        # Resposta AJAX (popup) ou redirect normal
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'status': p.status})

        messages.warning(request, f"{p.nome_completo} atualizado para: {p.get_status_display()}.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def excluir_view(self, request, object_id):
        if request.method != 'POST':
            messages.error(request, "A exclusão deve ser confirmada.")
            return redirect(request.META.get('HTTP_REFERER', '..'))

        p = get_object_or_404(UserProfile, pk=object_id)
        try:
            p.user.delete()
        except Exception:
            # fallback
            p.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect('/admin/core/userprofile/')

    def voltar_analise_view(self, request, object_id):
        if request.method != 'POST':
            messages.error(request, "A ação deve ser confirmada.")
            return redirect(request.META.get('HTTP_REFERER', '..'))

        p = get_object_or_404(UserProfile, pk=object_id)
        p.status = 'pendente'
        p.motivo_reprovacao = None
        p.observacao_admin = ''
        p.data_reprovacao = None
        p.bloqueado_ate = None
        p.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'status': p.status})
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def banir_cpf_view(self, request, object_id):
        if request.method != 'POST':
            messages.error(request, "A ação deve ser confirmada.")
            return redirect(request.META.get('HTTP_REFERER', '..'))

        p = get_object_or_404(UserProfile, pk=object_id)
        cpf_raw = (p.cpf or '').strip()
        cpf_digits = re.sub(r'\D', '', cpf_raw)
        if not cpf_digits:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': 'CPF não informado.'}, status=400)
            messages.error(request, "Não foi possível banir: CPF não informado.")
            return redirect(request.META.get('HTTP_REFERER', '..'))

        with transaction.atomic():
            CpfBanido.objects.get_or_create(cpf=cpf_digits, defaults={'motivo': 'Banido pelo admin'})
            try:
                p.user.delete()
            except Exception:
                p.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect('/admin/core/userprofile/')

    def gerar_link_senha_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        token = default_token_generator.make_token(p.user)
        uid = urlsafe_base64_encode(force_bytes(p.user.pk))
        link = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
        return JsonResponse({'link': link})

    def preview_rosto(self, obj): return format_html('<img src="{}" style="height:150px; border-radius:12px;">', obj.foto_rosto.url) if obj.foto_rosto else "---"
    def preview_corpo(self, obj): return format_html('<img src="{}" style="height:150px; border-radius:12px;">', obj.foto_corpo.url) if obj.foto_corpo else "---"

    fieldsets = (
        ('DADOS PESSOAIS', {'fields': (('nome_completo','data_nascimento'), ('cpf','rg'), ('nacionalidade','genero','etnia'))}),
        ('CONTATO', {'fields': (('whatsapp','instagram'), ('cep','endereco','numero'), ('bairro','cidade','estado'))}),
        ('FÍSICO', {'fields': (('altura','peso'), ('manequim','calcado','tamanho_camiseta'), ('olhos','cabelo_tipo'))}),
        ('PROFISSIONAL', {'fields': ('is_pcd', 'descricao_pcd', 'experiencia', 'areas_atuacao', 'disponibilidade', ('nivel_ingles','nivel_espanhol','nivel_frances'))}),
        ('DADOS BANCÁRIOS', {'fields': (('banco','tipo_conta'), ('agencia','conta'), ('tipo_chave_pix','chave_pix'))}),
        ('GALERIA', {'fields': (('preview_rosto','foto_rosto'), ('preview_corpo','foto_corpo'))}),
    )

# REGISTRO FINAL DOS MODELOS
class JobDiaInline(admin.TabularInline):
    model = JobDia
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    inlines = [JobDiaInline]

    # Jazzmin: força um único formulário (sem abas)
    changeform_format = 'single'

    list_display = ('titulo', 'empresa', 'status', 'data_pagamento')
    list_filter = ('status', 'data_pagamento')
    search_fields = ('titulo', 'empresa', 'cidade', 'estado', 'endereco', 'local')

    readonly_fields = ('latitude', 'longitude', 'geocodificado_em', 'criado_em')

    # Sem colunas: tudo em uma sequência vertical
    fields = (
        'titulo',
        'empresa',
        'status',
        'tipo_servico',
        'tipo_servico_outros',
        'descricao',
        'uniforme_fornecido',
        'cep',
        'endereco',
        'numero',
        'bairro',
        'cidade',
        'estado',
        'local',
        'data_pagamento',
        'requer_experiencia',
        'generos_aceitos',
        'etnias_aceitas',
        'olhos_aceitos',
        'cabelo_tipos_aceitos',
        'cabelo_comprimentos_aceitos',
        'nivel_ingles_min',
        'competencias',
        'latitude',
        'longitude',
        'geocodificado_em',
        'criado_em',
    )

admin.site.register(Candidatura)
admin.site.register(Resposta)
admin.site.register(Avaliacao)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    changeform_format = 'single'
    list_display = ('razao_social', 'nome_fantasia', 'cnpj_formatado', 'cidade', 'uf', 'email_nfe')
    search_fields = (
        'cnpj',
        'razao_social',
        'nome_fantasia',
        'email_nfe',
        'telefone',
        'inscricao_estadual',
        'inscricao_municipal',
        'cidade',
        'uf',
    )
    list_filter = ()

    fieldsets = (
        ('Identificação', {
            'fields': (
                'cnpj',
                'razao_social',
                'nome_fantasia',
                'data_abertura',
                'situacao_cadastral',
                'natureza_juridica',
                'cnae_principal',
                'cnae_principal_descricao',
            )
        }),
        ('Fiscal (NF)', {
            'fields': (
                'inscricao_estadual',
                'inscricao_municipal',
                'regime_tributario',
                'email_nfe',
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'uf',
            )
        }),
        ('Contato', {
            'fields': (
                'telefone',
                'contato_nome',
                'contato_cargo',
                'observacoes',
            )
        }),
    )

    class Media:
        js = ('core/js/admin_cliente.js',)
        css = {
            'all': ('core/css/admin_cliente.css',)
        }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'cnpj' and formfield and getattr(formfield, 'widget', None):
            # Permite digitar CNPJ com máscara no admin
            formfield.widget.attrs.setdefault('maxlength', 18)
            formfield.widget.attrs.setdefault('inputmode', 'numeric')
        return formfield

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'buscar-cnpj/',
                self.admin_site.admin_view(self.buscar_cnpj_view),
                name='core_cliente_buscar_cnpj',
            )
        ]
        return custom + urls

    @method_decorator(require_GET)
    def buscar_cnpj_view(self, request):
        cnpj = request.GET.get('cnpj', '')
        cnpj_digits = re.sub(r'\D+', '', cnpj)
        if len(cnpj_digits) != 14:
            return JsonResponse({'ok': False, 'error': 'CNPJ inválido.'}, status=400)

        try:
            resp = requests.get(
                f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_digits}',
                timeout=8,
                headers={'Accept': 'application/json'},
            )
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Falha ao consultar a API de CNPJ.'}, status=502)

        if resp.status_code != 200:
            return JsonResponse({'ok': False, 'error': 'CNPJ não encontrado.'}, status=404)

        try:
            data = resp.json() or {}
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Resposta inválida da API.'}, status=502)

        # Normaliza para os IDs dos campos do admin.
        out = {
            'cnpj': cnpj_digits,
            'razao_social': data.get('razao_social') or '',
            'nome_fantasia': data.get('nome_fantasia') or '',
            'data_abertura': data.get('data_inicio_atividade') or '',
            'situacao_cadastral': data.get('descricao_situacao_cadastral') or data.get('situacao_cadastral') or '',
            'natureza_juridica': data.get('natureza_juridica') or '',
            'cnae_principal': str(data.get('cnae_fiscal') or '') or '',
            'cnae_principal_descricao': data.get('cnae_fiscal_descricao') or '',
            'cep': data.get('cep') or '',
            'logradouro': data.get('logradouro') or '',
            'numero': data.get('numero') or '',
            'complemento': data.get('complemento') or '',
            'bairro': data.get('bairro') or '',
            'cidade': data.get('municipio') or '',
            'uf': (data.get('uf') or '').upper(),
            'telefone': (data.get('ddd_telefone_1') or data.get('telefone_1') or '') or '',
        }

        return JsonResponse({'ok': True, 'data': out})

class OrcamentoAdminForm(forms.ModelForm):
    localized_fields = ('desconto_valor', 'desconto_percentual')

    class Meta:
        model = Orcamento
        fields = '__all__'
        widgets = {
            # Em muitos browsers, DateInput vira type=date e não aceita máscara. Mantemos texto.
            'data_evento': forms.TextInput(
                attrs={
                    'inputmode': 'numeric',
                    'placeholder': 'dd/mm/aaaa',
                }
            ),
            # DecimalField com TextInput para aceitar vírgula e máscara BR
            'desconto_valor': forms.TextInput(
                attrs={
                    'inputmode': 'decimal',
                    'placeholder': '0,00',
                }
            ),
            'desconto_percentual': forms.TextInput(
                attrs={
                    'inputmode': 'decimal',
                    'placeholder': '0,00',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('desconto_valor', 'desconto_percentual'):
            field = self.fields.get(name)
            if not field:
                continue
            field.localize = True
            try:
                field.widget.is_localized = True
            except Exception:
                pass


class OrcamentoItemInlineForm(forms.ModelForm):
    localized_fields = ('valor_diaria',)

    class Meta:
        model = OrcamentoItem
        fields = '__all__'
        widgets = {
            'valor_diaria': forms.TextInput(
                attrs={
                    'inputmode': 'decimal',
                    'placeholder': '0,00',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get('valor_diaria')
        if field:
            field.localize = True
            try:
                field.widget.is_localized = True
            except Exception:
                pass

        # Para inlines NOVOS, não pré-preencher com defaults do model (ex.: 1 / 8 / 1).
        # Mantém valores normalmente quando o item já existe.
        if not self.is_bound and not getattr(self.instance, 'pk', None):
            for name in ('quantidade', 'carga_horaria_horas', 'diarias'):
                if name in self.fields:
                    self.fields[name].initial = None
                    self.initial[name] = ''
                    try:
                        setattr(self.instance, name, None)
                    except Exception:
                        pass


class OrcamentoItemInline(admin.StackedInline):
    model = OrcamentoItem
    form = OrcamentoItemInlineForm
    extra = 1
    ordering = ('ordem', 'id')
    exclude = ('ordem', 'total')
    fields = ('funcao', 'quantidade', 'carga_horaria_horas', 'valor_diaria', 'diarias')


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    form = OrcamentoAdminForm
    changeform_format = 'single'
    list_display = ('id', 'cliente_coluna', 'criado_em', 'acoes')
    search_fields = ('id', 'cliente__razao_social', 'cliente__nome_fantasia', 'cliente__cnpj')
    list_filter = ()
    sortable_by = ('criado_em',)

    # Remove seleção por checkbox + dropdown de ações (não usado nesta tela)
    actions = None
    actions_selection_counter = False

    fields = ('cliente', 'data_evento', 'validade_dias', 'desconto_valor', 'desconto_percentual')
    inlines = (OrcamentoItemInline,)

    change_list_template = 'admin/core/orcamento/change_list.html'
    change_form_template = 'admin/core/orcamento/change_form.html'

    class Media:
        js = ('core/js/admin_orcamento.js',)
        css = {
            'all': ('core/css/admin_orcamento.css',)
        }

    @admin.display(description='Cliente', ordering='cliente__razao_social')
    def cliente_coluna(self, obj: Orcamento):
        c = getattr(obj, 'cliente', None)
        if not c:
            return '-'
        # Preferimos o mesmo texto que o sistema já usa (razao_social/nome_fantasia),
        # mas sem o "(opcional)" no cabeçalho.
        return str(c)

    @admin.display(description='', ordering=False)
    def acoes(self, obj: Orcamento):
        delete_url = reverse('admin:core_orcamento_delete', args=[obj.pk])
        pdf_url = reverse('admin:core_orcamento_pdf', args=[obj.pk])
        return format_html(
            '<details class="oc-actions" data-oc-actions="1">'
            '  <summary class="oc-actions__toggle" aria-label="Ações" title="Ações">⋯</summary>'
            '  <div class="oc-actions__menu" role="menu">'
            '    <a class="oc-actions__item" role="menuitem" href="{}" data-oc-delete="1" data-oc-id="{}">Excluir</a>'
            '    <a class="oc-actions__item" role="menuitem" href="{}">Baixar PDF</a>'
            '  </div>'
            '</details>',
            delete_url,
            obj.pk,
            pdf_url,
        )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:orcamento_id>/pdf/',
                self.admin_site.admin_view(self.pdf_view),
                name='core_orcamento_pdf',
            )
        ]
        return custom + urls

    @method_decorator(require_GET)
    def pdf_view(self, request, orcamento_id: int):
        import base64
        import mimetypes
        from django.contrib.staticfiles import finders
        from django.template.loader import render_to_string
        from django.utils import timezone

        orcamento = get_object_or_404(Orcamento.objects.prefetch_related('itens', 'cliente'), pk=orcamento_id)
        config_site = ConfiguracaoSite.load()

        pdf_engine = (os.getenv('ORCAMENTO_PDF_ENGINE') or 'auto').strip().lower()

        def _static_file_data_uri(static_rel_path: str) -> str | None:
            found = finders.find(static_rel_path)
            if not found:
                return None
            mime, _ = mimetypes.guess_type(found)
            if not mime:
                mime = 'application/octet-stream'
            try:
                with open(found, 'rb') as f:
                    encoded = base64.b64encode(f.read()).decode('ascii')
                return f"data:{mime};base64,{encoded}"
            except Exception:
                return None

        def _instagram_handle(url: str | None) -> str | None:
            u = (url or '').strip()
            if not u:
                return None
            u = u.replace('https://', '').replace('http://', '')
            if 'instagram.com' in u:
                parts = [p for p in u.split('/') if p]
                if parts:
                    last = parts[-1]
                    if last.lower() in {'instagram.com', 'www.instagram.com'} and len(parts) >= 2:
                        last = parts[-2]
                    last = last.split('?')[0].strip('@')
                    return f"@{last.upper()}" if last else None
            # se já vier como @handle
            if u.startswith('@'):
                return u.upper()
            return None

        meses = [
            'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
        ]

        contatos_qs = getattr(config_site, 'contatos', None)
        contatos = list(contatos_qs.all()) if contatos_qs is not None else []
        contatos_por_tipo = {
            'email': [],
            'telefone': [],
            'instagram': [],
            'facebook': [],
        }
        for c in contatos:
            if c.tipo in contatos_por_tipo:
                contatos_por_tipo[c.tipo].append(c)

        contato_email_principal = contatos_por_tipo['email'][0] if contatos_por_tipo['email'] else None
        contato_whatsapp_principal = None
        for c in contatos_por_tipo['telefone']:
            if (c.telefone_tipo or '').strip() in {'whatsapp', 'ambos'}:
                contato_whatsapp_principal = c
                break

        dt = timezone.localtime(orcamento.criado_em) if orcamento.criado_em else timezone.now()
        mes_ano = f"{meses[dt.month - 1].capitalize()}, {dt.year}"
        site_domain = request.get_host()
        instagram_handle = _instagram_handle(getattr(config_site, 'instagram_link', None))

        data_evento_fmt = None
        if getattr(orcamento, 'data_evento', None):
            try:
                data_evento_fmt = orcamento.data_evento.strftime('%d/%m/%Y')
            except Exception:
                data_evento_fmt = None

        validade_dias = int(orcamento.validade_dias or 0)
        frase_validade = f"Este orçamento tem validade de {validade_dias} dias corridos a partir de hoje." if validade_dias else None
        itens = list(orcamento.itens.all())
        subtotal_geral = Decimal('0.00')
        for item in itens:
            subtotal_geral += (item.total or Decimal('0.00'))

        desconto_aplicado = orcamento.calcular_desconto_aplicado(subtotal_geral)
        total_final = (subtotal_geral - desconto_aplicado).quantize(Decimal('0.01'))

        desconto_tipo = None
        desconto_percentual_texto = None
        try:
            desconto_pct = Decimal(str(orcamento.desconto_percentual or '0'))
        except Exception:
            desconto_pct = Decimal('0')
        try:
            desconto_val = Decimal(str(orcamento.desconto_valor or '0'))
        except Exception:
            desconto_val = Decimal('0')

        if desconto_pct and desconto_pct > 0:
            desconto_tipo = 'pct'
            try:
                pct_2 = desconto_pct.quantize(Decimal('0.01'))
            except Exception:
                pct_2 = desconto_pct
            if pct_2 == pct_2.to_integral_value():
                desconto_percentual_texto = str(int(pct_2))
            else:
                desconto_percentual_texto = f"{pct_2:.2f}".replace('.', ',')
        elif desconto_val and desconto_val > 0:
            desconto_tipo = 'valor'

        html = render_to_string(
            'pdfs/orcamento.html',
            {
                'orcamento': orcamento,
                'itens': itens,
                'subtotal_geral': subtotal_geral,
                'desconto_aplicado': desconto_aplicado,
                'total_geral': total_final,
                'desconto_tipo': desconto_tipo,
                'desconto_percentual_texto': desconto_percentual_texto,
                'desconto_valor_informado': desconto_val,
                'config_site': config_site,
                'data_formatada': dt.strftime('%d/%m/%Y'),
                'validade_dias': validade_dias,
                'valido_ate': (orcamento.valido_ate.strftime('%d/%m/%Y') if orcamento.valido_ate else None),
                'observacoes': None,
                'mes_ano': mes_ano,
                'site_domain': site_domain,
                'instagram_handle': instagram_handle,
                'pdf_engine': pdf_engine,
                # Para o Chromium (Playwright) funciona melhor embutir imagem.
                # Para xhtml2pdf, usamos STATIC_URL + link_callback.
                'logo_src': (_static_file_data_uri('images/logo.png') if pdf_engine in {'auto', 'playwright'} else f"{settings.STATIC_URL}images/logo.png"),
                'cliente_nome': (orcamento.cliente.razao_social if orcamento.cliente_id else None),
                'cliente_cnpj': (orcamento.cliente.cnpj_formatado if (orcamento.cliente_id and orcamento.cliente.cnpj) else None),
                'data_evento': data_evento_fmt,
                'frase_validade': frase_validade,
                'contato_telefone': (getattr(contato_whatsapp_principal, 'valor', None) or None),
                'contato_email': (getattr(contato_email_principal, 'valor', None) or None),
            },
            request=request,
        )

        if request.GET.get('format') == 'html':
            return HttpResponse(html, content_type='text/html; charset=utf-8')

        # 1) Tenta Chromium (Playwright) se configurado ou em auto
        if pdf_engine in {'auto', 'playwright'}:
            try:
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page(viewport={"width": 794, "height": 1123})  # ~A4 @96dpi
                    page.set_content(html, wait_until='load')
                    page.emulate_media(media='print')
                    pdf_bytes = page.pdf(
                        format='A4',
                        print_background=True,
                        prefer_css_page_size=True,
                    )
                    browser.close()

                filename = f"orcamento-{orcamento.pk}.pdf"
                return FileResponse(BytesIO(pdf_bytes), as_attachment=True, filename=filename)
            except Exception as e:
                if pdf_engine == 'playwright':
                    return HttpResponse(
                        f'Falha ao gerar PDF via Chromium (Playwright): {e}',
                        status=500,
                        content_type='text/plain; charset=utf-8',
                    )
                # auto -> cai para xhtml2pdf

        # 2) Fallback: xhtml2pdf (mais compatível em hosts restritos como PythonAnywhere)
        try:
            from xhtml2pdf import pisa
        except Exception as e:
            return HttpResponse(
                f'Não foi possível gerar o PDF (faltam dependências). Erro: {e}',
                status=500,
                content_type='text/plain; charset=utf-8',
            )

        def link_callback(uri: str, rel: str | None = None):
            # Resolve /static/... via STATIC_ROOT (prod) ou finders (dev)
            if uri.startswith(settings.STATIC_URL):
                static_path = uri[len(settings.STATIC_URL):]
                static_root = getattr(settings, 'STATIC_ROOT', None)
                if static_root:
                    candidate = os.path.join(str(static_root), static_path)
                    if os.path.exists(candidate):
                        return candidate

                found = finders.find(static_path)
                if found:
                    return found

            # Resolve /media/... via MEDIA_ROOT
            if uri.startswith(settings.MEDIA_URL):
                media_path = uri[len(settings.MEDIA_URL):]
                return os.path.join(str(settings.MEDIA_ROOT), media_path)

            return uri

        # Re-render com logo via STATIC_URL (xhtml2pdf não é confiável com data URI)
        html_xhtml2pdf = render_to_string(
            'pdfs/orcamento.html',
            {
                'orcamento': orcamento,
                'itens': itens,
                'subtotal_geral': subtotal_geral,
                'desconto_aplicado': desconto_aplicado,
                'total_geral': total_final,
                'desconto_tipo': desconto_tipo,
                'desconto_percentual_texto': desconto_percentual_texto,
                'desconto_valor_informado': desconto_val,
                'config_site': config_site,
                'data_formatada': dt.strftime('%d/%m/%Y'),
                'validade_dias': validade_dias,
                'valido_ate': (orcamento.valido_ate.strftime('%d/%m/%Y') if orcamento.valido_ate else None),
                'observacoes': None,
                'mes_ano': mes_ano,
                'site_domain': site_domain,
                'instagram_handle': instagram_handle,
                'pdf_engine': 'xhtml2pdf',
                'logo_src': f"{settings.STATIC_URL}images/logo.png",
                'cliente_nome': (orcamento.cliente.razao_social if orcamento.cliente_id else None),
                'cliente_cnpj': (orcamento.cliente.cnpj_formatado if (orcamento.cliente_id and orcamento.cliente.cnpj) else None),
                'data_evento': data_evento_fmt,
                'frase_validade': frase_validade,
                'contato_telefone': (getattr(contato_whatsapp_principal, 'valor', None) or None),
                'contato_email': (getattr(contato_email_principal, 'valor', None) or None),
            },
            request=request,
        )

        out = BytesIO()
        status = pisa.CreatePDF(src=html_xhtml2pdf, dest=out, encoding='UTF-8', link_callback=link_callback)
        if status.err:
            return HttpResponse('Erro ao gerar PDF do orçamento.', status=500, content_type='text/plain; charset=utf-8')

        out.seek(0)
        filename = f"orcamento-{orcamento.pk}.pdf"
        return FileResponse(out, as_attachment=True, filename=filename)

    def response_add(self, request, obj, post_url_continue=None):
        if '_generate_pdf' in request.POST:
            return redirect(reverse('admin:core_orcamento_pdf', args=(obj.pk,)))
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if '_generate_pdf' in request.POST:
            return redirect(reverse('admin:core_orcamento_pdf', args=(obj.pk,)))
        return super().response_change(request, obj)


class ConfiguracaoSiteContatosForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSite
        fields = ()


@admin.register(ConfiguracaoSite)
class ConfiguracaoSiteAdmin(admin.ModelAdmin):
    list_display = ('titulo_site',)
    inlines = (ContatoSiteInline,)
    form = ConfiguracaoSiteContatosForm
    fieldsets = ((None, {'fields': ()}),)

    # Jazzmin: evita tabs/scroll desnecessários
    changeform_format = 'single'

    change_form_template = 'admin/core/configuracaosite/change_form.html'

    class Media:
        js = ('core/js/admin_contatos.js',)
        css = {
            'all': ('core/css/admin_contatos.css',)
        }

    def changelist_view(self, request, extra_context=None):
        # Ao clicar no menu "Contatos", abre direto o singleton.
        obj = ConfiguracaoSite.load()
        return redirect(reverse('admin:core_configuracaosite_change', args=(obj.pk,)))

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # Ajuda a diagnosticar validações dos inlines quando o admin mostra apenas
        # o banner genérico "Please correct the errors below".
        try:
            if request.method == 'POST':
                inline_sets = context.get('inline_admin_formsets') or []
                msgs = []
                for inline_admin_formset in inline_sets:
                    fs = getattr(inline_admin_formset, 'formset', None)
                    if not fs:
                        continue
                    try:
                        non_form = list(fs.non_form_errors())
                    except Exception:
                        non_form = []
                    if non_form:
                        msgs.append(f"Inline {inline_admin_formset.opts.verbose_name_plural}: {non_form}")

                    try:
                        for idx, ferr in enumerate(getattr(fs, 'errors', []) or []):
                            if ferr:
                                msgs.append(f"Inline {inline_admin_formset.opts.verbose_name_plural} item {idx + 1}: {dict(ferr)}")
                    except Exception:
                        pass

                if msgs:
                    # Mostra só um resumo para não poluir demais.
                    messages.error(request, "Erros ao salvar Contatos: " + " | ".join(msgs[:6]))
        except Exception:
            pass

        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def has_add_permission(self, request):
        # Singleton
        return not ConfiguracaoSite.objects.filter(pk=1).exists()

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(CpfBanido)

# FIM DO ARQUIVO ADMIN.PY V6.0