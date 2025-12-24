from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_userprofile_bloqueado_ate'),
    ]

    operations = [
        migrations.CreateModel(
            name='CpfBanido',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cpf', models.CharField(max_length=14, unique=True, verbose_name='CPF (banido)')),
                ('motivo', models.CharField(blank=True, max_length=200, null=True, verbose_name='Motivo')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Banido em')),
            ],
            options={
                'verbose_name': 'CPF Banido',
                'verbose_name_plural': 'CPFs Banidos',
            },
        ),
    ]
