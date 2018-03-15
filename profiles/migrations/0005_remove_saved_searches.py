# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_profile_user_onetoonefield'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='savedsearchmeta',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='savedsearchmeta',
            name='search',
        ),
        migrations.RemoveField(
            model_name='search',
            name='param_studies',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='saved_searches',
        ),
        migrations.DeleteModel(
            name='SavedSearchMeta',
        ),
        migrations.DeleteModel(
            name='Search',
        ),
    ]
