# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-07-26 19:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0003_dccreview'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('status', models.IntegerField(choices=[(1, 'Agree'), (0, 'Disagree')])),
                ('comment', models.TextField(blank=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('dcc_review', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='study_response', to='tags.DCCReview')),
            ],
            options={
                'verbose_name': 'study response',
            },
        ),
    ]