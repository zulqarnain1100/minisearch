#!/usr/bin/env bash
set -euo pipefail

# --- Wait for Postgres to be ready ---
echo "Waiting for Postgres..."
until pg_isready -h db -p 5432 -U "${POSTGRES_USER:-django}" >/dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

cd /app

# --- Bootstrap Django project if missing ---
if [ ! -f "manage.py" ]; then
  echo "No Django project found; creating one in /app ..."
  # Create project "config" in the current dir (manage.py at /app/manage.py)
  django-admin startproject config .
  # create a sample application "core"
  python manage.py startapp core

  # Overwrite config/settings.py with our initial setup (safe on first run)
  cat > config/settings.py <<'PY'
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # local app
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database via env (DATABASE_URL), e.g. postgresql+psycopg://user:pass@db:5432/db
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
}

# Cache (Redis) via REDIS_URL=redis://redis:6379/0
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
        }
    }

# Static/Media (dev-friendly defaults)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PY

  # Create minimal urls.py if missing
  if [ ! -f "config/urls.py" ]; then
    cat > config/urls.py <<'PY'
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def ok(_):
    return HttpResponse("Django is up ✨")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ok),
]
PY
  fi
fi

# --- DB migrations (safe to run every start) ---
python manage.py migrate --noinput

# --- (Optional) collect static in dev; keep commented if not needed ---
# python manage.py collectstatic --noinput

echo "Starting Django dev server on 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000

