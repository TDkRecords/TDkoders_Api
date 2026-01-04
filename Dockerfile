FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config_api.settings.production

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && gunicorn config_api.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]
