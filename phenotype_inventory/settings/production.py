from .staging import *
import json

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


