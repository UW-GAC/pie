# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    replaces = [('profiles', '0001_initial'), ('profiles', '0002_auto_20170124_1433'), ('profiles', '0003_auto_20170125_1058')]

    dependencies = [
        ('trait_browser', '0004_savedsearch_times_saved'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSearches',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('saved_search_id', models.ForeignKey(to='trait_browser.SavedSearch')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='usersearches',
            unique_together=set([('user', 'saved_search_id')]),
        ),
        migrations.RenameField(
            model_name='usersearches',
            old_name='saved_search_id',
            new_name='search',
        ),
        migrations.AlterUniqueTogether(
            name='usersearches',
            unique_together=set([('user', 'search')]),
        ),
    ]
