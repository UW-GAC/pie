# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-12 01:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0003_dccreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='taggedtrait',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
