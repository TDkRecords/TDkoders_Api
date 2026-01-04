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
        "NAME": os.environ.get("PGDATABASE"),
        "USER": os.environ.get("PGUSER"),
        "PASSWORD": os.environ.get("PGPASSWORD"),
        "HOST": os.environ.get("PGHOST"),
        "PORT": os.environ.get("PGPORT", "5432"),
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
