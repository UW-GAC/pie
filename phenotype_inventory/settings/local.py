from .base import *

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


########## SECRET_KEY CONFIGURATION
# Requires DJANGO_SECRET_KEY environmental variable to be set
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')
########## END SECRET_KEY CONFIGURATION

