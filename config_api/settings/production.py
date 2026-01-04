from .base import *
import os
import dj_database_url


DEBUG = False

# Donde vive el api
ALLOWED_HOSTS = ["api.tdkoders.online"]

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        ssl_require=True,
    )
}

# Quien puede llamar al api
CORS_ALLOWED_ORIGINS = [
    "https://tdkoders.online",
]

# Quien puede enviar cookies y demás data al api (incluye credenciales)
CSRF_TRUSTED_ORIGINS = [
    "https://tdkoders.online",
    "https://api.tdkoders.online",
]
