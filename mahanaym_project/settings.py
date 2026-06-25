from pathlib import Path
from datetime import timedelta

# 1. Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Configuración de seguridad para desarrollo y producción
SECRET_KEY = 'django-insecure-demo-mahanaym'
DEBUG = True

# Permitir que el servidor responda en Render
ALLOWED_HOSTS = ['*']

# Solución al error 403: Permitir que Django confíe en las peticiones de tu dominio en la nube
CSRF_TRUSTED_ORIGINS = ['https://mahanaym-demo.onrender.com']

# 3. Aplicaciones instaladas del sistema y dependencias
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',      # Framework para la API Rest
    'plataforma',          # Tu aplicación académica para el colegio
]

# 4. Middlewares del sistema (Orden correcto para autenticación)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mahanaym_project.urls'

# 5. Configuración del motor de plantillas HTML para la interfaz visual
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mahanaym_project.wsgi.application'

# 6. Base de datos interna para persistencia de usuarios locales (createsuperuser)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 7. Validadores de contraseñas de Django
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

# 8. Configuración regional e idioma
LANGUAGE_CODE = 'es-ec'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 9. Configuración de Django REST Framework para usar JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# 10. Parámetros de los Tokens JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1), # Duración de 24 horas para pruebas estables
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# 11. Configuración obligatoria de archivos estáticos
STATIC_URL = 'static/'