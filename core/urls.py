from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- ROTAS PRINCIPAIS ---
    path('', views.home, name='home'),
    path('dashboard/', views.lista_vagas, name='lista_vagas'),
    
    # --- VAGAS ---
    path('vaga/<int:job_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    path('vaga/<int:job_id>/aplicar/', views.candidatar_vaga, name='candidatar_vaga'),
    
    # --- USUÁRIO ---
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- PÚBLICO (LINKS EXTERNOS) ---
    path('p/<uuid:uuid>/', views.perfil_publico, name='perfil_publico'),
    path('avaliar/<uuid:uuid>/', views.avaliar_promotor, name='avaliar_promotor'),

    # --- REDEFINIÇÃO DE SENHA (ESQUECI A SENHA) ---
    # 1. Tela para digitar o e-mail
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    
    # 2. Tela de aviso "E-mail enviado"
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    
    # 3. Link que chega no e-mail para digitar a nova senha
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    
    # 4. Tela de sucesso "Senha alterada"
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]