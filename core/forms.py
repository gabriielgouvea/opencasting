from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from datetime import datetime

class CadastroForm(forms.ModelForm):
    # ==========================================================================
    # 1. DADOS DE LOGIN
    # ==========================================================================
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
    
    # ==========================================================================
    # 2. DADOS PESSOAIS & DOCUMENTOS
    # ==========================================================================
    nome_completo = forms.CharField(
        label="Nome Completo", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome artístico ou civil'})
    )
    
    cpf = forms.CharField(
        label="CPF", 
        widget=forms.TextInput(attrs={'class': 'form-control cpf-mask', 'placeholder': '000.000.000-00'})
    )
    rg = forms.CharField(
        label="RG / RNE", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do RG'})
    )

    whatsapp = forms.CharField(
        label="WhatsApp", 
        widget=forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '(11) 99999-9999'})
    )
    instagram = forms.CharField(
        label="Instagram", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@seu.perfil'})
    )
    data_nascimento = forms.CharField(
        label="Data de Nascimento", 
        widget=forms.TextInput(attrs={'class': 'form-control date-mask', 'placeholder': 'DD/MM/AAAA', 'inputmode': 'numeric'})
    )

    # [CORREÇÃO] Adicionado opção vazia no início para forçar o usuário a escolher
    genero = forms.ChoiceField(
        label="Gênero", 
        choices=[('', 'Selecione...')] + UserProfile.GENERO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    etnia = forms.ChoiceField(
        label="Cor / Etnia", 
        choices=[('', 'Selecione...')] + UserProfile.ETNIA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nacionalidade = forms.ChoiceField(
        label="Nacionalidade", 
        choices=[('', 'Selecione...')] + UserProfile.NACIONALIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_pcd = forms.BooleanField(
        label="Sou PCD (Pessoa com Deficiência)", required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    descricao_pcd = forms.CharField(
        label="Qual deficiência?", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descreva brevemente'})
    )

    # ==========================================================================
    # 3. ENDEREÇO
    # ==========================================================================
    cep = forms.CharField(
        label="CEP", 
        widget=forms.TextInput(attrs={'class': 'form-control cep-mask', 'placeholder': '00000-000', 'onblur': 'buscarCep(this.value)'})
    )
    endereco = forms.CharField(label="Endereço", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_endereco'}))
    numero = forms.CharField(label="Número", widget=forms.TextInput(attrs={'class': 'form-control'}))
    bairro = forms.CharField(label="Bairro", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_bairro'}))
    cidade = forms.CharField(label="Cidade", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cidade'}))
    estado = forms.CharField(label="Estado", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_estado'}))

    # ==========================================================================
    # 4. CARACTERÍSTICAS FÍSICAS
    # ==========================================================================
    altura = forms.CharField(
        label="Altura", 
        widget=forms.TextInput(attrs={'class': 'form-control height-mask', 'placeholder': 'Ex: 1.70', 'inputmode': 'numeric'})
    )
    # Adicionada classe 'weight-mask'
    peso = forms.CharField(
        label="Peso (kg)", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control weight-mask', 'placeholder': 'Ex: 65.00', 'inputmode': 'numeric'})
    )
    manequim = forms.CharField(label="Manequim", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 38'}))
    
    tamanho_camiseta = forms.ChoiceField(
        label="Tamanho de Camiseta", 
        choices=[('', 'Selecione...')] + UserProfile.TAMANHO_CAMISETA, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    calcado = forms.CharField(label="Calçado", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 37'}))

    olhos = forms.ChoiceField(
        label="Cor dos Olhos", 
        choices=[('', 'Selecione...')] + UserProfile.OLHOS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cabelo_tipo = forms.ChoiceField(
        label="Tipo de Cabelo", 
        choices=[('', 'Selecione...')] + UserProfile.CABELO_TIPO_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cabelo_comprimento = forms.ChoiceField(
        label="Comprimento", 
        choices=[('', 'Selecione...')] + UserProfile.CABELO_TAM_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # ==========================================================================
    # 5. PROFISSIONAL & IDIOMAS
    # ==========================================================================
    experiencia = forms.ChoiceField(
        label="Experiência", 
        choices=[('', 'Selecione...')] + UserProfile.EXPERIENCIA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    disponibilidade = forms.ChoiceField(
        label="Disponibilidade", 
        choices=[('', 'Selecione...')] + UserProfile.DISPONIBILIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    nivel_ingles = forms.ChoiceField(
        label="Inglês", 
        choices=[('', 'Selecione o nível...')] + UserProfile.NIVEL_IDIOMA, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nivel_espanhol = forms.ChoiceField(
        label="Espanhol", 
        choices=[('', 'Selecione o nível...')] + UserProfile.NIVEL_IDIOMA, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nivel_frances = forms.ChoiceField(
        label="Francês", 
        choices=[('', 'Selecione o nível...')] + UserProfile.NIVEL_IDIOMA, required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    outros_idiomas = forms.CharField(
        label="Outros Idiomas", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Japonês Fluente'})
    )

    AREAS_OPCOES = [
        ('recepcao', 'Recepção'),
        ('degustacao', 'Degustação'),
        ('bartender', 'Bartender'),
        ('garcom', 'Garçom/Garçonete'),
        ('modelo', 'Modelo'),
        ('seguranca', 'Segurança'),
        ('mascote', 'Mascote'),
        ('controle_acesso', 'Controle de Acesso'),
        ('limpeza', 'Limpeza'),
        ('dj', 'DJ'),
        ('fotografo', 'Fotógrafo'),
        ('apresentador', 'Apresentador/Locutor'),
        ('outros', 'Outros (Descrever abaixo)'),
    ]
    areas_interesse = forms.MultipleChoiceField(
        label="Áreas de Interesse",
        choices=AREAS_OPCOES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input-custom'})
    )
    
    areas_outros_texto = forms.CharField(
        label="Quais outras áreas?", required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descreva...'})
    )

    # ==========================================================================
    # 6. DADOS BANCÁRIOS
    # ==========================================================================
    banco = forms.CharField(required=False, label="Banco", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Nubank, Itaú'}))
    
    tipo_conta = forms.ChoiceField(
        required=False, label="Tipo de Conta",
        choices=[('', 'Selecione...')] + UserProfile.TIPO_CONTA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    agencia = forms.CharField(required=False, label="Agência", widget=forms.TextInput(attrs={'class': 'form-control'}))
    conta = forms.CharField(required=False, label="Conta com Dígito", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    tipo_chave_pix = forms.ChoiceField(
        required=False, label="Tipo de Chave",
        choices=[('', 'Selecione...')] + UserProfile.TIPO_CHAVE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    chave_pix = forms.CharField(required=False, label="Chave PIX", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua chave'}))

    # ==========================================================================
    # 7. FOTOS & TERMOS
    # ==========================================================================
    foto_rosto = forms.ImageField(label="Foto de Rosto", required=False, widget=forms.FileInput(attrs={'id': 'input_foto_rosto', 'style': 'display:none;'}))
    foto_corpo = forms.ImageField(label="Foto de Corpo", required=False, widget=forms.FileInput(attrs={'id': 'input_foto_corpo', 'style': 'display:none;'}))

    termo_uso_imagem = forms.BooleanField(
        required=True, label="Autorizo o uso da minha imagem para divulgação."
    )
    termo_comunicacao = forms.BooleanField(
        required=True, label="Autorizo o contato via WhatsApp/E-mail."
    )

    class Meta:
        model = UserProfile
        fields = [
            'nome_completo', 'cpf', 'rg', 'whatsapp', 'instagram', 'data_nascimento',
            'genero', 'etnia', 'nacionalidade', 'is_pcd', 'descricao_pcd',
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado',
            'altura', 'peso', 'manequim', 'tamanho_camiseta', 'calcado',
            'olhos', 'cabelo_tipo', 'cabelo_comprimento',
            'experiencia', 'disponibilidade', 'areas_atuacao',
            'nivel_ingles', 'nivel_espanhol', 'nivel_frances', 'outros_idiomas',
            'banco', 'tipo_conta', 'agencia', 'conta', 'tipo_chave_pix', 'chave_pix',
            'foto_rosto', 'foto_corpo',
            'termo_uso_imagem', 'termo_comunicacao'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("As senhas não conferem.")
        
        areas = cleaned_data.get('areas_interesse')
        outros = cleaned_data.get('areas_outros_texto')
        
        texto_final = ""
        if areas:
            texto_final = ", ".join(areas)
        
        if 'outros' in (areas or []) and outros:
            texto_final += f", Outros: {outros}"
            
        cleaned_data['areas_atuacao'] = texto_final
        self.instance.areas_atuacao = texto_final
        
        return cleaned_data

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

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso:
            return peso.replace(',', '.')
        return peso

    def clean_termo_uso_imagem(self):
        aceite = self.cleaned_data.get('termo_uso_imagem')
        if not aceite:
            raise forms.ValidationError("Necessário aceitar o termo de imagem.")
        return aceite

    def clean_termo_comunicacao(self):
        aceite = self.cleaned_data.get('termo_comunicacao')
        if not aceite:
            raise forms.ValidationError("Necessário aceitar o termo de comunicação.")
        return aceite