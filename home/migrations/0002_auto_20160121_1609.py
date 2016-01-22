# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='homecontent',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='homecontent',
            name='order',
            field=models.PositiveIntegerField(default=1, db_index=True, editable=False),
            preserve_default=False,
        ),
    ]
