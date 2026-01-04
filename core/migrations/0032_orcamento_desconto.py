from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_orcamento_data_evento'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='desconto_percentual',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Informe um desconto em R$ ou em %, não os dois.',
                max_digits=6,
                verbose_name='Desconto (%)',
            ),
        ),
        migrations.AddField(
            model_name='orcamento',
            name='desconto_valor',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
                verbose_name='Desconto (R$)',
            ),
        ),
    ]
