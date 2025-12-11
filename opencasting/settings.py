from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-troque-isso-em-producao'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# --- APLICATIVOS INSTALADOS ---
INSTALLED_APPS = [
    'jazzmin',                  # <--- TEMA MODERNO (Sempre no topo)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'cloudinary_storage',       # <--- ARMAZENAMENTO DE FOTOS
    'cloudinary',               # <--- BIBLIOTECA CLOUDINARY
    
    'core',                     # <--- SEU APP
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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# --- CONFIGURAÇÃO DE LOGIN/LOGOUT ---
LOGIN_REDIRECT_URL = 'lista_vagas'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# --- CONFIGURAÇÃO CLOUDINARY (SUAS CHAVES REAIS) ---
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dszogqjjj',
    'API_KEY': '195742113116927',
    'API_SECRET': 'TBBhLIVMMdWYvlMmT6lRb-gF4wk',
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'  # URL base para acessar fotos

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURAÇÃO DO PAINEL ADMIN (JAZZMIN) ---
JAZZMIN_SETTINGS = {
    "site_title": "OpenCasting Admin",
    "site_header": "OpenCasting",
    "site_brand": "OpenCasting",
    "welcome_sign": "Bem-vindo ao Painel de Controle",
    "copyright": "OpenCasting Agency",
    "search_model": ["core.UserProfile", "core.Job"],
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.UserProfile": "fas fa-id-card-alt",
        "core.Job": "fas fa-briefcase",
        "core.Candidatura": "fas fa-hand-paper",
        "core.Pergunta": "fas fa-question-circle",
    },
}

JAZZMIN_UI_TWEAKS = {
    "brand_colour": "navbar-teal",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-teal",
    "theme": "flatly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}