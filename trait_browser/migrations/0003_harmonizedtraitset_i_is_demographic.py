# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0002_harmonizedtraitset_component_html_detail'),
    ]

    operations = [
        migrations.AddField(
            model_name='harmonizedtraitset',
            name='i_is_demographic',
            field=models.BooleanField(default=False, verbose_name='is_demographic'),
        ),
    ]
