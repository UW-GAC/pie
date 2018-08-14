# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def set_permissions_for_studyresponse(apps, schema_editor):
    """Add permissions for the tags.StudyResponse model."""
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
    study_response_permissions = Permission.objects.filter(content_type__app_label='tags',
                                                           content_type__model='StudyResponse')
    # Developers already have permissions for StudyResponse because they have blanket permissions for the tags app.
    # Give phenotype taggers add and change permissions on the StudyResponse model.
    taggers = Group.objects.get(name='phenotype_taggers')
    taggers.permissions.add(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='StudyResponse', codename__startswith='add'))
    taggers.permissions.add(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='StudyResponse', codename__startswith='change'))
    # Remove permissions for DCC analysts, which have blanket perimssions for the tags app.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*study_response_permissions)


def delete_permissions_for_studyresponse(apps, schema_editor):
    """Delete permissions for the tags.StudyResponse model."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    study_response_permissions = Permission.objects.filter(content_type__app_label='tags',
                                                           content_type__model='StudyResponse')
    # Revoke all permissions on the StudyResponse model for phenotype taggers.
    taggers = Group.objects.get(name='phenotype_taggers')
    taggers.permissions.remove(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='StudyResponse', codename__startswith='add'))
    taggers.permissions.remove(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='StudyResponse', codename__startswith='change'))
    # Add permissions for DCC analysts, who started with blanket perimssions for the tags app.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*study_response_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_dccreview_group_permissions'),
        ('tags', '0004_studyresponse')
    ]

    operations = [
        migrations.RunPython(set_permissions_for_studyresponse, reverse_code=delete_permissions_for_studyresponse),
    ]
