"""Data migration to set the site domain and name to proper values."""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


# Source: example code in Django Unleased 15.7
# Function to apply the migration
def add_site_data(apps, schema_editor):
    """Add or change site data.

    Add a new Site instance with the information we want for our site, or,
    if it already exists, alter the domain name for the existing site instance.
    """
    Site = apps.get_model('sites', 'Site')  # Get the historical Site model
    new_domain = 'topmedphenotypes.org'
    new_name = 'TOPMed PIE'
    site_id = getattr(settings, 'SITE_ID', 1)
    if Site.objects.exists():
        current_site = Site.objects.get(
            pk=site_id)
        current_site.domain = new_domain
        current_site.name = new_name
        current_site.save()
    else:
        current_site = Site(
            pk=site_id,  # coerce primary key
            domain=new_domain,
            name=new_name)
        current_site.save()


# Function to unapply the migration.
def remove_site_data(apps, schema_editor):
    """Restore the 'example.com' default site domain."""
    Site = apps.get_model('sites', 'Site')
    current_site = Site.objects.get(
        pk=getattr(settings, 'SITE_ID', 1))
    current_site.domain = 'example.com'
    current_site.name = 'example.com'
    current_site.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_site_data,
            remove_site_data,
        ),
    ]
