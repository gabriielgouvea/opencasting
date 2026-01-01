from django.db import migrations


def forwards(apps, schema_editor):
    ConfiguracaoSite = apps.get_model('core', 'ConfiguracaoSite')

    try:
        obj, _created = ConfiguracaoSite.objects.get_or_create(pk=1)
    except Exception:
        return

    changed = False

    titulo = (getattr(obj, 'titulo_site', '') or '').strip()
    if titulo in {'', 'OpenCasting', 'OPENCASTING'}:
        obj.titulo_site = 'Casting Certo'
        changed = True

    texto = getattr(obj, 'texto_quem_somos', None)
    if isinstance(texto, str) and 'OpenCasting' in texto:
        obj.texto_quem_somos = texto.replace('OpenCasting', 'Casting Certo')
        changed = True

    if changed:
        obj.save()


def backwards(apps, schema_editor):
    # Não revertido automaticamente
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_apresentacao'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
