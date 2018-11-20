# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def set_permissions_for_dccdecision(apps, schema_editor):
    """Add permissions for the tags.DCCDecision model."""
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
    dcc_decision_permissions = Permission.objects.filter(content_type__app_label='tags',
                                                         content_type__model='DCCDecision')
    # Give DCC analysts add and change permissions on the DCCDecision model.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*dcc_decision_permissions.exclude(codename__startswith='delete'))
    # Give DCC developers all permissions on the DCCDecision model.
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.add(*dcc_decision_permissions)


def delete_permissions_for_dccdecision(apps, schema_editor):
    """Delete permissions for the tags.DCCDecision model."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    dcc_decision_permissions = Permission.objects.filter(content_type__app_label='tags',
                                                         content_type__model='DCCDecision')
    # Remove all permissions for the DCCDecision model from analysts and developers.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*dcc_decision_permissions)
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.remove(*dcc_decision_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_studyresponse_groups_permissions'),
        ('tags', '0007_dccdecision')
    ]

    operations = [
        migrations.RunPython(set_permissions_for_dccdecision, reverse_code=delete_permissions_for_dccdecision),
    ]
