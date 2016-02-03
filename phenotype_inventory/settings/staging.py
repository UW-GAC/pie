from .base import *


########## DEBUG CONFIGURATION
DEBUG = True
TEMPLATE_DEBUG = DEBUG
########## END DEBUG CONFIGURATION


########## DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.normpath(join(SITE_ROOT, 'site_db', 'sqlite3')),
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


