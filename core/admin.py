from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta

# --- AÇÕES RÁPIDAS (BOTÕES DE UM CLIQUE) ---
@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos(modeladmin, request, queryset):
    queryset.update(status='aprovado')

@admin.action(description='❌ Reprovar Selecionados')
def reprovar_modelos(modeladmin, request, queryset):
    queryset.update(status='reprovado')

# --- CONFIGURAÇÃO ---

class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    readonly_fields = ('pergunta', 'texto_resposta')
    can_delete = False
    verbose_name = "Resposta Adicional"
    verbose_name_plural = "Respostas do Questionário"

class UserProfileAdmin(admin.ModelAdmin):
    inlines = [RespostaInline]
    
    # Colunas da Tabela
    list_display = ('nome_completo', 'whatsapp', 'status_visual', 'ver_foto', 'altura')
    list_filter = ('status', 'estado', 'manequim')
    search_fields = ('nome_completo', 'email', 'whatsapp')
    
    # Adiciona os botões de ação em massa
    actions = [aprovar_modelos, reprovar_modelos]

    # Organização Visual (SEM COLLAPSE - TUDO ABERTO)
    fieldsets = (
        ('🚨 ÁREA DE DECISÃO (STATUS)', {
            'fields': ('status', 'motivo_reprovacao', 'observacao_admin'),
            # Removi o 'classes': ('collapse',) -> Agora fica sempre visível!
            'description': 'Defina aqui se o candidato pode ou não ver as vagas.'
        }),
        ('👤 Dados Pessoais', {
            'fields': ('user', 'nome_completo', 'whatsapp', 'data_nascimento')
        }),
        ('📍 Localização', {
            'fields': ('cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado')
        }),
        ('📏 Medidas', {
            'fields': ('altura', 'manequim', 'calcado')
        }),
        ('📸 Fotos', {
            'fields': ('foto_rosto', 'foto_corpo')
        }),
    )

    # Bolinha colorida na lista
    def status_visual(self, obj):
        cores = {'aprovado': 'green', 'reprovado': 'red', 'pendente': 'orange'}
        cor = cores.get(obj.status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px 10px; border-radius: 15px; font-weight: bold;">{}</span>',
            cor, obj.get_status_display()
        )
    status_visual.short_description = 'Status Atual'

    # Miniatura da foto na lista
    def ver_foto(self, obj):
        if obj.foto_rosto:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%;" />', obj.foto_rosto.url)
        return "Sem foto"
    ver_foto.short_description = 'Foto'

# Jobs
class JobDiaInline(admin.TabularInline):
    model = JobDia
    extra = 1

class JobAdmin(admin.ModelAdmin):
    inlines = [JobDiaInline]
    list_display = ('titulo', 'local', 'status_badge', 'criado_em')
    list_filter = ('status',)

    def status_badge(self, obj):
        cor = 'green' if obj.status == 'aberto' else 'gray'
        return format_html('<span style="color: {};">●</span> {}', cor, obj.get_status_display())
    status_badge.short_description = 'Status'

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Candidatura)
admin.site.register(Pergunta)