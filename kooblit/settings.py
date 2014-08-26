"""
Django settings for kooblit project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import yaml
from slugify import Slugify

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
s = yaml.load(open(os.path.join(PROJECT_ROOT, "config.yaml"), "r").read())

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
AMAZON_KEY = s["AMAZON_KEY"]
MONGO_PWD = s["MONGO_PWD"]
MONGO_USER = s["MONGO_USER"]
PAYMILL_PRIV = s["PAYMILL_PRIV"]
PAYMILL_PUB = s["PAYMILL_PUB"]

from mongoengine import connect
connect('docs_db', username=MONGO_USER, password=MONGO_PWD)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SLUGIFY BOOKS TITLE
BOOKS_SLUG = Slugify(to_lower=True)
BOOKS_SLUG.separator = ' '

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

SECRET_KEY = s["SECRET_KEY"]

# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'search_engine',
    'usr_management',
    'south',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'achat.middleware.CartMiddleware',
)


ROOT_URLCONF = 'kooblit.urls'

WSGI_APPLICATION = 'kooblit.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'kooblit_db',
        'USER': 'endoderconic',
        'PASSWORD': s['DB_PASSWORD'],
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
AUTH_PROFILE_MODULE = "usr_management.UserKooblit"

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/static/'

STATICFILES_FINDER = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder', )

STATICFILES_DIRS = ( '/home/endoderconic/kooblit/static/',)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates/'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages"
)

AUTHENTICATION_BACKENDS = (
    'usr_management.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend'
)
EMAIL_HOST = s['EMAIL_HOST']
EMAIL_HOST_PASSWORD = s['EMAIL_HOST_PASSWORD']
EMAIL_HOST_USER = s['EMAIL_HOST_USER']
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# INTERNE
MAX_BOOK_TITLE_LEN = 1024

MEDIA_ROOT='/var/www/media'
