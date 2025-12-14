from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta, Avaliacao

# Remove o admin padrão para usarmos o nosso personalizado
admin.site.unregister(User)

# --- FUNÇÃO AUXILIAR: MENSAGEM NO TOPO ---
def mostrar_aviso_topo(request, titulo, texto):
    msg = format_html(f'<strong>📌 {titulo}:</strong> {texto}')
    messages.add_message(request, messages.INFO, msg)

# --- AÇÃO: ENVIAR SENHA (GLOBAL) ---
@admin.action(description='📧 Enviar E-mail de Senha')
def enviar_reset_senha(modeladmin, request, queryset):
    enviados = 0
    for obj in queryset:
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
        messages.success(request, f"Link enviado para {enviados} pessoas.")
    else:
        messages.warning(request, "Nenhum e-mail válido encontrado.")

# ==============================================================================
# 1. EQUIPE INTERNA (ADMINISTRADORES)
# ==============================================================================
@admin.register(User)
class EquipeAdmin(BaseUserAdmin):
    list_display = ('nome_visual', 'email', 'tipo_acesso', 'ultimo_acesso')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('first_name',)
    actions = [enviar_reset_senha]

    fieldsets = (
        ('👤 Identificação', {'fields': ('username', 'first_name', 'last_name', 'email')}),
        ('🔑 Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    def nome_visual(self, obj):
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username
    nome_visual.short_description = "Nome"

    def tipo_acesso(self, obj):
        if obj.is_superuser: return format_html('<span style="color:red; font-weight:bold;">Super Admin</span>')
        if obj.is_staff: return format_html('<span style="color:green; font-weight:bold;">Equipe</span>')
        return "Usuário Comum"
    tipo_acesso.short_description = "Nível"

    def ultimo_acesso(self, obj): return obj.last_login
    ultimo_acesso.short_description = "Último Login"

# ==============================================================================
# 2. BASE DE PROMOTORES (ATUALIZADO COM OS NOVOS CAMPOS)
# ==============================================================================
@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos(modeladmin, request, queryset):
    count = 0
    for perfil in queryset:
        if perfil.status != 'aprovado':
            perfil.status = 'aprovado'
            perfil.save() # Dispara e-mail
            count += 1
    messages.success(request, f"{count} perfis aprovados!")

@admin.action(description='❌ Reprovar Selecionados')
def reprovar_modelos(modeladmin, request, queryset):
    for perfil in queryset:
        perfil.status = 'reprovado'
        perfil.save()
    messages.warning(request, "Perfis reprovados.")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'whatsapp', 'status_visual', 'acoes_rapidas')
    list_filter = ('status', 'genero', 'experiencia', 'nacionalidade', 'is_pcd', 'olhos')
    search_fields = ('nome_completo', 'cpf', 'user__email', 'whatsapp')
    actions = [aprovar_modelos, reprovar_modelos, enviar_reset_senha]
    
    readonly_fields = ('preview_rosto', 'preview_corpo', 'editar_login')

    # --- ORGANIZAÇÃO DOS CAMPOS (FIELDSETS ATUALIZADOS) ---
    fieldsets = (
        ('🚨 APROVAÇÃO & STATUS', {
            'fields': ('status', 'motivo_reprovacao', 'observacao_admin'),
            'classes': ('extrapretty',),
        }),
        ('👤 DADOS PESSOAIS & DOCUMENTOS', {
            'fields': (
                ('nome_completo', 'data_nascimento'),
                ('cpf', 'rg'),
                ('whatsapp', 'instagram', 'editar_login'),
                ('nacionalidade', 'is_pcd', 'descricao_pcd')
            ),
        }),
        ('📍 ENDEREÇO', {
            'fields': ('cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado'),
            'classes': ('collapse',),
        }),
        ('📏 CARACTERÍSTICAS FÍSICAS', {
            'fields': (
                ('altura', 'peso'),
                ('manequim', 'calcado', 'tamanho_camiseta'),
                ('genero', 'etnia'),
                ('olhos', 'cabelo_tipo', 'cabelo_comprimento')
            ),
        }),
        ('💼 PROFISSIONAL & IDIOMAS', {
            'fields': (
                'experiencia', 
                'disponibilidade', 
                'areas_atuacao',
                ('nivel_ingles', 'nivel_espanhol', 'nivel_frances', 'outros_idiomas')
            ),
        }),
        ('💰 DADOS BANCÁRIOS', {
            'fields': ('banco', 'tipo_conta', 'agencia', 'conta', 'tipo_chave_pix', 'chave_pix'),
            'classes': ('collapse',),
        }),
        ('📸 FOTOS & TERMOS', {
            'fields': (
                ('preview_rosto', 'foto_rosto'), 
                ('preview_corpo', 'foto_corpo'),
                ('termo_uso_imagem', 'termo_comunicacao')
            ),
        }),
    )

    # --- VISUAIS ---
    def preview_rosto(self, obj):
        return format_html('<img src="{}" style="height:150px; border-radius:10px;" />', obj.foto_rosto.url) if obj.foto_rosto else "-"
    preview_rosto.short_description = "Rosto"

    def preview_corpo(self, obj):
        return format_html('<img src="{}" style="height:150px; border-radius:10px;" />', obj.foto_corpo.url) if obj.foto_corpo else "-"
    preview_corpo.short_description = "Corpo"

    def status_visual(self, obj):
        cor = {'aprovado':'#28a745', 'reprovado':'#dc3545', 'pendente':'#ffc107'}.get(obj.status, '#6c757d')
        icon = {'aprovado':'check_circle', 'reprovado':'cancel', 'pendente':'hourglass_empty'}.get(obj.status, '')
        return format_html(f'<span style="color:{cor}; font-weight:bold; display:flex; align-items:center; gap:5px;"><i class="material-icons" style="font-size:16px;">{icon}</i> {obj.get_status_display()}</span>')
    status_visual.short_description = "Status"

    def acoes_rapidas(self, obj):
        if not obj.uuid: return "-"
        # Ajuste o link conforme sua URL real
        return format_html(f'<a href="/admin/core/userprofile/{obj.id}/change/" class="btn btn-sm btn-info" style="color:#009688; font-weight:bold;">🔍 Analisar</a>')
    acoes_rapidas.short_description = "Ação"

    def editar_login(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html(f'<a href="{url}" target="_blank" style="color:#009688;">🖊️ Alterar E-mail/Senha</a>')
    editar_login.short_description = "Conta"

# ==============================================================================
# 3. VAGAS E CANDIDATURAS
# ==============================================================================
@admin.register(Job)
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

@admin.register(Candidatura)
class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('job', 'modelo', 'status_visual')
    list_filter = ('status', 'job')
    
    def status_visual(self, obj):
        cor = {'aprovado':'green', 'reprovado':'red', 'pendente':'orange'}.get(obj.status, 'black')
        return format_html(f'<b style="color:{cor}">{obj.get_status_display()}</b>')
    status_visual.short_description = "Situação"

admin.site.register(JobDia)
admin.site.register(Pergunta)
admin.site.register(Resposta)
admin.site.register(Avaliacao)