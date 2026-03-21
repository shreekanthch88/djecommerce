import os
import sys

import dj_database_url
from decouple import config


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def env_flag(name, default=False):
    value = config(name, default=None)
    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on', 'debug', 'development', 'dev'}:
        return True
    if normalized in {'0', 'false', 'no', 'off', 'release', 'production', 'prod', ''}:
        return False
    return default


SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = env_flag('DEBUG', default=True)
IS_RUNSERVER = 'runserver' in sys.argv
ALLOWED_HOSTS = [
    host.strip()
    for host in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
    if host.strip()
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_countries',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
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

WSGI_APPLICATION = 'djecommerce.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

database_url = config('DATABASE_URL', default='')
IS_LOCAL_ENV = not database_url

if database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite3'),
        }
    }


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [os.path.join(PROJECT_ROOT, 'static_in_env')]
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_root')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media_root')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'


CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap4',)


CSRF_TRUSTED_ORIGINS = [
    origin.strip().strip("'\"[]")
    for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',')
    if origin.strip()
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
secure_defaults_enabled = not IS_LOCAL_ENV and not IS_RUNSERVER
SECURE_SSL_REDIRECT = env_flag('SECURE_SSL_REDIRECT', default=secure_defaults_enabled)
SESSION_COOKIE_SECURE = env_flag('SESSION_COOKIE_SECURE', default=secure_defaults_enabled)
CSRF_COOKIE_SECURE = env_flag('CSRF_COOKIE_SECURE', default=secure_defaults_enabled)


EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='noreply@localhost' if DEBUG else 'webmaster@localhost',
)


if DEBUG:
    RAZORPAY_KEY_ID = config(
        'RAZORPAY_TEST_KEY_ID',
        default=config('RAZORPAY_LIVE_KEY_ID', default=''),
    )
    RAZORPAY_KEY_SECRET = config(
        'RAZORPAY_TEST_KEY_SECRET',
        default=config('RAZORPAY_LIVE_KEY_SECRET', default=''),
    )
else:
    RAZORPAY_KEY_ID = config(
        'RAZORPAY_LIVE_KEY_ID',
        default=config('RAZORPAY_TEST_KEY_ID', default=''),
    )
    RAZORPAY_KEY_SECRET = config(
        'RAZORPAY_LIVE_KEY_SECRET',
        default=config('RAZORPAY_TEST_KEY_SECRET', default=''),
    )

GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
