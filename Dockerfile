FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config_api.settings.production

WORKDIR /app

RUN python -m pip install --upgrade pip setuptools wheel

# Instala dependencias necesarias del proyecto
RUN pip install --no-cache-dir \
    "django>=6.0" \
    "djangorestframework>=3.16.1" \
    "django-cors-headers>=4.9.0" \
    "djangorestframework-simplejwt>=5.5.1" \
    "python-dotenv>=1.0.0" \
    "gunicorn>=21.2.0" \
    "psycopg[binary]>=3.1"

COPY . /app

EXPOSE 8000

CMD ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && gunicorn config_api.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]
