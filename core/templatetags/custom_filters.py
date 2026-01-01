"""
CASTING CERTO - FILTROS PERSONALIZADOS PARA TEMPLATES
------------------------------------------------------------------
Este arquivo define funções utilitárias que podem ser chamadas 
diretamente nos arquivos HTML do Django.
Desenvolvido para: Gabriel Gouvêa
"""

from django import template
import re
from decimal import Decimal, InvalidOperation

# Inicializa o registro de filtros do Django
register = template.Library()

@register.filter(name='phone_digits')
def phone_digits(value):
    """
    FILTRO: phone_digits
    --------------------
    Finalidade: Sanitização de números de telefone.
    Lógica: Utiliza Expressões Regulares (Regex) para remover qualquer 
    caractere não numérico, transformando formatos como 
    '(11) 98888-7777' em '11988887777'.
    
    Uso no Template: {{ objeto.whatsapp|phone_digits }}
    Essencial para: Construção de links wa.me/55...
    """
    
    # Validação de segurança: Retorna vazio se o valor não existir
    if value is None or value == "":
        return ""
    
    # Converte para string e remove parênteses, espaços e hifens
    # \D representa qualquer caractere que NÃO seja um dígito (0-9)
    cleaned_value = re.sub(r'\D', '', str(value))
    
    return cleaned_value

@register.filter(name='truncate_uuid')
def truncate_uuid(value):
    """
    FILTRO AUXILIAR: truncate_uuid
    ------------------------------
    Reduz o tamanho visual do UUID para não quebrar o layout da tabela.
    Exemplo: '550e8400-e29b-41d4...' vira '550e8400...'
    """
    if not value:
        return "---"
    str_val = str(value)
    return f"{str_val[:8]}..."


@register.filter(name='brl')
def brl(value):
    """Formata número/Decimal como moeda BRL: 'R$ 1.234,56' (remove ',00')."""
    if value is None or value == "":
        return "R$ 0"

    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return f"R$ {value}"

    # normaliza para 2 casas
    dec = dec.quantize(Decimal('0.01'))
    s = f"{dec:.2f}"
    inteiro, frac = s.split('.')

    # separador de milhar
    inteiro_rev = inteiro[::-1]
    grupos = [inteiro_rev[i:i+3] for i in range(0, len(inteiro_rev), 3)]
    inteiro_fmt = '.'.join(g[::-1] for g in grupos[::-1])

    if frac == '00':
        return f"R$ {inteiro_fmt}"
    return f"R$ {inteiro_fmt},{frac}"


def _format_br_number(dec: Decimal, always_two: bool) -> str:
    dec = dec.quantize(Decimal('0.01'))
    s = f"{dec:.2f}"
    inteiro, frac = s.split('.')

    inteiro_rev = inteiro[::-1]
    grupos = [inteiro_rev[i:i+3] for i in range(0, len(inteiro_rev), 3)]
    inteiro_fmt = '.'.join(g[::-1] for g in grupos[::-1])

    if not always_two and frac == '00':
        return inteiro_fmt
    return f"{inteiro_fmt},{frac}"


@register.filter(name='br_num')
def br_num(value):
    """Formata número como pt-BR (ex: 6200.00 -> 6.200,00). Sempre 2 casas."""
    if value is None or value == "":
        return "0,00"
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    return _format_br_number(dec, always_two=True)


@register.filter(name='brl_compacto')
def brl_compacto(value):
    """Moeda estilo Canva: 'R$350,00' (sem espaço, sempre 2 casas)."""
    if value is None or value == "":
        return "R$0,00"
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return f"R${value}"
    return f"R${_format_br_number(dec, always_two=True)}"

# FIM DO ARQUIVO CUSTOM_FILTERS.PY - CASTING CERTO