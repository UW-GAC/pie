"""Production server development settings for the phenotype_inventory project.

This settings module is designed to work with an Apached site deployment. Apache
is pointed at the production_wsgi.py script in the .conf file and the
DJANGO_SETTINGS_MODULE environment variable is set within that wsgi script. For
these specific settings, here is how the variable is set:
  
os.environ['DJANGO_SETTINGS_MODULE'] = 'phenotype_inventory.settings.production'

Secret values are set in a .secrets.json file rather than as environmental
variables. In particular, DJANGO_SECRET_KEY and CNF_PATH must be set in the
secrets file for the site to function.

The staging settings are imported and then a few of them are over-ridden in
this module.

Functions:
    get_secret

DEBUG is False
The database backend is SQLite

Set Constants:
    STATIC_ROOT
    WSGI_APPLICATION
"""

import json

from .staging import *


########## DEBUG CONFIGURATION
DEBUG = False
ALLOWED_HOSTS = []
########## END DEBUG CONFIGURATION


########## DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}
########## END DATABASE CONFIGURATION


########## STATIC FILE CONFIGURATION
# Change this later
STATIC_ROOT = '/var/django/topmed_pheno_site/static_collected/'
########## END STATIC FILE CONFIGURATION