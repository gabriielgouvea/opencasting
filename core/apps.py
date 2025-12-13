from django.apps import AppConfig
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    # Essa linha é a MÁGICA que conserta o erro no PythonAnywhere
    # Ela diz: "O caminho real deste app é EXATAMENTE onde este arquivo está"
    path = os.path.dirname(os.path.abspath(__file__))