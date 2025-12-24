from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_userprofile_whatsapp'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='bloqueado_ate',
            field=models.DateField(blank=True, null=True, verbose_name='Bloqueado até'),
        ),
    ]
