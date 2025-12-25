import re
from django.core.exceptions import ValidationError


class ComplexityPasswordValidator:
    """Exige senha com complexidade mínima.

    Regras:
    - mínimo de 8 caracteres
    - pelo menos 1 letra minúscula
    - pelo menos 1 letra maiúscula
    - pelo menos 1 número
    - pelo menos 1 símbolo
    """

    def validate(self, password, user=None):
        errors = []

        if len(password or "") < 8:
            errors.append("A senha deve ter pelo menos 8 caracteres.")

        if not re.search(r"[a-z]", password or ""):
            errors.append("Inclua pelo menos 1 letra minúscula.")

        if not re.search(r"[A-Z]", password or ""):
            errors.append("Inclua pelo menos 1 letra maiúscula.")

        if not re.search(r"\d", password or ""):
            errors.append("Inclua pelo menos 1 número.")

        if not re.search(r"[^A-Za-z0-9]", password or ""):
            errors.append("Inclua pelo menos 1 símbolo (ex: ! @ # $).")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "Use no mínimo 8 caracteres, com letra maiúscula e minúscula, "
            "número e símbolo."
        )
