from .base import *
import os

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

########## SNUFFLES DATABASE CONNECTION INFO
CNF_PATH = os.path.join(os.path.expanduser("~"), ".mysql-topmed.cnf")
########## END SNUFFLES DATABASE CONNECTION INFO

########## SECRET_KEY CONFIGURATION
# Requires DJANGO_SECRET_KEY environmental variable to be set
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')
########## END SECRET_KEY CONFIGURATION

