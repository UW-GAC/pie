# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0006_major_schema_changes_including_harmonized_trait_set_version'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=500)),
                ('lower_title', models.CharField(max_length=500, blank=True, unique=True)),
                ('description', models.TextField()),
                ('instructions', models.TextField()),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name': 'phenotype tag',
            },
        ),
        migrations.CreateModel(
            name='TaggedTrait',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('recommended', models.BooleanField()),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True)),
                ('tag', models.ForeignKey(to='tags.Tag')),
                ('trait', models.ForeignKey(to='trait_browser.SourceTrait')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='tag',
            name='traits',
            field=models.ManyToManyField(to='trait_browser.SourceTrait', through='tags.TaggedTrait'),
        ),
    ]
