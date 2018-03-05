# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0006_major_schema_changes_including_harmonized_trait_set_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcedataset',
            name='dataset_name',
            field=models.CharField(max_length=255, default=''),
        ),
        migrations.AddField(
            model_name='sourcedataset',
            name='dbgap_filename',
            field=models.CharField(max_length=255, default=''),
        ),
    ]
