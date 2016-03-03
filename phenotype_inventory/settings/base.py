"""
Base Django settings for phenotype_inventory project.

Setup according to Jacob Kaplan-Moss's 'One True Way'
(https://speakerdeck.com/jacobian/the-best-and-worst-of-django?slide=81)
and recommendations from Two Scoops of Django 1.8

Base settings are applicable to all environments, and
local.py, production.py, and staging.py all build on
base.py.

To use the appropriate settings files, set your PYTHONPATH and
DJANGO_SETTINGS_MODULE environmental variables. For example:

    export DJANGO_SETTINGS_MODULE='phenotype_inventory.settings.local'
    export PYTHONPATH='~/devel/phenotype_inventory'
    
PYTHONPATH is the project's top level directory, containing all scripts for
the website.
DJANGO_SETTINGS_MODULE is the appropriate settings module to use for the
given environment and should be one of the following:
phenotype_inventory.settings.local
phenotype_inventory.settings.staging
phenotype_inventory.settings.production
"""

import os

# Normally you should not import ANYTHING from Django directly
# into your settings, but ImproperlyConfigured is an exception.
from django.core.exceptions import ImproperlyConfigured

# Use this function to get required environmental variables for settings
def get_env_variable(var_name):
    """Get the environment variable or return exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable".format(var_name)
        raise ImproperlyConfigured(error_msg)


########## PATH CONFIGURATION
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

## These are some custom settings based on an online example
## https://www.rdegges.com/2011/the-perfect-django-settings-file/

# Site name.
SITE_NAME = os.path.basename(BASE_DIR)

# Absolute filesystem path to the top-level project folder.
SITE_ROOT = os.path.dirname(BASE_DIR)
########## END PATH CONFIGURATION


########## DEBUG CONFIGURATION
# Disable debugging by default.
DEBUG = False

# We'll need to set ALLOWED_HOSTS for DEBUG=False to work
# but this should be in production settings
# ALLOWED_HOSTS = []
########## END DEBUG CONFIGURATION


########## LOCALE CONFIGURATION
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Vancouver'
USE_I18N = True
USE_L10N = True
USE_TZ = True
########## END LOCALE CONFIGURATION


########## STATIC FILE CONFIGURATION
# URL prefix for static files
STATIC_URL = '/static/'

# Additional locations of static files.
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, "static"), 
    )
########## END STATIC FILE CONFIGURATION


########## TEMPLATE CONFIGURATION
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Directories to search when loading templates. 
        'DIRS': [os.path.join(SITE_ROOT, 'templates')],
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

########## END TEMPLATE CONFIGURATION


########## MIDDLEWARE CONFIGURATION
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)
########## END MIDDLEWARE CONFIGURATION


########## APP CONFIGURATION
INSTALLED_APPS = (
    # Built-in apps.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Sites and flatpages.
    'django.contrib.sites',       # https://docs.djangoproject.com/en/1.8/ref/contrib/sites/
    'django.contrib.flatpages',   # https://docs.djangoproject.com/es/1.9/ref/contrib/flatpages/
    
    # 3rd party apps.
    'django_tables2',     # https://github.com/bradleyayers/django-tables2
    'crispy_forms',       # https://github.com/maraujop/django-crispy-forms
    
    # Our custom apps.
    'trait_browser',   # handles table-based viewing and searching of trait data
    'core',            # handles data migrations for built-in apps (e.g. sites)
)
########## END APP CONFIGURATION


########## URL CONFIGURATION
ROOT_URLCONF = '%s.urls' % SITE_NAME
########## END URL CONFIGURATION


########## APP-SPECIFIC CONFIGURATION
# django.contrib.sites
SITE_ID = 1

# crispy_forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'
########## END APP-SPECIFIC CONFIGURATION




