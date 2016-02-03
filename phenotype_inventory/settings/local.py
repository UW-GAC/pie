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


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5-baroul^vr5_nmx(x2b5y+8k7)73@wld5z^+$^ni65dsxd@7m'
