# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def set_permissions_for_profiles(apps, schema_editor):
    """Add permissions for the profiles.Profile model."""
    # In a migration from scratch, Django creates all of the models from all of the migrations, then runs
    # post-migrate signals that create the matching contenttypes and permissions for those models. So to
    # have the permissions available as needed, force the post-migrate signal to run now.
    # https://code.djangoproject.com/ticket/23422#comment:20
    db_alias = schema_editor.connection.alias
    try:
        emit_post_migrate_signal(2, False, 'default', db_alias)
    except TypeError:  # Django < 1.8
        emit_post_migrate_signal([], 2, False, 'default', db_alias)
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Give developers all permissions on the Profile model.
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.add(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile'))
    # Give analysts change permissions on the Profile model.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile', codename__startswith='change'))


def delete_permissions_for_profiles(apps, schema_editor):
    """Delete permissions for the profiles.Profile model."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Revoke all permissions on the Profile model from developers.
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.remove(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile'))
    # Revoke change permissions on the Profile model from analysts.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile', codename__startswith='change'))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_tags_groups_permissions'),
        ('profiles', '0004_profile_user_onetoonefield')
    ]

    operations = [
        migrations.RunPython(set_permissions_for_profiles, reverse_code=delete_permissions_for_profiles),
    ]
