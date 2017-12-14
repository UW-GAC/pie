# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


def add_phenotype_taggers_group(apps, schema_editor):
    """Create the 'phenotype_taggers' group and give tagging permissions."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Get or create the phenotype_taggers group.
    tagger_group = Group.objects.get_or_create(name='phenotype_taggers')[0]
    analysts_group = Group.objects.get(name='dcc_analysts')
    developers_group = Group.objects.get(name='dcc_developers')
    # Add all permissions for the tags models to the group, and to DCC analysts.
    tag_permissions = Permission.objects.filter(content_type__app_label='tags', content_type__model='tag')
    analysts_group.permissions.add(*tag_permissions)
    developers_group.permissions.add(*tag_permissions)
    taggedtrait_permissions = Permission.objects.filter(
        content_type__app_label='tags', content_type__model='taggedtrait')
    tagger_group.permissions.add(*taggedtrait_permissions)


def remove_phenotype_taggers_group(apps, schema_editor):
    """Remove the 'phenotype_taggers' group and revoke tagging permissions."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Delete the phenotype_taggers group.
    Group.objects.get(name='phenotype_taggers').delete()
    # Remove permissions to the tags models from the DCC groups.
    analysts_group = Group.objects.get(name='dcc_analysts')
    developers_group = Group.objects.get(name='dcc_developers')
    tag_permissions = Permission.objects.filter(content_type__app_label='tags')
    analysts_group.permissions.remove(*tag_permissions)
    developers_group.permissions.remove(*tag_permissions)


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
