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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('lower_title', models.CharField(blank=True, max_length=255, unique=True)),
                ('description', models.TextField()),
                ('instructions', models.TextField()),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'phenotype tag',
            },
        ),
        migrations.CreateModel(
            name='TaggedTrait',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('recommended', models.BooleanField()),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL)),
                ('tag', models.ForeignKey(to='tags.Tag')),
                ('trait', models.ForeignKey(to='trait_browser.SourceTrait')),
            ],
            options={
                'verbose_name': 'tagged phenotype',
            },
        ),
        migrations.AddField(
            model_name='tag',
            name='traits',
            field=models.ManyToManyField(through='tags.TaggedTrait', to='trait_browser.SourceTrait'),
        ),
        migrations.AlterUniqueTogether(
            name='taggedtrait',
            unique_together=set([('trait', 'tag')]),
        ),
    ]
