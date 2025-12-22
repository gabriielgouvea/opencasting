"""
OPENCASTING CRM - FILTROS PERSONALIZADOS PARA TEMPLATES
------------------------------------------------------------------
Este arquivo define funções utilitárias que podem ser chamadas 
diretamente nos arquivos HTML do Django.
Desenvolvido para: Gabriel Gouvêa
"""

from django import template
import re

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

# FIM DO ARQUIVO CUSTOM_FILTERS.PY - OPENCASTING CRM V3.0