from django import template
import re

register = template.Library()

@register.filter(name='phone_digits')
def phone_digits(value):
    """
    Remove qualquer caractere que não seja número (parênteses, espaços, traços).
    Exemplo: '(11) 98888-7777' vira '11988887777'
    """
    if not value:
        return ""
    return re.sub(r'\D', '', str(value))