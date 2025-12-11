from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Capa (Landing Page)
    path('', views.home, name='home'),

    # Área de Vagas (Dashboard)
    path('vagas/', views.lista_vagas, name='lista_vagas'),
    path('vaga/<int:job_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    path('vaga/<int:job_id>/aplicar/', views.candidatar_vaga, name='candidatar_vaga'),
    
    # Cadastro e Perfil
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # Login e Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]