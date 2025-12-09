from django.contrib import admin
from .models import UserProfile, Job, JobDia, Candidatura

# --- Configuração para mostrar os Dias DENTRO do Job ---
class JobDiaInline(admin.TabularInline):
    model = JobDia
    extra = 1

class JobAdmin(admin.ModelAdmin):
    inlines = [JobDiaInline] 
    list_display = ('titulo', 'local', 'status', 'criado_em')
    list_filter = ('status',)

class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'job', 'status', 'data_candidatura')
    list_filter = ('status', 'job')

admin.site.register(UserProfile)
admin.site.register(Job, JobAdmin)
admin.site.register(Candidatura, CandidaturaAdmin)