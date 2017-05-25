# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0004_add_component_harmonized_trait_sets'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='harmonizationunit',
            name='component_harmonized_traits',
        ),
        migrations.RemoveField(
            model_name='harmonizedtrait',
            name='component_harmonized_traits',
        ),
    ]
