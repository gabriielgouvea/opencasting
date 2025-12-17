from .models import ConfiguracaoSite

def site_config(request):
    # Disponibiliza a configuração do site para todos os templates (HTML)
    return {
        'config_site': ConfiguracaoSite.load()
    }