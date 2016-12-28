# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='harmonizationrecipe',
            unique_together=set([('creator', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='unitrecipe',
            unique_together=set([('creator', 'name')]),
        ),
    ]
