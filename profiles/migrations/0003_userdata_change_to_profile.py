# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_userdata_taggable_studies'),
    ]

    operations = [
        migrations.RenameModel('UserData', 'Profile'),
        migrations.RenameField('SavedSearchMeta', 'user_data', 'profile'),
    ]
