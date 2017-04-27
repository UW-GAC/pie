# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

# Created the .json fixture file like so:
# ./manage.py dumpdata --indent=2 auth.Group > core/fixtures/auth_group.json


def load_groups_from_fixture(apps, schema_editor):
    from django.core.management import call_command
    call_command('loaddata', 'auth_group')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_sites_data'),
        ('auth', '0001_initial')
    ]

    operations = [
        migrations.RunPython(load_groups_from_fixture),
    ]
