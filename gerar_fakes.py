import os
import django
import random
from decimal import Decimal
from faker import Faker

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opencasting.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Pergunta, Resposta

# Inicializa o Faker em português
fake = Faker('pt_BR')

def criar_perguntas_padrao():
    """Garante que existam perguntas no banco para serem respondidas"""
    if Pergunta.objects.count() == 0:
        print("⚠️ Nenhuma pergunta encontrada. Criando perguntas padrão...")
        Pergunta.objects.create(texto="Possui veículo próprio?", tipo="sim_nao")
        Pergunta.objects.create(texto="Tem disponibilidade para viagens?", tipo="sim_nao")
        Pergunta.objects.create(texto="Possui tatuagens visíveis?", tipo="sim_nao")
        Pergunta.objects.create(texto="Qual seu tamanho de calça?", tipo="texto")

def gerar_dados():
    print("🚀 Iniciando a criação de 50 promotores fake COMPLETO...")
    
    # Garante que temos perguntas para responder
    criar_perguntas_padrao()
    perguntas_ativas = Pergunta.objects.filter(ativa=True)

    # Listas de opções baseadas no seu models.py
    GENERO_OPTS = ['feminino', 'masculino', 'nao_binario', 'outros']
    ETNIA_OPTS = ['branca', 'preta', 'parda', 'amarela', 'indigena']
    NACIONALIDADE_OPTS = ['brasileira', 'americana', 'espanhola', 'italiana']
    NIVEL_IDIOMA = ['basico', 'intermediario', 'fluente']
    TAMANHO_CAMISETA = ['PP', 'P', 'M', 'G', 'GG', 'XG']
    OLHOS_OPTS = ['castanho_escuro', 'castanho_claro', 'azul', 'verde', 'preto']
    CABELO_TIPO = ['liso', 'ondulado', 'cacheado', 'crespo', 'trancas']
    CABELO_TAM = ['curto', 'medio', 'longo']
    EXPERIENCIA_OPTS = ['sem_experiencia', 'pouca', 'media', 'muita']
    DISPONIBILIDADE = ['total', 'seg_sex', 'fds', 'noite', 'freelancer']
    BANCOS = ['Nubank', 'Itaú', 'Bradesco', 'Santander', 'Inter']
    TIPO_CONTA = ['corrente', 'poupanca']
    TIPO_CHAVE = ['cpf', 'email', 'telefone', 'aleatoria']

    for i in range(50):
        try:
            # 1. Criar Usuário de Login (Auth)
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1, 9999)}"
            email = f"{username}@exemplo.com"
            
            # Evitar erro de username duplicado
            if User.objects.filter(username=username).exists():
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password="senha123" # Senha padrão para todos
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # 2. Criar Perfil (UserProfile)
            perfil = UserProfile(
                user=user,
                nome_completo=f"{first_name} {last_name}",
                instagram=f"@{username}_fake",
                
                # Documentos
                cpf=fake.cpf(),
                rg=fake.rg(),
                
                # Contato e Pessoal
                whatsapp=fake.cellphone_number(),
                data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=40),
                genero=random.choice(GENERO_OPTS),
                etnia=random.choice(ETNIA_OPTS),
                
                # Nacionalidade
                nacionalidade=random.choice(NACIONALIDADE_OPTS),
                nivel_ingles=random.choice(NIVEL_IDIOMA) if random.random() > 0.5 else None,
                
                # Endereço
                cep=fake.postcode(),
                endereco=fake.street_name(),
                numero=fake.building_number(),
                bairro=fake.bairro(),
                cidade=fake.city(),
                estado=fake.estado_sigla(),
                
                # Medidas
                altura=Decimal(random.uniform(1.55, 1.90)).quantize(Decimal("0.01")),
                peso=Decimal(random.uniform(50.0, 95.0)).quantize(Decimal("0.01")),
                manequim=str(random.choice([36, 38, 40, 42, 44])),
                calcado=str(random.choice([35, 36, 37, 38, 39, 40, 41, 42])),
                tamanho_camiseta=random.choice(TAMANHO_CAMISETA),
                olhos=random.choice(OLHOS_OPTS),
                cabelo_tipo=random.choice(CABELO_TIPO),
                cabelo_comprimento=random.choice(CABELO_TAM),
                
                # Profissional
                experiencia=random.choice(EXPERIENCIA_OPTS),
                areas_atuacao="Recepção, Blitz, Eventos, Modelo Fotográfico",
                disponibilidade=random.choice(DISPONIBILIDADE),
                
                # Bancário
                banco=random.choice(BANCOS),
                tipo_conta=random.choice(TIPO_CONTA),
                agencia=str(random.randint(1000, 9999)),
                conta=f"{random.randint(10000, 99999)}-{random.randint(0,9)}",
                tipo_chave_pix=random.choice(TIPO_CHAVE),
                chave_pix=email, # Usando o email como chave pix simplificada
                
                # Termos e Status
                termo_uso_imagem=True,
                termo_comunicacao=True,
                status='pendente'
            )
            perfil.save()

            # 3. Responder Perguntas (OBRIGATÓRIO)
            for pergunta in perguntas_ativas:
                resp_texto = ""
                if pergunta.tipo == 'sim_nao':
                    resp_texto = random.choice(['Sim', 'Não'])
                else:
                    resp_texto = fake.sentence(nb_words=3)
                
                Resposta.objects.create(
                    perfil=perfil,
                    pergunta=pergunta,
                    texto_resposta=resp_texto
                )

            print(f"✅ Criado: {perfil.nome_completo}")

        except Exception as e:
            print(f"❌ Erro ao criar usuário: {e}")

    print("-" * 30)
    print("🎉 Finalizado! 50 usuários criados com perfis e respostas.")

if __name__ == "__main__":
    gerar_dados()