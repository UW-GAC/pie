# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def create_default_groups(apps, schema_editor):
    """Create groups for DCC analysts and developers."""
    # In a migration from scratch, Django creates all of the models from all of the migrations, then runs
    # post-migrate signals that create the matching contenttypes and permissions for those models. So to
    # have the permissions available as needed, force the post-migrate signal to run now.
    # https://code.djangoproject.com/ticket/23422#comment:20
    db_alias = schema_editor.connection.alias
    try:
        emit_post_migrate_signal(2, False, db_alias)
    except TypeError:
        # Django < 1.9
        try:
            # Django 1.8
            emit_post_migrate_signal(2, False, 'default', db_alias)
        except TypeError:  # Django < 1.8
            emit_post_migrate_signal([], 2, False, 'default', db_alias)
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    custom_user_app = settings.AUTH_USER_MODEL.split('.')[0]
    # Create the dcc_analysts group.
    analysts = Group.objects.get_or_create(name='dcc_analysts')[0]
    # Since only trait_browser is installed so far, there are no models to give permission to.
    # Create the dcc_developers group and add permissions for flatpages.
    developers = Group.objects.get_or_create(name='dcc_developers')[0]
    flatpages_permissions = Permission.objects.filter(
        content_type__app_label='flatpages', content_type__model='flatpage')
    developers.permissions.add(*flatpages_permissions)


def delete_default_groups(apps, schema_editor):
    """Delete the default DCC developer and analyst groups."""
    Group = apps.get_model('auth', 'Group')
    # Delete the dcc_analysts group.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.delete()
    # Delete the dcc_developers group.
    developers = Group.objects.get(name='dcc_developers')
    developers.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_sites_data'),
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flatpages', '0001_initial'),
        ('trait_browser', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_groups, reverse_code=delete_default_groups),
    ]
