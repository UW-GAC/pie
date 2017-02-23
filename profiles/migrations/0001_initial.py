# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('trait_browser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedSearchMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Search',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('param_text', models.CharField(db_index=True, max_length=100)),
                ('search_count', models.IntegerField(default=1)),
                ('search_type', models.CharField(max_length=25)),
                ('param_studies', models.ManyToManyField(to='trait_browser.Study')),
            ],
            options={
                'verbose_name_plural': 'searches',
            },
        ),
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('saved_searches', models.ManyToManyField(through='profiles.SavedSearchMeta', to='profiles.Search')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='savedsearchmeta',
            name='search',
            field=models.ForeignKey(to='profiles.Search'),
        ),
        migrations.AddField(
            model_name='savedsearchmeta',
            name='user_data',
            field=models.ForeignKey(to='profiles.UserData'),
        ),
    ]
