from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 1. ADMINISTRAÇÃO E HOME
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    
    # 2. FLUXO DE VAGAS (JOBS)
    path('vagas/', views.lista_vagas, name='lista_vagas'),
    path('vagas/<int:job_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    path('vagas/<int:job_id>/candidatar/', views.candidatar_vaga, name='candidatar_vaga'),
    
    # 3. GESTÃO DE PERFIL E CADASTRO
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<uuid:uuid>/', views.perfil_publico, name='perfil_publico'),
    
    # 4. AVALIAÇÃO EXTERNA (CRM)
    path('avaliar/<uuid:uuid>/', views.avaliar_promotor, name='avaliar_promotor'),

    # 4.1 APRESENTAÇÃO PÚBLICA (LINK)
    path('apresentacao/<uuid:uuid>/', views.apresentacao_publica, name='apresentacao_publica'),
    
    # 5. AUTENTICAÇÃO (LOGIN/LOGOUT)
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # 6. REDEFINIÇÃO DE SENHA (CORREÇÃO DO ERRO)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    
    # (Rotas institucionais removidas)
]

# CONFIGURAÇÃO PARA ARQUIVOS DE MÍDIA (FOTOS)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)