from .base import *
import json

########## SECRETS CONFIGURATION
# JSON-based secrets module
with open(os.path.normpath(os.path.join(BASE_DIR, 'settings', '.secrets.json'))) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    """Get the secret variable or return explicit exception."""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {0} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)

SECRET_KEY = get_secret("DJANGO_SECRET_KEY")
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


