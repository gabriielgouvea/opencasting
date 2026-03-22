import os
from pathlib import Path
from django.templatetags.static import static
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-only')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', '1').strip() in {'1', 'true', 'True', 'yes', 'YES'}

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Segurança em produção
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# Application definition
INSTALLED_APPS = [
    'unfold',                   # <--- TEMA MODERNO DO ADMIN (Sempre primeiro)
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
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'core.password_validators.ComplexityPasswordValidator'},
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
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'core/static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- CLOUDINARY (FOTOS) ---
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --- E-MAIL (GMAIL) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Casting Certo <no-reply@localhost>')

# --- LOGIN ---
LOGIN_REDIRECT_URL = 'lista_vagas'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# --- CONFIGURAÇÃO DO ADMIN (UNFOLD) ---
UNFOLD = {
    "SITE_TITLE": "Casting Certo",
    "SITE_HEADER": "Casting Certo",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "dark",
    "STYLES": [
        lambda request: static("css/admin_custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin_custom.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "#e0f2f1",
            "100": "#b2dfdb",
            "200": "#80cbc4",
            "300": "#4db6ac",
            "400": "#26a69a",
            "500": "#009688",
            "600": "#00897b",
            "700": "#00796b",
            "800": "#00695c",
            "900": "#004d40",
            "950": "#002e27",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Gestão",
                "items": [
                    {
                        "title": "Base de Promotores",
                        "icon": "badge",
                        "link": reverse_lazy("admin:core_userprofile_changelist"),
                    },
                    {
                        "title": "Clientes",
                        "icon": "business",
                        "link": reverse_lazy("admin:core_cliente_changelist"),
                    },
                    {
                        "title": "Orçamentos",
                        "icon": "request_quote",
                        "link": reverse_lazy("admin:core_orcamento_changelist"),
                    },
                    {
                        "title": "Vagas / Jobs",
                        "icon": "work",
                        "link": reverse_lazy("admin:core_job_changelist"),
                    },
                    {
                        "title": "Candidaturas",
                        "icon": "description",
                        "link": reverse_lazy("admin:core_candidatura_changelist"),
                    },
                ],
            },
            {
                "title": "Sistema",
                "items": [
                    {
                        "title": "Equipe Interna",
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Contatos do Site",
                        "icon": "settings",
                        "link": reverse_lazy("admin:core_configuracaosite_changelist"),
                    },
                    {
                        "title": "CPFs Banidos",
                        "icon": "block",
                        "link": reverse_lazy("admin:core_cpfbanido_changelist"),
                    },
                ],
            },
            {
                "title": "Links Rápidos",
                "items": [
                    {
                        "title": "Ver Site",
                        "icon": "open_in_new",
                        "link": "/",
                    },
                    {
                        "title": "Suporte Técnico",
                        "icon": "support_agent",
                        "link": "https://wa.me/5511999999999",
                    },
                ],
            },
        ],
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'