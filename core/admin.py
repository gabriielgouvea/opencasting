from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from datetime import date
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta, Avaliacao, ConfiguracaoSite

admin.site.unregister(User)

# ==============================================================================
# 1. UTILITÁRIOS E FILTROS PERSONALIZADOS
# ==============================================================================
def clean_number(val):
    if not val: return None
    try: return float(str(val).replace(',', '.'))
    except ValueError: return None

class GhostFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin): return []
    def queryset(self, request, queryset): return queryset

class IdadeMinFilter(GhostFilter): title='Idade Min'; parameter_name='idade_min'
class IdadeMaxFilter(GhostFilter): title='Idade Max'; parameter_name='idade_max'
class AlturaMinFilter(GhostFilter): title='Altura Min'; parameter_name='altura_min'
class AlturaMaxFilter(GhostFilter): title='Altura Max'; parameter_name='altura_max'

# ==============================================================================
# 2. AÇÕES EM MASSA INTELIGENTES (CONECTADAS AO POP-UP DO JS)
# ==============================================================================
@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos_massa(modeladmin, request, queryset):
    updated = queryset.update(status='aprovado')
    messages.success(request, f"{updated} perfis APROVADOS.")

@admin.action(description='❌ Reprovar/Ajuste em Massa')
def reprovar_modelos_massa(modeladmin, request, queryset):
    """
    Esta ação agora recebe os dados injetados pelo SweetAlert2 no JS.
    """
    motivo = request.POST.get('motivo_massa', 'outros')
    obs = request.POST.get('obs_massa', '')
    pode_tentar = request.POST.get('pode_tentar_massa') == 'true'
    
    novo_status = 'correcao' if pode_tentar else 'reprovado'
    
    count = queryset.update(
        status=novo_status,
        motivo_reprovacao=motivo,
        observacao_admin=obs,
        data_reprovacao=timezone.now()
    )
    messages.warning(request, f"{count} perfis atualizados para {novo_status.upper()}.")

@admin.action(description='🗑️ Excluir Selecionados')
def excluir_modelos_massa(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    messages.info(request, f"{count} perfis excluídos permanentemente.")

# ==============================================================================
# 3. ADMINISTRAÇÃO DO PERFIL (CRM)
# ==============================================================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list.html"
    change_form_template = "admin/core/userprofile/change_form.html"
    
    class Media:
        css = { 'all': ('css/admin_custom.css',) }
        js = ('js/admin_custom.js',)

    # LISTAGEM: Padronizada (Removido o botão individual da coluna do meio)
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
        IdadeMinFilter, IdadeMaxFilter, AlturaMinFilter, AlturaMaxFilter
    )
    
    search_fields = ('nome_completo', 'cpf', 'whatsapp')
    actions = [aprovar_modelos_massa, reprovar_modelos_massa, excluir_modelos_massa]
    
    # IMPORTANTE: Apenas as previews são somente leitura. 
    # Nacionalidade, Etnia e Idiomas ficam livres para edição no formulário.
    readonly_fields = ('preview_rosto', 'preview_corpo')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/aprovar/', self.admin_site.admin_view(self.aprovar_view), name='userprofile_aprovar'),
            path('<int:object_id>/reprovar/', self.admin_site.admin_view(self.reprovar_view), name='userprofile_reprovar'),
            path('<int:object_id>/excluir/', self.admin_site.admin_view(self.excluir_view), name='userprofile_excluir'),
            path('<int:object_id>/enviar-senha/', self.admin_site.admin_view(self.enviar_senha_view), name='userprofile_enviar_senha'),
        ]
        return custom_urls + urls

    # --- VIEWS DE PROCESSAMENTO INDIVIDUAL ---
    def reprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        p.motivo_reprovacao = request.GET.get('motivo')
        p.observacao_admin = request.GET.get('obs', '')
        p.status = 'correcao' if request.GET.get('pode_tentar') == 'true' else 'reprovado'
        p.data_reprovacao = timezone.now()
        p.save()
        messages.warning(request, f"Perfil de {p.nome_completo} atualizado.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def aprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        p.status = 'aprovado'; p.save()
        messages.success(request, f"Perfil de {p.nome_completo} aprovado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def excluir_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        p.user.delete(); return redirect('/admin/core/userprofile/')

    def enviar_senha_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        if p.user.email:
            form = PasswordResetForm({'email': p.user.email})
            if form.is_valid(): form.save(request=request); messages.success(request, "Link enviado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    # --- COMPONENTES VISUAIS ---
    def exibir_foto(self, obj):
        return format_html('<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;border:1px solid #ddd;">', obj.foto_rosto.url) if obj.foto_rosto else "-"
    
    def copy_link_btn(self, obj):
        return format_html('<button type="button" class="btn btn-sm" style="background:#673ab7;color:white;border-radius:20px;font-size:10px;font-weight:bold;" onclick="copiarLinkAvaliacao(\'{}\')"><i class="fas fa-copy"></i> LINK</button>', obj.uuid)
    
    def status_visual(self, obj):
        cores = {'pendente': '#f39c12', 'aprovado': '#27ae60', 'reprovado': '#c0392b', 'correcao': '#3498db'}
        return format_html('<b style="color: {}; text-transform: uppercase;">{}</b>', cores.get(obj.status, '#7f8c8d'), obj.get_status_display())

    def acoes_rapidas(self, obj): 
        return format_html(f'<a href="/admin/core/userprofile/{obj.id}/change/" class="btn btn-sm btn-info" style="border-radius:20px;">🔍 ABRIR</a>')

    def idade_visual(self, obj):
        return f"{date.today().year - obj.data_nascimento.year} anos" if obj.data_nascimento else "-"

    def whatsapp_link(self, obj):
        if obj.whatsapp:
            num = ''.join(filter(str.isdigit, str(obj.whatsapp)))
            return format_html('<a href="https://wa.me/55{}" target="_blank" style="color:#25D366;font-weight:bold;"><i class="fab fa-whatsapp"></i> Chat</a>', num)
        return "-"

    def preview_rosto(self, obj): return format_html('<img src="{}" style="height:120px;border-radius:8px;">', obj.foto_rosto.url) if obj.foto_rosto else "-"
    def preview_corpo(self, obj): return format_html('<img src="{}" style="height:120px;border-radius:8px;">', obj.foto_corpo.url) if obj.foto_corpo else "-"

    # ESTRUTURA DO FORMULÁRIO DE EDIÇÃO (DROPDOWNS DESTRAVADOS)
    fieldsets = (
        ('DADOS PESSOAIS', {'fields': (('nome_completo','data_nascimento'), ('cpf','rg'), ('nacionalidade','genero','etnia'), 'is_pcd', 'descricao_pcd')}),
        ('CONTATO', {'fields': (('whatsapp','instagram'), ('cep','endereco','numero'), ('bairro','cidade','estado'))}),
        ('PERFIL FÍSICO', {'fields': (('altura','peso'), ('manequim','calcado','tamanho_camiseta'), ('olhos','cabelo_tipo','cabelo_comprimento'))}),
        ('PROFISSIONAL', {'fields': ('experiencia', 'areas_atuacao', 'disponibilidade', ('nivel_ingles','nivel_espanhol','nivel_frances'), 'outros_idiomas')}),
        ('DADOS BANCÁRIOS', {'fields': (('banco','tipo_conta'), ('agencia','conta'), ('tipo_chave_pix','chave_pix'))}),
        ('GALERIA', {'fields': (('preview_rosto','foto_rosto'), ('preview_corpo','foto_corpo'))}),
        ('SISTEMA', {'fields': ('status','motivo_reprovacao','observacao_admin','data_reprovacao'), 'classes': ('collapse',)})
    )

# REGISTRO DOS MODELOS
admin.site.register(Job)
admin.site.register(Candidatura)
admin.site.register(JobDia)
admin.site.register(Pergunta)
admin.site.register(Resposta)
admin.site.register(Avaliacao)
admin.site.register(ConfiguracaoSite)