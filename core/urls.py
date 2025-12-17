from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    # --- ADMINISTRAÇÃO ---
    path('admin/', admin.site.urls),

    # --- AUTENTICAÇÃO (Login / Logout) ---
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # --- RECUPERAÇÃO DE SENHA (Padrão Django) ---
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    # --- INSTITUCIONAL (SITE) ---
    path('', views.home, name='home'),
    path('quem-somos/', views.quem_somos, name='quem_somos'),  # <--- NOVA ROTA PARA A PÁGINA

    # --- ÁREA DO CANDIDATO (Logado) ---
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('vagas/', views.lista_vagas, name='lista_vagas'),
    path('vagas/<int:job_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    path('vagas/<int:job_id>/candidatar/', views.candidatar_vaga, name='candidatar_vaga'),

    # --- PERFIL PÚBLICO E AVALIAÇÃO ---
    path('p/<uuid:uuid>/', views.perfil_publico, name='perfil_publico'),
    path('p/<uuid:uuid>/avaliar/', views.avaliar_promotor, name='avaliar_promotor'),
]

# --- SERVIR ARQUIVOS DE MÍDIA (FOTOS) NO MODO DEBUG ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)