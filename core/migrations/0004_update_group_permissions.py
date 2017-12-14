# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


# Created the .json fixture file like so:
# ./manage.py dumpdata --indent=2 --natural-foreign auth.Group > core/fixtures/auth_group_0002.json


# Add permissions for tags to dcc_analysts and dcc_developers
# Add permissions for Profiles

def update_group_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Set up developer permissions.
    developers = Group.objects.get(name='dcc_developers')
    developer_perms = Permission.objects.exclude(
        content_type__app_label__in=['admin', 'auth', 'authtools', 'contenttypes', 'sites'])
    developers.permissions.add(*developer_perms)
    developers.permissions.remove(*Permission.objects.filter(
        content_type__app_label__in=['admin', 'auth', 'authtools', 'contenttypes', 'sites']))
    # Set up analyst permissions.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.add(*Permission.objects.filter(content_type__app_label='recipes'))
    analysts.permissions.add(*Permission.objects.filter(content_type__app_label='tags'))
    analysts.permissions.add(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile', codename__startswith='change'))
    # Set up phenotype_tagger permissions.
    taggers = Group.objects.get(name='phenotype_taggers')
    taggers.permissions.add(*Permission.objects.filter(
        content_type__app_label='tags', content_type__model='taggedtrait'))
    # Set up recipe submitter permissions.
    recipe_submitters = Group.objects.get(name='recipe_submitters')
    recipe_submitters.permissions.add(*Permission.objects.filter(content_type__app_label='recipes'))


def remove_group_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # # Set up developer permissions.
    # developers = Group.objects.get(name='dcc_developers')
    # developer_perms = Permission.objects.exclude(
    #     content_type__app_label__in=['admin', 'auth', 'authtools', 'contenttypes', 'sites'])
    # developers.permissions.remove(*developer_perms)
    # Set up analyst permissions.
    analysts = Group.objects.get(name='dcc_analysts')
    analysts.permissions.remove(*Permission.objects.filter(content_type__app_label='recipes'))
    analysts.permissions.remove(*Permission.objects.filter(content_type__app_label='tags'))
    analysts.permissions.remove(*Permission.objects.filter(
        content_type__app_label='profiles', content_type__model='profile', codename__startswith='change'))
    # Set up phenotype_tagger permissions.
    taggers = Group.objects.get(name='phenotype_taggers')
    taggers.permissions.remove(*Permission.objects.filter(content_type__app_label='tags'))
    # Set up recipe submitter permissions.
    recipe_submitters = Group.objects.get(name='recipe_submitters')
    recipe_submitters.permissions.remove(*Permission.objects.filter(content_type__app_label='recipes'))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_phenotype_taggers_auth_group'),
        ('auth', '0001_initial')
    ]

    operations = [
        migrations.RunPython(update_group_permissions, reverse_code=remove_group_permissions),
    ]
