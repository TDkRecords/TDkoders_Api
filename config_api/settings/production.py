from .base import *
import os
import dotenv

dotenv.load_dotenv()

DEBUG = False

# Donde vive el api
ALLOWED_HOSTS = ["api.tdkoders.online"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Quien puede llamar al api
CORS_ALLOWED_ORIGINS = [
    "https://tdkoders.online",
]

# Quien puede enviar cookies y demás data al api (incluye credenciales)
CSRF_TRUSTED_ORIGINS = [
    "https://tdkoders.online",
]
