"""Settings to run unittests on servers for the phenotype_inventory project.

Use this settings module only with the migrate.py test command. Make sure to
manually specify this settings module, like so:

./manage.py test --settings=phenotype_inventory.settings.unittest

DEBUG is set to True
The database backend is SQLite
SECRET_KEY and CNF_PATH are obtained from the .secrets.json file.
"""

import os

from .base import *  # noqa: F403
from .staging import secrets, get_secret  # noqa: F401


# DEBUG SETTINGS
DEBUG = True


# DATABASE SETTINGS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.normpath(os.path.join(SITE_ROOT, 'site_db.sqlite3')),  # noqa: F405
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}


# SNUFFLES DATABASE CONNECTION SETTINGS
CNF_PATH = get_secret('CNF_PATH')


# SECRET_KEY SETTINGS
SECRET_KEY = get_secret('DJANGO_SECRET_KEY')
