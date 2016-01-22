# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sourceencodedvalue',
            old_name='source_trait',
            new_name='trait',
        ),
    ]
