# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


def add_phenotype_taggers_group(apps, schema_editor):
    """Create the 'phenotype_taggers' group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name='phenotype_taggers')


def remove_phenotype_taggers_group(apps, schema_editor):
    """Remove the 'phenotype_taggers' group."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.get(name='phenotype_taggers').delete()


class Migration(migrations.Migration):

    dependencies = [
        # See this SO comment: https://stackoverflow.com/questions/33485464/right-way-to-create-a-django-data-migration-that-creates-a-group#comment72582870_33486304
        # From the built-in help: swappable_dependency(value): Turns a setting value into a dependency.
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_initial_groups'),
    ]

    operations = [
    migrations.RunPython(add_phenotype_taggers_group, reverse_code=remove_phenotype_taggers_group)
    ]
