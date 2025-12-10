from django.urls import path
from . import views

urlpatterns = [
    # Página Inicial (Mural)
    path('', views.lista_vagas, name='lista_vagas'),
    
    # Detalhes da Vaga (ex: /vaga/1/)
    path('vaga/<int:job_id>/', views.detalhe_vaga, name='detalhe_vaga'),
    
    # Ação de Candidatar (ex: /vaga/1/aplicar/)
    path('vaga/<int:job_id>/aplicar/', views.candidatar_vaga, name='candidatar_vaga'),
    
    # Página de Cadastro
    path('cadastro/', views.cadastro, name='cadastro'),
]