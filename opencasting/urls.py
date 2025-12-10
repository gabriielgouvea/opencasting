from django.contrib import admin
from django.urls import path, include # <--- Adicione o include aqui

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <--- Isso conecta seu app ao site principal
]