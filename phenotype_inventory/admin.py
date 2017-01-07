"""Set up admin for the entire project."""

from django.contrib import admin
from django.contrib.sites.models import Site

site_name = Site.objects.get_current().name
# Set the name for the admin site.
admin.site.site_header = site_name + ' Administration'
