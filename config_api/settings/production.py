from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    'tu-dominio.com',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'TU_PASSWORD',
        'HOST': 'db.xxxxx.supabase.co',
        'PORT': '5432',
    }
}

CORS_ALLOWED_ORIGINS = [
    'https://tu-frontend.com',
]
