"""
OPENCASTING CRM - SISTEMA DE GESTÃO DE TALENTOS V6.0
------------------------------------------------------------------
Versão: 6.0 - Compatibilidade Total Jazzmin & Estabilidade de URL
Finalidade: Backend para Listagem Inteligente e Gestão de Promotores.
Desenvolvido para: Gabriel Gouvêa com suporte de IA.
"""

import re
from datetime import date
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Importação dos Modelos do Sistema OpenCasting
from .models import (
    UserProfile, 
    Job, 
    JobDia, 
    Candidatura, 
    Pergunta, 
    Resposta, 
    Avaliacao, 
    ConfiguracaoSite
)

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
        IdadeMinFilter, IdadeMaxFilter, 
        AlturaMinFilter, AlturaMaxFilter,
        PesoMinFilter, PesoMaxFilter,
        SapatoMinFilter, SapatoMaxFilter
    )
    
    search_fields = ('nome_completo', 'cpf', 'whatsapp')
    actions = [aprovar_modelos_massa, reprovar_modelos_massa, excluir_modelos_massa]
    
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

        return qs

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
            path('<int:object_id>/aprovar/', self.admin_site.admin_view(self.aprovar_view), name='userprofile_aprovar'),
            path('<int:object_id>/reprovar/', self.admin_site.admin_view(self.reprovar_view), name='userprofile_reprovar'),
            path('<int:object_id>/excluir/', self.admin_site.admin_view(self.excluir_view), name='userprofile_excluir'),
            path('<int:object_id>/enviar-senha/', self.admin_site.admin_view(self.enviar_senha_view), name='userprofile_enviar_senha'),
            path('<int:object_id>/gerar-link-senha/', self.admin_site.admin_view(self.gerar_link_senha_view), name='userprofile_gerar_link_senha'),
        ]
        return custom_urls + urls

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
        p = get_object_or_404(UserProfile, pk=object_id); p.status = 'reprovar'; p.save()
        messages.warning(request, f"{p.nome_completo} reprovado.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def excluir_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id); p.user.delete()
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
        ('SISTEMA', {'fields': ('status','motivo_reprovacao','observacao_admin','data_reprovacao'), 'classes': ('collapse',)})
    )

# REGISTRO FINAL DOS MODELOS
admin.site.register(Job)
admin.site.register(Candidatura)
admin.site.register(Pergunta)
admin.site.register(Resposta)
admin.site.register(Avaliacao)
admin.site.register(ConfiguracaoSite)

# FIM DO ARQUIVO ADMIN.PY V6.0