# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-02 23:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0007_sourcedataset_add_datasetname_dbgapfilename'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='globalstudy',
            options={'verbose_name_plural': 'Global studies'},
        ),
    ]
