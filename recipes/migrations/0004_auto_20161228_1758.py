# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20161228_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harmonizationrecipe',
            name='encoded_values',
            field=models.TextField(verbose_name='definition of encoded values for target variable', validators=[django.core.validators.RegexValidator(message='Invalid format for encoded values definitions.', regex='^(.*: .*\\n)*(.*: .*)$')], blank=True),
        ),
        migrations.AlterField(
            model_name='harmonizationrecipe',
            name='target_description',
            field=models.TextField(verbose_name='target phenotype variable description'),
        ),
    ]
