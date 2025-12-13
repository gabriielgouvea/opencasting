from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from datetime import datetime

class CadastroForm(forms.ModelForm):
    # --- 1. DADOS DE LOGIN ---
    email = forms.EmailField(
        label="E-mail", 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Seu melhor e-mail'})
    )
    password = forms.CharField(
        label="Senha", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha segura'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Senha", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a senha'})
    )
    
    # --- 2. DADOS PESSOAIS ---
    nome_completo = forms.CharField(
        label="Nome Completo", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome artístico ou civil'})
    )
    whatsapp = forms.CharField(
        label="WhatsApp", 
        widget=forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '(11) 99999-9999'})
    )
    # [NOVO CAMPO] Instagram
    instagram = forms.CharField(
        label="Instagram", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@seu.perfil'})
    )
    data_nascimento = forms.CharField(
        label="Data de Nascimento", 
        widget=forms.TextInput(attrs={'class': 'form-control date-mask', 'placeholder': 'DD/MM/AAAA', 'inputmode': 'numeric'})
    )
    
    # --- 3. ENDEREÇO ---
    cep = forms.CharField(
        label="CEP", 
        widget=forms.TextInput(attrs={'class': 'form-control cep-mask', 'placeholder': '00000-000', 'onblur': 'buscarCep(this.value)'})
    )
    endereco = forms.CharField(
        label="Endereço", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_endereco'})
    )
    numero = forms.CharField(
        label="Número", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bairro = forms.CharField(
        label="Bairro", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_bairro'})
    )
    cidade = forms.CharField(
        label="Cidade", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cidade'})
    )
    estado = forms.CharField(
        label="Estado", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_estado'})
    )

    # --- 4. MEDIDAS ---
    altura = forms.CharField(
        label="Altura", 
        widget=forms.TextInput(attrs={'class': 'form-control height-mask', 'placeholder': 'Ex: 1.70', 'inputmode': 'decimal'})
    )
    manequim = forms.CharField(
        label="Manequim", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 38', 'type': 'number'})
    )
    calcado = forms.CharField(
        label="Calçado", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 37', 'type': 'number'})
    )

    # --- 5. DADOS BANCÁRIOS ---
    cpf = forms.CharField(
        label="CPF", 
        widget=forms.TextInput(attrs={'class': 'form-control cpf-mask', 'placeholder': '000.000.000-00'})
    )
    
    banco = forms.CharField(
        required=False, 
        label="Banco", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Nubank, Itaú'})
    )
    
    tipo_conta = forms.ChoiceField(
        required=False, 
        label="Tipo de Conta",
        choices=[('', 'Selecione...'), ('corrente', 'Conta Corrente'), ('poupanca', 'Conta Poupança')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    agencia = forms.CharField(
        required=False, 
        label="Agência", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    conta = forms.CharField(
        required=False, 
        label="Conta com Dígito", 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    tipo_chave_pix = forms.ChoiceField(
        required=False, 
        label="Tipo de Chave",
        choices=[('', 'Selecione o tipo...'), ('cpf', 'CPF'), ('email', 'E-mail'), ('telefone', 'Telefone'), ('aleatoria', 'Chave Aleatória')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    chave_pix = forms.CharField(
        required=False, 
        label="Chave PIX", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua chave'})
    )

    # --- 6. FOTOS ---
    foto_rosto = forms.ImageField(
        label="Foto de Rosto",
        required=False, 
        widget=forms.FileInput(attrs={'id': 'input_foto_rosto', 'style': 'display:none;'})
    )
    
    foto_corpo = forms.ImageField(
        label="Foto de Corpo",
        required=False,
        widget=forms.FileInput(attrs={'id': 'input_foto_corpo', 'style': 'display:none;'})
    )

    # --- 7. TERMOS E CONDIÇÕES [NOVOS CAMPOS] ---
    termo_uso_imagem = forms.BooleanField(
        required=True, 
        label="Autorizo o uso da minha imagem em fotos e vídeos captados em eventos ou enviados por mim para divulgação em site e redes sociais da agência."
    )
    termo_comunicacao = forms.BooleanField(
        required=True, 
        label="Autorizo a agência a entrar em contato a qualquer momento via WhatsApp, E-mail ou Telefone para tratar de vagas, jobs ou assuntos administrativos."
    )

    class Meta:
        model = UserProfile
        # Lista com TODOS os campos que serão salvos no banco
        fields = [
            'nome_completo', 'whatsapp', 'instagram', 'data_nascimento', 
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado',
            'altura', 'manequim', 'calcado',
            'cpf', 'banco', 'tipo_conta', 'agencia', 'conta', 'tipo_chave_pix', 'chave_pix',
            'foto_rosto', 'foto_corpo',
            'termo_uso_imagem', 'termo_comunicacao'
        ]

    # --- MÉTODOS DE LIMPEZA E VALIDAÇÃO ---

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("As senhas não conferem.")
            
    def clean_data_nascimento(self):
        data = self.cleaned_data['data_nascimento']
        try:
            return datetime.strptime(data, '%d/%m/%Y').date()
        except ValueError:
            raise forms.ValidationError("Data inválida. Use o formato DD/MM/AAAA")
            
    def clean_altura(self):
        altura = self.cleaned_data['altura']
        if altura:
            return altura.replace(',', '.')
        return altura

    # [NOVAS VALIDAÇÕES] Garantir que o usuário marcou os termos
    def clean_termo_uso_imagem(self):
        aceite = self.cleaned_data.get('termo_uso_imagem')
        if not aceite:
            raise forms.ValidationError("Você precisa autorizar o uso de imagem para se cadastrar.")
        return aceite

    def clean_termo_comunicacao(self):
        aceite = self.cleaned_data.get('termo_comunicacao')
        if not aceite:
            raise forms.ValidationError("Você precisa autorizar a comunicação para se cadastrar.")
        return aceite