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
from datetime import date
import re

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

# Desregistra o User padrão para usarmos a versão customizada na Equipe
admin.site.unregister(User)

# ==============================================================================
# 1. UTILITÁRIOS E FILTROS PERSONALIZADOS (SIDEBAR CRM)
# ==============================================================================

def clean_number(val):
    """Limpa strings para conversão numérica (troca vírgula por ponto)."""
    if not val: return None
    try: return float(str(val).replace(',', '.'))
    except ValueError: return None

class GhostFilter(admin.SimpleListFilter):
    """Filtro base para parâmetros que não existem nativamente no banco."""
    def lookups(self, request, model_admin): return []
    def queryset(self, request, queryset): return queryset

class IdadeMinFilter(GhostFilter): title='Idade Mínima'; parameter_name='idade_min'
class IdadeMaxFilter(GhostFilter): title='Idade Máxima'; parameter_name='idade_max'
class AlturaMinFilter(GhostFilter): title='Altura Mínima'; parameter_name='altura_min'
class AlturaMaxFilter(GhostFilter): title='Altura Máxima'; parameter_name='altura_max'

# ==============================================================================
# 2. AÇÕES EM MASSA (DASHBOARD PRINCIPAL)
# ==============================================================================

@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos_massa(modeladmin, request, queryset):
    """Aprova múltiplos perfis simultaneamente."""
    updated = queryset.update(status='aprovado')
    messages.success(request, f"{updated} perfis foram marcados como APROVADOS.")

@admin.action(description='❌ Reprovar/Ajuste em Massa (Popup Inteligente)')
def reprovar_modelos_massa(modeladmin, request, queryset):
    """
    Recebe os parâmetros 'motivo_massa', 'obs_massa' e 'pode_tentar_massa' 
    enviados via injeção JavaScript no formulário de listagem.
    """
    motivo = request.POST.get('motivo_massa', 'outros')
    obs = request.POST.get('obs_massa', '')
    pode_tentar = request.POST.get('pode_tentar_massa') == 'true'
    
    # Define o status com base na escolha do Administrador
    novo_status = 'correcao' if pode_tentar else 'reprovado'
    
    count = queryset.update(
        status=novo_status,
        motivo_reprovacao=motivo,
        observacao_admin=obs,
        data_reprovacao=timezone.now()
    )
    messages.warning(request, f"{count} perfis foram atualizados para {novo_status.upper()}.")

@admin.action(description='🗑️ Excluir Selecionados Permanentemente')
def excluir_modelos_massa(modeladmin, request, queryset):
    """Remove perfis e usuários vinculados do sistema."""
    count = queryset.count()
    queryset.delete()
    messages.info(request, f"{count} perfis foram removidos definitivamente.")

# ==============================================================================
# 3. ADMINISTRAÇÃO DE USUÁRIOS (EQUIPE INTERNA)
# ==============================================================================

@admin.register(User)
class EquipeAdmin(BaseUserAdmin):
    """Configuração da visualização da equipe de gestão no Admin."""
    list_display = ('nome_visual', 'email', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    
    def nome_visual(self, obj): 
        return obj.get_full_name() or obj.username
    nome_visual.short_description = "Nome do Gestor"

# ==============================================================================
# 4. GESTÃO DE TALENTOS (CRM CORE - USERPROFILE)
# ==============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """O coração do CRM OpenCasting - Gestão completa de Promotores."""
    
    change_list_template = "admin/change_list.html"
    change_form_template = "admin/core/userprofile/change_form.html"
    
    class Media:
        css = { 'all': ('css/admin_custom.css',) }
        js = ('js/admin_custom.js',)

    # CONFIGURAÇÃO DA TABELA DE LISTAGEM (VIEW PRINCIPAL)
    list_display = (
        'exibir_foto', 
        'nome_completo', 
        'whatsapp_link', 
        'copy_link_btn', 
        'idade_visual', 
        'status_visual', 
        'acoes_rapidas'
    )
    
    list_filter = (
        'status', 'genero', 'etnia', 'nacionalidade', 
        'is_pcd', 'cabelo_tipo', 'nivel_ingles',
        IdadeMinFilter, IdadeMaxFilter, AlturaMinFilter, AlturaMaxFilter
    )
    
    search_fields = ('nome_completo', 'cpf', 'rg', 'whatsapp', 'instagram', 'user__email')
    actions = [aprovar_modelos_massa, reprovar_modelos_massa, excluir_modelos_massa]
    
    # ==========================================================================
    # IMPORTANTE: DESTRAVAMENTO DE CAMPOS PARA EDIÇÃO (BACKEND)
    # Para que campos como Nacionalidade, Gênero e Etnia sejam editáveis, 
    # eles NÃO podem estar na tupla abaixo. Apenas elementos visuais de leitura.
    # ==========================================================================
    readonly_fields = ('preview_rosto', 'preview_corpo', 'data_reprovacao')

    def get_urls(self):
        """Define as rotas internas para as funcionalidades de CRM."""
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/aprovar/', self.admin_site.admin_view(self.aprovar_view), name='userprofile_aprovar'),
            path('<int:object_id>/reprovar/', self.admin_site.admin_view(self.reprovar_view), name='userprofile_reprovar'),
            path('<int:object_id>/excluir/', self.admin_site.admin_view(self.excluir_view), name='userprofile_excluir'),
            path('<int:object_id>/enviar-senha/', self.admin_site.admin_view(self.enviar_senha_view), name='userprofile_enviar_senha'),
            path('<int:object_id>/gerar-link-senha/', self.admin_site.admin_view(self.gerar_link_senha_view), name='userprofile_gerar_link_senha'),
        ]
        return custom_urls + urls

    # --- VIEWS DE PROCESSAMENTO LÓGICO ---

    def gerar_link_senha_view(self, request, object_id):
        """Gera um token de segurança e retorna o link de reset via JSON."""
        perfil = get_object_or_404(UserProfile, pk=object_id)
        user = perfil.user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        )
        return JsonResponse({'link': link})

    def reprovar_view(self, request, object_id):
        """Processa a reprovação individual salvando motivos e observações."""
        p = get_object_or_404(UserProfile, pk=object_id)
        p.motivo_reprovacao = request.GET.get('motivo')
        p.observacao_admin = request.GET.get('obs', '')
        p.status = 'correcao' if request.GET.get('pode_tentar') == 'true' else 'reprovado'
        p.data_reprovacao = timezone.now()
        p.save()
        messages.warning(request, f"O perfil de {p.nome_completo} foi atualizado.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def aprovar_view(self, request, object_id):
        """Aprova o perfil individualmente."""
        p = get_object_or_404(UserProfile, pk=object_id)
        p.status = 'aprovado'
        p.save()
        messages.success(request, f"Perfil de {p.nome_completo} aprovado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def excluir_view(self, request, object_id):
        """Exclui o perfil e o objeto de usuário vinculado."""
        p = get_object_or_404(UserProfile, pk=object_id)
        nome = p.nome_completo
        p.user.delete()
        messages.error(request, f"Perfil de {nome} removido do sistema.")
        return redirect('/admin/core/userprofile/')

    def enviar_senha_view(self, request, object_id):
        """Dispara o e-mail oficial de redefinição de senha do Django."""
        p = get_object_or_404(UserProfile, pk=object_id)
        if p.user.email:
            form = PasswordResetForm({'email': p.user.email})
            if form.is_valid(): 
                form.save(request=request)
                messages.success(request, "E-mail de recuperação enviado com sucesso.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    # --- MÉTODOS DE FORMATAÇÃO E EXIBIÇÃO ---

    def exibir_foto(self, obj):
        """Renderiza a miniatura da foto de rosto na tabela principal."""
        if obj.foto_rosto:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border: 1px solid #ddd;">', obj.foto_rosto.url)
        return format_html('<div style="width:45px; height:45px; border-radius:50%; background:#f0f0f0; display:flex; align-items:center; justify-content:center; color:#ccc;"><i class="fas fa-user"></i></div>')
    exibir_foto.short_description = "Avatar"

    def copy_link_btn(self, obj):
        """Botão para copiar o link de avaliação rápida."""
        return format_html(
            '<button type="button" class="btn btn-sm" style="background:#673ab7; color:white; border-radius:20px; font-size:10px; font-weight:bold; padding:2px 10px;" '
            'onclick="copiarLinkAvaliacao(\'{}\')"><i class="fas fa-copy"></i> LINK</button>',
            obj.uuid
        )
    copy_link_btn.short_description = "Avaliação"

    def status_visual(self, obj):
        """Badge colorida de status para fácil identificação."""
        cores = {'pendente': '#f39c12', 'aprovado': '#27ae60', 'reprovado': '#c0392b', 'correcao': '#3498db'}
        return format_html('<b style="color: {}; text-transform: uppercase; font-size: 10px;">{}</b>', cores.get(obj.status, '#7f8c8d'), obj.get_status_display())
    status_visual.short_description = "Situação"

    def acoes_rapidas(self, obj): 
        """Botão de acesso rápido ao perfil completo."""
        return format_html(f'<a href="/admin/core/userprofile/{obj.id}/change/" class="btn btn-sm btn-info" style="border-radius:20px; font-weight:bold; padding:2px 12px;"><i class="fas fa-search"></i> ABRIR</a>')
    acoes_rapidas.short_description = "Gestão"

    def idade_visual(self, obj):
        """Calcula e exibe a idade em anos."""
        if obj.data_nascimento:
            today = date.today()
            return f"{today.year - obj.data_nascimento.year} anos"
        return "---"
    idade_visual.short_description = "Idade"

    def whatsapp_link(self, obj):
        """Gera o link de conversa direta para o WhatsApp do promotor."""
        if obj.whatsapp:
            num = re.sub(r'\D', '', str(obj.whatsapp))
            return format_html('<a href="https://wa.me/55{}" target="_blank" style="color:#25D366; font-weight:bold;"><i class="fab fa-whatsapp"></i> Chat</a>', num)
        return "---"
    whatsapp_link.short_description = "Contato"

    def preview_rosto(self, obj): 
        """Preview ampliada da foto de rosto no formulário de edição."""
        return format_html('<img src="{}" style="height:150px; border-radius:12px; border:2px solid #eee;">', obj.foto_rosto.url) if obj.foto_rosto else "Nenhuma foto"
    
    def preview_corpo(self, obj): 
        """Preview ampliada da foto de corpo no formulário de edição."""
        return format_html('<img src="{}" style="height:150px; border-radius:12px; border:2px solid #eee;">', obj.foto_corpo.url) if obj.foto_corpo else "Nenhuma foto"

    def get_queryset(self, request):
        """Aplica filtros customizados de idade e altura via URL parameters."""
        qs = super().get_queryset(request)
        p = request.GET
        # Filtros de Idade
        if p.get('idade_min'): qs = qs.filter(data_nascimento__lte=date.today().replace(year=date.today().year - int(p.get('idade_min'))))
        if p.get('idade_max'): qs = qs.filter(data_nascimento__gt=date.today().replace(year=date.today().year - int(p.get('idade_max')) - 1))
        # Filtros de Altura
        h_min = clean_number(p.get('altura_min'))
        h_max = clean_number(p.get('altura_max'))
        if h_min: qs = qs.filter(altura__gte=h_min)
        if h_max: qs = qs.filter(altura__lte=h_max)
        return qs

    # ESTRUTURA DO FORMULÁRIO DE EDIÇÃO (ORDEM LÓGICA)
    fieldsets = (
        ('DADOS PESSOAIS', {'fields': (('nome_completo','data_nascimento'), ('cpf','rg'), ('nacionalidade','genero','etnia'), 'is_pcd', 'descricao_pcd')}),
        ('CONTATO', {'fields': (('whatsapp','instagram'), ('cep','endereco','numero'), ('bairro','cidade','estado'))}),
        ('PERFIL FÍSICO', {'fields': (('altura','peso'), ('manequim','calcado','tamanho_camiseta'), ('olhos','cabelo_tipo','cabelo_comprimento'))}),
        ('PROFISSIONAL', {'fields': ('experiencia', 'areas_atuacao', 'disponibilidade', ('nivel_ingles','nivel_espanhol','nivel_frances'), 'outros_idiomas')}),
        ('DADOS BANCÁRIOS', {'fields': (('banco','tipo_conta'), ('agencia','conta'), ('tipo_chave_pix','chave_pix'))}),
        ('GALERIA', {'fields': (('preview_rosto','foto_rosto'), ('preview_corpo','foto_corpo'))}),
        ('SISTEMA', {'fields': ('status','motivo_reprovacao','observacao_admin','data_reprovacao'), 'classes': ('collapse',)})
    )

# REGISTRO DOS DEMAIS MODELOS NO ADMIN
admin.site.register(Job)
admin.site.register(Candidatura)
admin.site.register(JobDia)
admin.site.register(Pergunta)
admin.site.register(Resposta)
admin.site.register(Avaliacao)
admin.site.register(ConfiguracaoSite)