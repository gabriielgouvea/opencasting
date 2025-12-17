from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from datetime import date
from .models import UserProfile, Job, JobDia, Candidatura, Pergunta, Resposta, Avaliacao, ConfiguracaoSite

admin.site.unregister(User)

# --- UTILS ---
def clean_number(val):
    if not val: return None
    try: return float(str(val).replace(',', '.'))
    except ValueError: return None

# --- FILTROS FANTASMAS (Ranges Manuais) ---
class GhostFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin): return []
    def queryset(self, request, queryset): return queryset

class IdadeMinFilter(GhostFilter): title='Idade Min'; parameter_name='idade_min'
class IdadeMaxFilter(GhostFilter): title='Idade Max'; parameter_name='idade_max'
class AlturaMinFilter(GhostFilter): title='Altura Min'; parameter_name='altura_min'
class AlturaMaxFilter(GhostFilter): title='Altura Max'; parameter_name='altura_max'
class ManequimMinFilter(GhostFilter): title='Manequim Min'; parameter_name='manequim_min'
class ManequimMaxFilter(GhostFilter): title='Manequim Max'; parameter_name='manequim_max'
class CalcadoMinFilter(GhostFilter): title='Calçado Min'; parameter_name='calcado_min'
class CalcadoMaxFilter(GhostFilter): title='Calçado Max'; parameter_name='calcado_max'
class CamisetaMinFilter(GhostFilter): title='Camiseta Min'; parameter_name='camiseta_min'
class CamisetaMaxFilter(GhostFilter): title='Camiseta Max'; parameter_name='camiseta_max'

class AreaAtuacaoFilter(admin.SimpleListFilter):
    title = 'Áreas de Atuação'
    parameter_name = 'area_atuacao'
    def lookups(self, request, model_admin):
        return [
            ('recepcao', 'Recepção'), ('modelo', 'Modelo'), ('bartender', 'Bartender'),
            ('garcom', 'Garçom'), ('eventos', 'Eventos'), ('limpeza', 'Limpeza'),
            ('seguranca', 'Segurança'), ('mascote', 'Mascote')
        ]
    def queryset(self, request, queryset):
        if self.value(): return queryset.filter(areas_atuacao__icontains=self.value())
        return queryset

# --- AÇÕES ---
@admin.action(description='✅ Aprovar Selecionados')
def aprovar_modelos(modeladmin, request, queryset):
    updated = queryset.update(status='aprovado')
    messages.success(request, f"{updated} perfis APROVADOS.")

@admin.action(description='❌ Reprovar Selecionados')
def reprovar_modelos(modeladmin, request, queryset):
    updated = queryset.update(status='reprovado', motivo_reprovacao='Massa')
    messages.warning(request, f"{updated} perfis REPROVADOS.")

@admin.action(description='🗑️ Excluir Selecionados')
def excluir_modelos(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    messages.info(request, f"{count} perfis excluídos.")

# --- ADMINS ---
@admin.register(User)
class EquipeAdmin(BaseUserAdmin):
    list_display = ('nome_visual', 'email', 'is_staff', 'last_login')
    def nome_visual(self, obj): return obj.get_full_name() or obj.username

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list.html"
    class Media:
        css = { 'all': ('css/admin_custom.css',) }
        js = ('js/admin_custom.js',)

    list_display = ('nome_completo', 'whatsapp_link', 'idade_visual', 'altura_visual', 'status_visual', 'acoes_rapidas')
    
    # LISTA COMPLETA DE FILTROS (Dropdows + Ranges)
    list_filter = (
        'status', 
        'genero', 
        'is_pcd', 
        'etnia',
        'nacionalidade',
        'cabelo_tipo', 
        'cabelo_comprimento',
        'olhos',
        'experiencia',
        'disponibilidade',
        'nivel_ingles', 
        'nivel_espanhol', 
        'nivel_frances',
        AreaAtuacaoFilter,
        IdadeMinFilter, IdadeMaxFilter, 
        AlturaMinFilter, AlturaMaxFilter, 
        ManequimMinFilter, ManequimMaxFilter, 
        CalcadoMinFilter, CalcadoMaxFilter, 
        CamisetaMinFilter, CamisetaMaxFilter
    )
    
    search_fields = ('nome_completo', 'cpf', 'user__email', 'whatsapp', 'areas_atuacao', 'instagram')
    actions = [aprovar_modelos, reprovar_modelos, excluir_modelos]
    readonly_fields = ('painel_acoes', 'preview_rosto', 'preview_corpo')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/aprovar/', self.admin_site.admin_view(self.aprovar_view), name='userprofile_aprovar'),
            path('<int:object_id>/reprovar/', self.admin_site.admin_view(self.reprovar_view), name='userprofile_reprovar'),
            path('<int:object_id>/enviar-senha/', self.admin_site.admin_view(self.enviar_senha_view), name='userprofile_enviar_senha'),
        ]
        return custom_urls + urls

    def aprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        p.status = 'aprovado'; p.save()
        messages.success(request, "Aprovado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def reprovar_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        p.status = 'reprovado'; p.motivo_reprovacao = request.GET.get('motivo',''); p.save()
        messages.warning(request, "Reprovado!")
        return redirect(request.META.get('HTTP_REFERER', '..'))
        
    def enviar_senha_view(self, request, object_id):
        p = get_object_or_404(UserProfile, pk=object_id)
        if p.user.email:
            try:
                form = PasswordResetForm({'email': p.user.email})
                if form.is_valid(): form.save(request=request); messages.success(request, "Enviado!")
            except: messages.error(request, "Erro.")
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def painel_acoes(self, obj):
        html = '<div class="profile-action-panel">'
        if obj.status == 'pendente':
            url = reverse('admin:userprofile_aprovar', args=[obj.pk])
            html += f'<div class="status-badge status-pending">PENDENTE</div>'
            html += f'<a class="btn-action btn-approve" href="{url}"><i class="fas fa-check"></i> APROVAR</a>'
            html += f'<button type="button" class="btn-action btn-reject" onclick="abrirModalReprovacao({obj.pk})"><i class="fas fa-times"></i> REPROVAR</button>'
        elif obj.status == 'aprovado':
            url = reverse('admin:userprofile_enviar_senha', args=[obj.pk])
            clean = ''.join(filter(str.isdigit, obj.whatsapp or ''))
            html += f'<div class="status-badge status-approved">APROVADO</div>'
            html += f'<a class="btn-action btn-whatsapp" href="https://wa.me/{clean}" target="_blank">WHATSAPP</a>'
            html += f'<a class="btn-action btn-email" href="mailto:{obj.user.email}">EMAIL</a>'
            html += f'<a class="btn-action btn-password" href="{url}">SENHA</a>'
        elif obj.status == 'reprovado':
            url = reverse('admin:userprofile_aprovar', args=[obj.pk])
            html += f'<div class="status-badge status-rejected">REPROVADO</div>'
            html += f'<a class="btn-action btn-reconsider" href="{url}">RECONSIDERAR</a>'
        html += '</div>'
        return format_html(html)
    painel_acoes.short_description = "Ações"

    fieldsets = (
        ('GESTOR', {'fields': ('painel_acoes',), 'classes': ('extrapretty',)}),
        ('DADOS', {'fields': (('nome_completo','data_nascimento'), ('cpf','rg'), ('nacionalidade','is_pcd','descricao_pcd'))}),
        ('CONTATO', {'fields': (('whatsapp','instagram'),)}),
        ('FÍSICO', {'fields': (('altura','peso'), ('manequim','calcado','tamanho_camiseta'), ('olhos','cabelo_tipo','cabelo_comprimento'), 'etnia')}),
        ('PROFISSIONAL', {'fields': ('experiencia', 'areas_atuacao', 'disponibilidade', ('nivel_ingles','nivel_espanhol','nivel_frances'))}),
        ('FOTOS', {'fields': (('preview_rosto','foto_rosto'), ('preview_corpo','foto_corpo'))}),
        ('SYSTEM', {'fields': ('status','motivo_reprovacao'), 'classes': ('collapse',)})
    )
    
    def whatsapp_link(self, obj): return obj.whatsapp
    def status_visual(self, obj): return obj.get_status_display()
    def idade_visual(self, obj):
        if obj.data_nascimento: return f"{date.today().year - obj.data_nascimento.year} anos"
        return "-"
    def altura_visual(self, obj): return f"{obj.altura}m" if obj.altura else "-"
    def acoes_rapidas(self, obj): return format_html(f'<a href="/admin/core/userprofile/{obj.id}/change/" class="btn btn-sm btn-info" style="border-radius:20px;">🔍 Abrir</a>')
    
    def preview_rosto(self, obj): return format_html('<img src="{}" style="height:100px; border-radius:5px;" />', obj.foto_rosto.url) if obj.foto_rosto else "-"
    def preview_corpo(self, obj): return format_html('<img src="{}" style="height:100px; border-radius:5px;" />', obj.foto_corpo.url) if obj.foto_corpo else "-"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        p = request.GET
        if p.get('idade_min'): qs = qs.filter(data_nascimento__lte=date.today().replace(year=date.today().year - int(p.get('idade_min'))))
        if p.get('idade_max'): qs = qs.filter(data_nascimento__gt=date.today().replace(year=date.today().year - int(p.get('idade_max')) - 1))
        n = lambda k: clean_number(p.get(k))
        if n('altura_min'): qs = qs.filter(altura__gte=n('altura_min'))
        if n('altura_max'): qs = qs.filter(altura__lte=n('altura_max'))
        if p.get('manequim_min'): qs = qs.filter(manequim__gte=p.get('manequim_min'))
        if p.get('manequim_max'): qs = qs.filter(manequim__lte=p.get('manequim_max'))
        if p.get('calcado_min'): qs = qs.filter(calcado__gte=p.get('calcado_min'))
        if p.get('calcado_max'): qs = qs.filter(calcado__lte=p.get('calcado_max'))
        SZ = {'PP':0,'P':1,'M':2,'G':3,'GG':4,'XG':5}
        cmin, cmax = p.get('camiseta_min'), p.get('camiseta_max')
        if cmin or cmax:
            valid = [k for k,v in SZ.items() if v >= SZ.get(cmin,0) and v <= SZ.get(cmax,5)]
            qs = qs.filter(tamanho_camiseta__in=valid)
        return qs

admin.site.register(Job)
admin.site.register(Candidatura)
admin.site.register(JobDia)
admin.site.register(Pergunta)
admin.site.register(Resposta)
admin.site.register(Avaliacao)
admin.site.register(ConfiguracaoSite)