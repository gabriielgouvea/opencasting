from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta, Avaliacao

# Remove o admin padrão para usarmos o nosso personalizado
admin.site.unregister(User)
# admin.site.unregister(Group) 

# --- FUNÇÃO AUXILIAR: MENSAGEM NO TOPO ---
def mostrar_aviso_topo(request, titulo, texto):
    msg = format_html(f'<strong>📌 {titulo}:</strong> {texto}')
    messages.add_message(request, messages.INFO, msg)

# --- AÇÃO: ENVIAR SENHA (GLOBAL) ---
@admin.action(description='📧 Enviar E-mail de Senha')
def enviar_reset_senha(modeladmin, request, queryset):
    enviados = 0
    for obj in queryset:
        # Pega o email do User ou do UserProfile
        email = getattr(obj, 'email', None)
        if not email and hasattr(obj, 'user'):
            email = obj.user.email
            
        if email:
            try:
                form = PasswordResetForm({'email': email})
                if form.is_valid():
                    form.save(request=request)
                    enviados += 1
            except: pass
    
    if enviados > 0:
        messages.success(request, f"Link de redefinição enviado para {enviados} pessoas.")
    else:
        messages.warning(request, "Nenhum e-mail válido encontrado para envio.")

# ==============================================================================
# 1. EQUIPE INTERNA (ADMINISTRADORES)
# ==============================================================================
@admin.register(User)
class EquipeAdmin(BaseUserAdmin):
    # Check 5: Mostrar NOME ao invés de apenas e-mail/usuário
    list_display = ('nome_visual', 'email', 'tipo_acesso', 'ultimo_acesso')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('first_name',)
    actions = [enviar_reset_senha]

    # Layout Simplificado de Edição
    fieldsets = (
        ('👤 Identificação', {
            'fields': ('username', 'first_name', 'last_name', 'email'),
            'description': 'Dados básicos de acesso.'
        }),
        ('🔑 Permissões de Acesso', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': '<b>Ativo:</b> Bloqueia/Desbloqueia o acesso.<br><b>Equipe (Staff):</b> Permite entrar neste painel.<br><b>Superusuário:</b> Acesso total.'
        }),
    )

    def nome_visual(self, obj):
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username
    nome_visual.short_description = "Nome do Colaborador"

    def tipo_acesso(self, obj):
        if obj.is_superuser: return format_html('<span style="color:red; font-weight:bold;">Super Admin</span>')
        if obj.is_staff: return format_html('<span style="color:green; font-weight:bold;">Equipe</span>')
        return "Usuário Comum"
    tipo_acesso.short_description = "Nível"

    def ultimo_acesso(self, obj):
        return obj.last_login
    ultimo_acesso.short_description = "Último Login"

    def changelist_view(self, request, extra_context=None):
        mostrar_aviso_topo(request, "Gestão da Equipe", "Cadastre aqui apenas quem trabalha DENTRO da agência.")
        return super().changelist_view(request, extra_context=extra_context)

# ==============================================================================
# 2. BASE DE PROMOTORES
# ==============================================================================
@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos(modeladmin, request, queryset):
    queryset.update(status='aprovado')
    messages.success(request, "Promotores APROVADOS e liberados.")

@admin.action(description='❌ Reprovar Selecionados')
def reprovar_modelos(modeladmin, request, queryset):
    queryset.update(status='reprovado')
    messages.warning(request, "Promotores REPROVADOS.")

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'whatsapp', 'status_visual', 'nota_visual', 'acoes_rapidas')
    list_display_links = ('nome_completo',)
    search_fields = ('nome_completo', 'cpf', 'user__email', 'whatsapp')
    list_filter = ('status', 'estado', 'manequim')
    # ADICIONE ISSO NO FINAL DA CLASSE UserProfileAdmin:
    class Media:
        js = ('js/admin_custom.js',)
        css = {
            'all': ('css/admin_custom.css',)
        }
    
    # Essas ações aparecerão como BOTÕES no topo graças ao Javascript que vamos criar
    actions = [aprovar_modelos, reprovar_modelos, enviar_reset_senha]
    
    readonly_fields = ('preview_rosto', 'preview_corpo')

    fieldsets = (
        ('🚨 APROVAÇÃO', {
            'fields': ('status', 'motivo_reprovacao', 'observacao_admin'),
            'classes': ('extrapretty',),
        }),
        ('👤 DADOS PESSOAIS', {
            'fields': ('nome_completo', 'cpf', 'whatsapp', 'data_nascimento', 'editar_login'),
        }),
        ('📸 FOTOS', {
            'fields': (('preview_rosto', 'foto_rosto'), ('preview_corpo', 'foto_corpo')),
        }),
        ('📍 ENDEREÇO & BANCO', {
            'fields': ('cidade', 'estado', 'banco', 'chave_pix'),
            'classes': ('collapse',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        mostrar_aviso_topo(request, "Base de Talentos", "Gerencie os cadastros. Selecione os nomes na lista abaixo para ver os botões de ação.")
        return super().changelist_view(request, extra_context=extra_context)

    # Visuais
    def preview_rosto(self, obj):
        return format_html('<img src="{}" style="height:150px; border-radius:10px;" />', obj.foto_rosto.url) if obj.foto_rosto else "-"
    
    def preview_corpo(self, obj):
        return format_html('<img src="{}" style="height:150px; border-radius:10px;" />', obj.foto_corpo.url) if obj.foto_corpo else "-"

    def status_visual(self, obj):
        cor = {'aprovado':'#28a745', 'reprovado':'#dc3545', 'pendente':'#ffc107'}.get(obj.status, '#6c757d')
        icon = {'aprovado':'check_circle', 'reprovado':'cancel', 'pendente':'hourglass_empty'}.get(obj.status, '')
        return format_html(f'<span style="color:{cor}; font-weight:bold; display:flex; align-items:center; gap:5px;"><i class="material-icons" style="font-size:16px;">{icon}</i> {obj.get_status_display()}</span>')
    status_visual.short_description = "Status"

    def nota_visual(self, obj):
        return format_html(f'<b style="color:#ffc107;">★ {obj.nota_media()}</b>') if obj.nota_media() else "-"
    nota_visual.short_description = "Nota"

    def acoes_rapidas(self, obj):
        if not obj.uuid: return "-"
        url = f"http://127.0.0.1:8000/p/{obj.uuid}/"
        return format_html(f'<a href="{url}" target="_blank" class="btn btn-sm btn-info" style="color:white;">Ver Portfólio</a>')
    acoes_rapidas.short_description = "Ações"

    def editar_login(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html(f'<a href="{url}" target="_blank" style="color:#009688;">🖊️ Alterar E-mail/Senha</a>')
    editar_login.short_description = "Login"

# ==============================================================================
# 3. VAGAS
# ==============================================================================
class JobAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'local', 'data_pagamento', 'inscritos_visual', 'status_badge')
    list_filter = ('status',)
    
    def status_badge(self, obj):
        cor = 'green' if obj.status == 'aberto' else 'gray'
        return format_html(f'<span style="color:{cor}; font-weight:bold;">● {obj.get_status_display()}</span>')
    status_badge.short_description = "Status"

    def inscritos_visual(self, obj):
        count = obj.candidatura_set.count()
        return format_html(f'<span style="background:#e0f2f1; color:#009688; padding:2px 8px; border-radius:10px; font-weight:bold;">{count}</span>')
    inscritos_visual.short_description = "Inscritos"

# ==============================================================================
# 4. CANDIDATURAS
# ==============================================================================
@admin.action(description='✅ Selecionar para o Job')
def aprovar_candidatura(modeladmin, request, queryset):
    queryset.update(status='aprovado')

class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('job', 'modelo', 'status_visual')
    list_filter = ('status', 'job')
    actions = [aprovar_candidatura]

    def status_visual(self, obj):
        cor = {'aprovado':'green', 'reprovado':'red', 'pendente':'orange'}.get(obj.status, 'black')
        return format_html(f'<b style="color:{cor}">{obj.get_status_display()}</b>')
    status_visual.short_description = "Situação"

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Candidatura, CandidaturaAdmin)
admin.site.register(Pergunta)