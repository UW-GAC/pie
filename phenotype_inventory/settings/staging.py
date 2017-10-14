"""Staging server development settings for the phenotype_inventory project.

This settings module is designed to work with an Apached site deployment. Apache
is pointed at the staging_wsgi.py script in the .conf file and the
DJANGO_SETTINGS_MODULE environment variable is set within that wsgi script. For
these specific settings, here is how the variable is set:

os.environ['DJANGO_SETTINGS_MODULE'] = 'phenotype_inventory.settings.staging'

Secret values are set in a .secrets.json file rather than as environmental
variables. In particular, DJANGO_SECRET_KEY and CNF_PATH must be set in the
secrets file for the site to function.

Functions:
    get_secret

DEBUG is True
The database backend is SQLite

Set Constants:
    STATIC_ROOT
    WSGI_APPLICATION
"""

import json
import os

from .base import *  # noqa: F403


# SECRETS SETTINGS
# Get json secrets file contents.
with open(os.path.normpath(os.path.join(BASE_DIR, 'settings', '.secrets.json'))) as f:  # noqa: F405
    secrets = json.loads(f.read())


def get_secret(setting, secrets=secrets):
    """Get the secret variable or return explicit exception.

    This function implements the recommended way to set secret variables for
    production and/or staging settings using Apache (where bash variables don't
    persist for the Apache process to use them). This recommendation is from the
    Two Scoops of Django book, example 5.19.

    With this function, the server's secret settings are kept in the .secrets.json
    file, which is listed in the .gitignore file so that it is not tracked by
    version control. These secret settings are retrieved by this function from the
    secrets file, which is read in above.

    An informative error message is reported when the secret setting requested
    is not found in the json file.

    Source: https://github.com/twoscoops/two-scoops-of-django-1.8/blob/master/code/chapter_05_example_19.py

    Arguments:
        setting -- string name of the variable setting to retrieve from the json file
        secrets -- a loaded json format file containing secret settings; default
            is the .secrets.json file loaded above

    Returns:
        the string value of the requested secret setting

    Raises:
        ImproperlyConfigured
    """
    # This function is not tested, because it was very difficult to write a test
    # using the appropriate settings module.
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {0} environment variable'.format(setting)
        raise ImproperlyConfigured(error_msg)  # noqa: F405


SECRET_KEY = get_secret('DJANGO_SECRET_KEY')
CNF_PATH = get_secret('CNF_PATH')


# DEBUG SETTINGS
DEBUG = True
INTERNAL_IPS = ('10.208.179.74', )  # The IP for gcc-pc-004.
# This IP is a "private network" IP, which is why the public IP for the client
# doesn't work in this case.
# "The assumption is that these private address ranges are not directly connected
# to the Internet, so the addresses don't have to be unique."

# DATABASE SETTINGS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': get_secret('DB_NAME'),
        'USER': get_secret('DB_USER'),
        'PASSWORD': get_secret('DB_PASS'),
        'HOST': get_secret('DB_HOST'),
        'PORT': get_secret('DB_PORT'),
        'ATOMIC_REQUESTS': True,
    }
}


# STATIC FILE SETTINGS
STATIC_ROOT = '/var/django/static_files/phenotype_inventory'
# URL prefix for static files.
STATIC_URL = '/pheno/static/'


# WSGI SETTINGS FOR APACHE MOD_WSGI
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME  # noqa: F405


# EMAIL SETTINGS
EMAIL_USE_SSL = True
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = get_secret('EMAIL_PORT')
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
DEFAULT_TO_EMAIL = EMAIL_HOST_USER
