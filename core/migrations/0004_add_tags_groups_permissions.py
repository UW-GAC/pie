# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def set_groups_and_permissions_for_tags(apps, schema_editor):
    """Create the phenotype_taggers group and add permissions for the tags models."""
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
    # Create the phenotype_taggers group.
    phenotype_taggers = Group.objects.get_or_create(name='phenotype_taggers')[0]
    phenotype_taggers.permissions.add(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='taggedtrait'))
    # Add permissions for tags to the dcc groups.
    tags_permissions = Permission.objects.filter(content_type__app_label='tags')
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.add(*tags_permissions)
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*tags_permissions)


def delete_groups_and_permissions_for_tags(apps, schema_editor):
    """Delete the phenotype_taggers group and remove permissions for the tags models."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Delete the phenotype_taggers group.
    phenotype_taggers = Group.objects.get(name='phenotype_taggers')
    phenotype_taggers.delete()
    # Remove permissions for tags to the dcc groups.
    tags_permissions = Permission.objects.filter(content_type__app_label='tags')
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.remove(*tags_permissions)
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*tags_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_recipe_groups_permissions'),
        ('tags', '0001_initial')
    ]

    operations = [
        migrations.RunPython(set_groups_and_permissions_for_tags, reverse_code=delete_groups_and_permissions_for_tags),
    ]
