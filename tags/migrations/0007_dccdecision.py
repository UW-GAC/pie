# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-19 18:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0006_change_creator_fields_to_protect_on_delete'),
    ]

    operations = [
        migrations.CreateModel(
            name='DCCDecision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('decision', models.IntegerField(choices=[(1, 'Confirm'), (0, 'Remove')])),
                ('comment', models.TextField(blank=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('dcc_review', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dcc_decision', to='tags.DCCReview')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
