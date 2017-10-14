"""Production server WSGI config for phenotype_inventory project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/

The environmental variable for which settings module to use is set here.
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ["DJANGO_SETTINGS_MODULE"] = "phenotype_inventory.settings.production"

application = get_wsgi_application()
