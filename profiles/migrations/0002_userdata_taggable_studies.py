# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0006_major_schema_changes_including_harmonized_trait_set_version'),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdata',
            name='taggable_studies',
            field=models.ManyToManyField(to='trait_browser.Study'),
        ),
    ]
