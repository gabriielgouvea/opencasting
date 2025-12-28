from .models import ConfiguracaoSite

def site_config(request):
    # Disponibiliza a configuração do site para todos os templates (HTML)
    config = ConfiguracaoSite.load()
    contatos_qs = getattr(config, 'contatos', None)
    contatos = list(contatos_qs.all()) if contatos_qs is not None else []

    contatos_por_tipo = {
        'email': [],
        'telefone': [],
        'instagram': [],
        'facebook': [],
    }
    for c in contatos:
        if c.tipo in contatos_por_tipo:
            contatos_por_tipo[c.tipo].append(c)

    # Atalhos comuns para hero/footer
    email_principal = contatos_por_tipo['email'][0] if contatos_por_tipo['email'] else None
    whatsapp_principal = None
    for c in contatos_por_tipo['telefone']:
        if (c.telefone_tipo or '').strip() in {'whatsapp', 'ambos'}:
            whatsapp_principal = c
            break

    return {
        'config_site': config,
        'contatos_site': contatos,
        'contatos_por_tipo': contatos_por_tipo,
        'contato_email_principal': email_principal,
        'contato_whatsapp_principal': whatsapp_principal,
    }