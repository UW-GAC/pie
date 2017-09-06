"""Local development settings for the phenotype_inventory project.

To use the this settings module, set your PYTHONPATH and
DJANGO_SETTINGS_MODULE environmental variables. For example:

    export DJANGO_SETTINGS_MODULE='phenotype_inventory.settings.local'
    export PYTHONPATH='~/devel/phenotype_inventory'

PYTHONPATH is the project's top level directory, containing all scripts for
the website.
DJANGO_SETTINGS_MODULE is the appropriate settings module to use for the
given environment

DEBUG is set to True
The database backend is SQLite
CNF_PATH is the user's home directory msyql .cnf
SECRET_KEY is obtained from the bash environment variable
"""

import os

from .base import *  # noqa: F403


# DEBUG SETTINGS
DEBUG = True
INTERNAL_IPS = ('127.0.0.1', )


# DATABASE SETTINGS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.normpath(os.path.join(SITE_ROOT, 'site_db.sqlite3')),  # noqa: F405
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'ATOMIC_REQUESTS': True,
    }
}


# SNUFFLES DATABASE CONNECTION SETTINGS
CNF_PATH = os.path.join(os.path.expanduser('~'), '.mysql-topmed.cnf')


# SECRET_KEY SETTINGS
# Requires DJANGO_SECRET_KEY environmental variable to be set
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')  # noqa: F405


# EMAIL SETTINGS
# To view sent emails in a shell, run this command:
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'development_testing@django.site'
