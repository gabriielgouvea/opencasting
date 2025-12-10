from django.contrib import admin
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta

class JobDiaInline(admin.TabularInline):
    model = JobDia
    extra = 1

class JobAdmin(admin.ModelAdmin):
    inlines = [JobDiaInline]
    list_display = ('titulo', 'local', 'status', 'criado_em')

# Mostra as respostas das modelos dentro do perfil delas
class RespostaInline(admin.TabularInline):
    model = Resposta
    extra = 0
    readonly_fields = ('pergunta', 'texto_resposta')
    can_delete = False

class UserProfileAdmin(admin.ModelAdmin):
    inlines = [RespostaInline]
    list_display = ('nome_completo', 'whatsapp', 'altura')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Candidatura)
admin.site.register(Pergunta) # <-- Aqui ela cria as perguntas