# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models


def set_groups_and_permissions_for_recipes(apps, schema_editor):
    """Create the recipe_submitters group and add permissions for the recipes models."""
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
    # Create the recipe_submitters group.
    recipe_submitters = Group.objects.get_or_create(name='recipe_submitters')[0]
    recipe_permissions = Permission.objects.filter(content_type__app_label='recipes')
    recipe_submitters.permissions.add(*recipe_permissions)
    # Add permissions for recipes to the dcc groups.
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.add(*recipe_permissions)
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*recipe_permissions)


def delete_groups_and_permissions_for_recipes(apps, schema_editor):
    """Delete the recipe_submitters group and remove permissions for the recipes models."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Delete the recipe_submitters group.
    recipe_submitters = Group.objects.get(name='recipe_submitters')
    recipe_submitters.delete()
    # Remove permissions for recipes to the dcc groups.
    recipe_permissions = Permission.objects.filter(content_type__app_label='recipes')
    developers = Group.objects.get(name='dcc_developers')
    developers.permissions.remove(*recipe_permissions)
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*recipe_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_default_groups'),
        ('recipes', '0001_initial')
    ]

    operations = [
        migrations.RunPython(set_groups_and_permissions_for_recipes,
                             reverse_code=delete_groups_and_permissions_for_recipes),
    ]
