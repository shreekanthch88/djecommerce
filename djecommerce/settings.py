import os
import sys

import dj_database_url
from decouple import AutoConfig


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
config = AutoConfig(search_path=PROJECT_ROOT)


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


def env_value(name, default=''):
    value = str(config(name, default=default)).strip()
    if not value:
        return default
    if value.lower().startswith('your-'):
        return ''
    return value


def env_list(name, default=''):
    return [
        item.strip().strip("'\"[]")
        for item in str(config(name, default=default)).split(',')
        if item.strip()
    ]


SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')
DEBUG = env_flag('DEBUG', default=True)
IS_RUNSERVER = 'runserver' in sys.argv
ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost,shreekanthch.pythonanywhere.com',
)
if IS_RUNSERVER:
    for local_host in ['127.0.0.1', 'localhost', '0.0.0.0', '[::1]']:
        if local_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local_host)
render_hostname = env_value('RENDER_EXTERNAL_HOSTNAME')
render_service_name = env_value('RENDER_SERVICE_NAME')
pythonanywhere_domain = env_value(
    'PYTHONANYWHERE_DOMAIN',
    default='shreekanthch.pythonanywhere.com',
)
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if render_service_name:
    render_onrender_host = f'{render_service_name}.onrender.com'
    if render_onrender_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_onrender_host)
if pythonanywhere_domain and pythonanywhere_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(pythonanywhere_domain)


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


CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', default='')
if IS_RUNSERVER:
    for local_origin in ['http://127.0.0.1:8000', 'http://localhost:8000']:
        if local_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(local_origin)
if render_hostname:
    render_origin = f'https://{render_hostname}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)
if render_service_name:
    render_service_origin = f'https://{render_service_name}.onrender.com'
    if render_service_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_service_origin)
if pythonanywhere_domain:
    pythonanywhere_origin = f'https://{pythonanywhere_domain}'
    if pythonanywhere_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(pythonanywhere_origin)
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


RAZORPAY_MODE = config(
    'RAZORPAY_MODE',
    default='test' if IS_LOCAL_ENV else ('test' if DEBUG else 'live'),
).strip().lower()
if RAZORPAY_MODE not in {'test', 'live'}:
    RAZORPAY_MODE = 'test' if IS_LOCAL_ENV else 'live'

RAZORPAY_TEST_KEY_ID = env_value('RAZORPAY_TEST_KEY_ID')
RAZORPAY_TEST_KEY_SECRET = env_value('RAZORPAY_TEST_KEY_SECRET')
RAZORPAY_LIVE_KEY_ID = env_value('RAZORPAY_LIVE_KEY_ID')
RAZORPAY_LIVE_KEY_SECRET = env_value('RAZORPAY_LIVE_KEY_SECRET')

if RAZORPAY_MODE == 'live':
    RAZORPAY_KEY_ID = RAZORPAY_LIVE_KEY_ID or RAZORPAY_TEST_KEY_ID
    RAZORPAY_KEY_SECRET = RAZORPAY_LIVE_KEY_SECRET or RAZORPAY_TEST_KEY_SECRET
else:
    RAZORPAY_KEY_ID = RAZORPAY_TEST_KEY_ID or RAZORPAY_LIVE_KEY_ID
    RAZORPAY_KEY_SECRET = RAZORPAY_TEST_KEY_SECRET or RAZORPAY_LIVE_KEY_SECRET

GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
