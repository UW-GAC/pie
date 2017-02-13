# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalStudy',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='global study id', primary_key=True, serialize=False, db_column='study_id')),
                ('i_name', models.CharField(max_length=200, verbose_name='global study name')),
            ],
            options={
                'verbose_name_plural': 'GlobalStudies',
            },
        ),
        migrations.CreateModel(
            name='HarmonizedTrait',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_trait_id', models.PositiveIntegerField(verbose_name='phenotype id', primary_key=True, serialize=False, db_column='i_trait_id')),
                ('i_trait_name', models.CharField(max_length=100, verbose_name='phenotype name')),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_data_type', models.CharField(max_length=45, verbose_name='data type')),
                ('i_unit', models.CharField(max_length=100, blank=True, verbose_name='unit')),
                ('i_is_unique_key', models.BooleanField(verbose_name='is unique key?')),
                ('trait_flavor_name', models.CharField(max_length=150)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HarmonizedTraitEncodedValue',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_category', models.CharField(max_length=45, verbose_name='category')),
                ('i_value', models.CharField(max_length=1000, verbose_name='value')),
                ('harmonized_trait', models.ForeignKey(to='trait_browser.HarmonizedTrait')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HarmonizedTraitSet',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='harmonized trait set id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_trait_set_name', models.CharField(max_length=45, verbose_name='trait set name')),
                ('i_flavor', models.PositiveIntegerField(verbose_name='flavor')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_description', models.CharField(max_length=1000, verbose_name='description')),
                ('component_harmonized_traits', models.ManyToManyField(to='trait_browser.HarmonizedTrait')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceDataset',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='dataset id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_accession', models.PositiveIntegerField(verbose_name='dataset accession')),
                ('i_version', models.PositiveIntegerField(verbose_name='dataset version')),
                ('i_visit_code', models.CharField(max_length=100, blank=True, verbose_name='visit code')),
                ('i_visit_number', models.CharField(max_length=45, blank=True, verbose_name='visit number')),
                ('i_is_subject_file', models.BooleanField(verbose_name='is subject file?')),
                ('i_study_subject_column', models.CharField(max_length=45, blank=True, verbose_name='study subject column name')),
                ('i_is_medication_dataset', models.NullBooleanField(verbose_name='is medication dataset?')),
                ('i_dbgap_description', models.TextField(blank=True, verbose_name='dbGaP description')),
                ('i_dcc_description', models.TextField(blank=True, verbose_name='DCC description')),
                ('pht_version_string', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceStudyVersion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='source study version id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_participant_set', models.PositiveIntegerField(verbose_name='participant set')),
                ('i_dbgap_date', models.DateTimeField(verbose_name='dbGaP date')),
                ('i_is_prerelease', models.BooleanField(verbose_name='is prerelease?')),
                ('i_is_deprecated', models.BooleanField(verbose_name='is deprecated?')),
                ('phs_version_string', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceTrait',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_trait_id', models.PositiveIntegerField(verbose_name='phenotype id', primary_key=True, serialize=False, db_column='i_trait_id')),
                ('i_trait_name', models.CharField(max_length=100, verbose_name='phenotype name')),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_detected_type', models.CharField(max_length=100, blank=True, verbose_name='detected type')),
                ('i_dbgap_type', models.CharField(max_length=100, blank=True, verbose_name='dbGaP type')),
                ('i_visit_number', models.CharField(max_length=45, blank=True, verbose_name='visit number')),
                ('i_dbgap_variable_accession', models.PositiveIntegerField(verbose_name='dbGaP variable accession')),
                ('i_dbgap_variable_version', models.PositiveIntegerField(verbose_name='dbGaP variable version')),
                ('i_dbgap_comment', models.TextField(blank=True, verbose_name='dbGaP comment')),
                ('i_dbgap_unit', models.CharField(max_length=45, blank=True, verbose_name='dbGaP unit')),
                ('i_n_records', models.PositiveIntegerField(null=True, blank=True, verbose_name='n records')),
                ('i_n_missing', models.PositiveIntegerField(null=True, blank=True, verbose_name='n missing')),
                ('i_is_visit_column', models.NullBooleanField(verbose_name='is visit column?')),
                ('i_is_unique_key', models.NullBooleanField(verbose_name='is unique key?')),
                ('study_accession', models.CharField(max_length=20)),
                ('dataset_accession', models.CharField(max_length=20)),
                ('variable_accession', models.CharField(max_length=23)),
                ('dbgap_study_link', models.URLField()),
                ('dbgap_variable_link', models.URLField()),
                ('dbgap_dataset_link', models.URLField()),
                ('source_dataset', models.ForeignKey(to='trait_browser.SourceDataset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceTraitEncodedValue',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_category', models.CharField(max_length=45, verbose_name='category')),
                ('i_value', models.CharField(max_length=1000, verbose_name='value')),
                ('source_trait', models.ForeignKey(to='trait_browser.SourceTrait')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_accession', models.PositiveIntegerField(verbose_name='study accession', primary_key=True, serialize=False, db_column='i_accession')),
                ('i_study_name', models.CharField(max_length=200, verbose_name='study name')),
                ('phs', models.CharField(max_length=9)),
                ('dbgap_latest_version_link', models.CharField(max_length=200)),
                ('global_study', models.ForeignKey(to='trait_browser.GlobalStudy')),
            ],
            options={
                'verbose_name_plural': 'Studies',
            },
        ),
        migrations.CreateModel(
            name='Subcohort',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='id', primary_key=True, serialize=False, db_column='i_id')),
                ('i_name', models.CharField(max_length=45, verbose_name='name')),
                ('study', models.ForeignKey(to='trait_browser.Study')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='sourcestudyversion',
            name='study',
            field=models.ForeignKey(to='trait_browser.Study'),
        ),
        migrations.AddField(
            model_name='sourcedataset',
            name='source_study_version',
            field=models.ForeignKey(to='trait_browser.SourceStudyVersion'),
        ),
        migrations.AddField(
            model_name='sourcedataset',
            name='subcohorts',
            field=models.ManyToManyField(to='trait_browser.Subcohort'),
        ),
        migrations.AddField(
            model_name='harmonizedtraitset',
            name='component_source_traits',
            field=models.ManyToManyField(to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='harmonized_trait_set',
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSet'),
        ),
    ]
