# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0001_squashed_0005_auto_20170125_0928'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Searches',
        ),
    ]
