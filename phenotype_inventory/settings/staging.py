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

from .base import *


########## SECRETS CONFIGURATION
# JSON-based secrets module
with open(os.path.normpath(os.path.join(BASE_DIR, 'settings', '.secrets.json'))) as f:
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
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {0} environment variable'.format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret('DJANGO_SECRET_KEY')
CNF_PATH = get_secret('CNF_PATH')
########## END SECRETS CONFIGURATION


########## DEBUG CONFIGURATION
DEBUG = True
########## END DEBUG CONFIGURATION


########## DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.normpath(os.path.join(SITE_ROOT, 'site_db.sqlite3')),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}
########## END DATABASE CONFIGURATION


########## STATIC FILE CONFIGURATION
STATIC_ROOT = '/var/django/topmed_pheno_site/static_collected/'
########## END STATIC FILE CONFIGURATION


########## WSGI CONFIGURATION FOR APACHE MOD_WSGI
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME 
########## END WSGI CONFIGURATION FOR APACHE MOD_WSGI