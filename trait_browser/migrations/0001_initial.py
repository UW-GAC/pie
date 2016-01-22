# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SourceEncodedValue',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('category', models.CharField(max_length=45)),
                ('value', models.CharField(max_length=100)),
                ('web_date_added', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceTrait',
            fields=[
                ('trait_id', models.IntegerField(db_column='trait_id', primary_key=True, serialize=False)),
                ('trait_name', models.CharField(max_length=100)),
                ('short_description', models.CharField(max_length=500)),
                ('data_type', models.CharField(choices=[('string', 'string'), ('integer', 'integer'), ('encoded', 'encoded'), ('decimal', 'decimal')], max_length=7)),
                ('web_date_added', models.DateTimeField(auto_now_add=True)),
                ('dbgap_study_id', models.CharField(max_length=45)),
                ('dbgap_study_version', models.IntegerField()),
                ('dbgap_dataset_id', models.CharField(max_length=45)),
                ('dbgap_dataset_version', models.IntegerField()),
                ('dbgap_variable_id', models.CharField(max_length=45)),
                ('dbgap_variable_version', models.IntegerField()),
                ('dbgap_comment', models.CharField(max_length=1000, null=True)),
                ('dbgap_unit', models.CharField(max_length=45, null=True)),
                ('dbgap_participant_set', models.IntegerField()),
                ('dbgap_date_created', models.DateTimeField(null=True)),
                ('dataset_description', models.CharField(max_length=1000, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='sourceencodedvalue',
            name='source_trait',
            field=models.ForeignKey(to='trait_browser.SourceTrait'),
        ),
    ]
