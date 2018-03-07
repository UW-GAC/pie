"""Base Django settings for phenotype_inventory project.

Setup according to Jacob Kaplan-Moss's 'One True Way'
(https://speakerdeck.com/jacobian/the-best-and-worst-of-django?slide=81)
and recommendations from Two Scoops of Django 1.8

Base settings are applicable to all environments, and
local.py, production.py, and staging.py all build on
base.py. Each setting module is specified either through an
argument to manage.py runserver, or through setting environment
or secret variables, depending on the environment where your
site is set up.

Functions:
    get_env_variable

Custom Constants:
    SITE_NAME
    SITE_ROOT
    SITE_ID
    CRISPY_TEMPLATE_PACK
"""

import os
from socket import gethostname

# Normally you should not import ANYTHING from Django directly
# into your settings, but ImproperlyConfigured is an exception
# here for the purpose of returning an informative error message.
from django.core.exceptions import ImproperlyConfigured
# Use this in resetting MESSAGE_TAGS in the template settings.
from django.contrib.messages import constants as message_constants


def get_env_variable(var_name):
    """Get the environment variable or return exception.

    From Two Scoops of Django, this function is the recommended way to
    access local vs. production settings for a django site. This is from
    example 5.15 from the book. For local settings, do 'export VAR_NAME=value'
    in a setting file for the conda env or virtualenv used for the project.
    Then this function can retrieve the environmental variable from bash
    using the variable name.

    This funciton also prints an informative error message and raises an
    informative exception if the environmental variable is not already set.

    Source:
        https://github.com/twoscoops/two-scoops-of-django-1.8/blob/master/code/chapter_05_example_15.py

    Arguments:
        var_name is a string of the name of the variable to get from the bash
        environment

    Returns:
        string value of the environmental variable value

    Raises:
        ImproperlyConfigured when an environment variable is not set first.
    """
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise ImproperlyConfigured(error_msg)


# PATH SETTINGS
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# These are some custom settings based on an online example:
# https://www.rdegges.com/2011/the-perfect-django-settings-file/
# Get the project name from the base directory name.
SITE_NAME = os.path.basename(BASE_DIR)
# Absolute filesystem path to the top-level project folder.
SITE_ROOT = os.path.dirname(BASE_DIR)


# DEBUG SETTINGS
# Disable debugging by default.
DEBUG = False


# LOCALE SETTINGS
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Vancouver'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# STATIC FILE SETTINGS
# Additional locations of static files.
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'static'),
)
# This may be overridden for a particular deployment.
STATIC_URL = '/static/'
# END STATIC FILE CONFIGURATION


# TEMPLATE SETTINGS
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Directories to search when loading templates.
        'DIRS': [os.path.join(SITE_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'phenotype_inventory.context_processors.site',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Change the message tag name to match the bootstrap alert class name.
MESSAGE_TAGS = {message_constants.DEBUG: 'alert-debug',
                message_constants.INFO: 'alert-info',
                message_constants.SUCCESS: 'alert-success',
                message_constants.WARNING: 'alert-warning',
                message_constants.ERROR: 'alert-danger',
                }


# MIDDLEWARE SETTINGS
MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'maintenance_mode.middleware.MaintenanceModeMiddleware',
)


# APP SETTINGS
INSTALLED_APPS = (
    # django-autocomplete-light, which must be loaded BEFORE django.contrib.admin
    'dal',
    'dal_select2',
    'django_admin_bootstrapped',
    # Built-in apps.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Sites and flatpages.
    'django.contrib.sites',    # https://docs.djangoproject.com/en/1.8/ref/contrib/sites/
    'django.contrib.flatpages',    # https://docs.djangoproject.com/es/1.9/ref/contrib/flatpages/
    # 3rd party apps.
    'debug_toolbar',    # https://github.com/jazzband/django-debug-toolbar
    'django_tables2',    # https://github.com/bradleyayers/django-tables2
    'crispy_forms',    # https://github.com/maraujop/django-crispy-forms
    'django_extensions',    # https://github.com/django-extensions/django-extensions
    'authtools',    # https://django-authtools.readthedocs.io/en/latest/index.html
    'dbbackup',    # https://github.com/django-dbbackup/django-dbbackup
    'maintenance_mode',    # https://github.com/fabiocaccamo/django-maintenance-mode
    # Our custom apps.
    'trait_browser',    # Handles table-based viewing and searching of trait data.
    'core',    # Code used across the project, and data migrations for built-in apps (e.g. sites).
    'profiles',    # Handles profile data for users interacting with the site.
    'recipes',
    'tags',
)


# URL SETTINGS
ROOT_URLCONF = '%s.urls' % SITE_NAME
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'


# THIRD PARTY APP SETTINGS
# django.contrib.sites SETTINGS variables.
SITE_ID = 1
# crispy_forms SETTINGS variables.
CRISPY_TEMPLATE_PACK = 'bootstrap3'
# dbbackup
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': SITE_ROOT + '/../phenotype_inventory_db_backups'}
DBBACKUP_CLEANUP_KEEP = 10
# maintenance_mode
MAINTENANCE_MODE_IGNORE_SUPERUSER = True

# USER AUTHENTICATION SETTINGS
AUTH_USER_MODEL = 'authtools.User'


# PROJECT SETTINGS
GAC_WEBSERVERS = ['modu', 'gcc-pc-004', ]
DEVELOPMENT = not (gethostname() in GAC_WEBSERVERS)
