import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "tiHhbXK19dpBpbkJXoX2KrCqV7Wmv1IO9kUx5c74nAek5maV")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

ALLOWED_HOSTS = list(filter(None, [
    "localhost",
    "127.0.0.1",
    "[::1]",
    "web",
    "django",
    "db",
    "redis",
    os.getenv("DJANGO_ALLOWED_HOSTS", ""),  # comma-separated, optional
]))

#ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# CSRF: include localhost + Docker hostnames; add your domain(s) if any
CSRF_TRUSTED_ORIGINS = list(filter(None, [
    "http://localhost",
    "http://127.0.0.1",
    "http://web",
    "http://django",
    os.getenv("CSRF_TRUSTED_ORIGINS", ""),  # comma-separated, optional
]))

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"))}

if os.getenv("REDIS_URL"):
    CACHES = {"default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL"),
    }}



CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Optionally enable compression/pickling tweaks:
            # "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            # "PARSER_CLASS": "redis.connection.HiredisParser",
        },
        "TIMEOUT": None,  # never expire by default; tune if needed
        "KEY_PREFIX": os.getenv("CACHE_KEY_PREFIX", "dj"),
    },
    "query": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # 5 min for query caching, tune as needed
        "KEY_PREFIX": os.getenv("QUERY_CACHE_KEY_PREFIX", "djq"),
    },
}



STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

