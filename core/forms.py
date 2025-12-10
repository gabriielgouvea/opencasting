from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class CadastroForm(forms.ModelForm):
    # 1. LOGIN
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Seu melhor e-mail'}))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha segura'}))
    confirm_password = forms.CharField(label="Confirmar Senha", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a senha'}))
    
    # 2. PESSOAL
    nome_completo = forms.CharField(label="Nome Completo", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome artístico ou civil'}))
    whatsapp = forms.CharField(label="WhatsApp", widget=forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '(11) 99999-9999'}))
    data_nascimento = forms.CharField(label="Data de Nascimento", widget=forms.TextInput(attrs={'class': 'form-control date-mask', 'placeholder': 'DD/MM/AAAA', 'inputmode': 'numeric'}))
    
    # 3. ENDEREÇO (NOVO)
    cep = forms.CharField(label="CEP", widget=forms.TextInput(attrs={'class': 'form-control cep-mask', 'placeholder': '00000-000', 'onblur': 'buscarCep(this.value)'}))
    endereco = forms.CharField(label="Endereço", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'rua'}))
    numero = forms.CharField(label="Número", widget=forms.TextInput(attrs={'class': 'form-control'}))
    bairro = forms.CharField(label="Bairro", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'bairro'}))
    cidade = forms.CharField(label="Cidade", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'cidade'}))
    estado = forms.CharField(label="Estado", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'uf'}))

    # 4. MEDIDAS
    altura = forms.CharField(label="Altura", widget=forms.TextInput(attrs={'class': 'form-control height-mask', 'placeholder': 'Ex: 1.70', 'inputmode': 'decimal'}))
    manequim = forms.CharField(label="Manequim", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 38', 'type': 'number'}))
    calcado = forms.CharField(label="Calçado", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 37', 'type': 'number'}))

    class Meta:
        model = UserProfile
        # Incluir os campos novos na lista
        fields = ['nome_completo', 'whatsapp', 'data_nascimento', 
                  'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado',
                  'altura', 'manequim', 'calcado']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("As senhas não conferem.")
            
    def clean_data_nascimento(self):
        data = self.cleaned_data['data_nascimento']
        try:
            from datetime import datetime
            return datetime.strptime(data, '%d/%m/%Y').date()
        except ValueError:
            raise forms.ValidationError("Data inválida.")
            
    def clean_altura(self):
        return self.cleaned_data['altura'].replace(',', '.')