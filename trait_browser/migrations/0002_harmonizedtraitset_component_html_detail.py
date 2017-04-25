# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='harmonizedtraitset',
            name='component_html_detail',
            field=models.TextField(default=''),
        ),
    ]
