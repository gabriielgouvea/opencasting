import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-troque-isso-por-algo-seguro-em-producao'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'jazzmin',                  # <--- TEMAS DO ADMIN (Sempre o primeiro)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps de Terceiros
    'cloudinary_storage',       # Armazenamento Nuvem
    'cloudinary',

    # Seus Apps
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'opencasting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # --- AQUI ESTÁ A CORREÇÃO CRUCIAL ---
        # Antes estava apontando para core/templates. 
        # Agora aponta para a pasta templates na raiz, onde está o seu dashboard.
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # --- CONTEXT PROCESSOR DO RODAPÉ ---
                'core.context_processors.site_config', 
            ],
        },
    },
]

WSGI_APPLICATION = 'opencasting.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- IDIOMA E FUSO HORÁRIO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- ARQUIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Importante: Onde o Django busca seus CSS/JS personalizados
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'core/static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- CLOUDINARY (FOTOS) ---
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dszogqjjj',
    'API_KEY': '195742113116927',
    'API_SECRET': 'TBBhLIVMMdWYvlMmT6lRb-gF4wk',
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --- E-MAIL (GMAIL) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'gabriielgouvea@gmail.com'
EMAIL_HOST_PASSWORD = 'niwdootsbzrabfji'
DEFAULT_FROM_EMAIL = 'OpenCasting <gabriielgouvea@gmail.com>'

# --- LOGIN ---
LOGIN_REDIRECT_URL = 'lista_vagas'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# --- CONFIGURAÇÃO DO ADMIN (JAZZMIN) ---
JAZZMIN_SETTINGS = {
    # Textos
    "site_title": "Gestão OpenCasting",
    "site_header": "OpenCasting Admin",
    "site_brand": "OpenCasting",
    "welcome_sign": "Painel de Controle Administrativo",
    "copyright": "Gouvea Automações",
    "search_model": ["core.UserProfile"],

    # Menu Superior
    "topmenu_links": [
        {"name": "Ver Site (Área do Candidato)", "url": "home", "permissions": ["auth.view_user"]},
        {"name": "Suporte Técnico", "url": "https://wa.me/5511999999999", "new_window": True},
    ],

    # Organização do Menu Lateral
    "order_with_respect_to": [
        "core.UserProfile", # Promotores
        "core.Job",         # Vagas
        "core.Candidatura", # Candidaturas
        "auth.User",        # Equipe Interna
    ],

    # Ícones
    "icons": {
        "auth": "fas fa-cogs",
        "auth.user": "fas fa-user-tie",
        "core.userprofile": "fas fa-id-badge",
        "core.job": "fas fa-briefcase",
        "core.candidatura": "fas fa-file-signature",
        "core.pergunta": "fas fa-question-circle",
        "core.avaliacao": "fas fa-star",
        "core.configuracaosite": "fas fa-sliders-h", 
    },

    "hide_models": ["auth.group", "core.resposta", "core.jobdia", "core.avaliacao"],

    # --- ARQUIVOS PERSONALIZADOS ---
    "custom_css": "css/admin_custom.css",
    "custom_js": "js/admin_custom.js", 

    # --- ADICIONE ESTAS LINHAS ABAIXO ---
    # Isso obriga o Jazzmin a renderizar os filtros na lista (onde o JS consegue ler)
    "change_list_filter_dropdown": False, 
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"core.userprofile": "collapsible"},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-white",
    "accent": "accent-teal",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-teal",
    "sidebar_nav_small_text": False,
    "theme": "lumen", 
    "button_classes": {
        "primary": "btn-outline-success",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'