# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20161228_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harmonizationrecipe',
            name='target_name',
            field=models.CharField(validators=[django.core.validators.RegexValidator(message='Only letters, numbers, and underscores (_) are allowed.', regex='^[0-9a-zA-Z_]*$')], verbose_name='target phenotype variable name', max_length=50),
        ),
        migrations.AlterField(
            model_name='unitrecipe',
            name='batch_variables',
            field=models.ManyToManyField(blank=True, to='trait_browser.SourceTrait', related_name='units_as_batch_trait'),
        ),
    ]
