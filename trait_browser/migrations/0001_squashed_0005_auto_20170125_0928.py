# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('trait_browser', '0001_initial'), ('trait_browser', '0002_savedsearch'), ('trait_browser', '0003_auto_20170124_1203'), ('trait_browser', '0004_savedsearch_times_saved'), ('trait_browser', '0005_auto_20170125_0928')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalStudy',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='study_id', serialize=False, verbose_name='global study id')),
                ('i_name', models.CharField(verbose_name='global study name', max_length=200)),
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
                ('i_trait_id', models.PositiveIntegerField(primary_key=True, db_column='i_trait_id', serialize=False, verbose_name='phenotype id')),
                ('i_trait_name', models.CharField(verbose_name='phenotype name', max_length=100)),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_data_type', models.CharField(verbose_name='data type', max_length=45)),
                ('i_unit', models.CharField(verbose_name='unit', max_length=100, blank=True)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='id')),
                ('i_category', models.CharField(verbose_name='category', max_length=45)),
                ('i_value', models.CharField(verbose_name='value', max_length=1000)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='harmonized trait set id')),
                ('i_trait_set_name', models.CharField(verbose_name='trait set name', max_length=45)),
                ('i_flavor', models.PositiveIntegerField(verbose_name='flavor')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_description', models.CharField(verbose_name='description', max_length=1000)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='dataset id')),
                ('i_accession', models.PositiveIntegerField(verbose_name='dataset accession')),
                ('i_version', models.PositiveIntegerField(verbose_name='dataset version')),
                ('i_visit_code', models.CharField(verbose_name='visit code', max_length=100, blank=True)),
                ('i_visit_number', models.CharField(verbose_name='visit number', max_length=45, blank=True)),
                ('i_is_subject_file', models.BooleanField(verbose_name='is subject file?')),
                ('i_study_subject_column', models.CharField(verbose_name='study subject column name', max_length=45, blank=True)),
                ('i_is_medication_dataset', models.NullBooleanField(verbose_name='is medication dataset?')),
                ('i_dbgap_description', models.TextField(verbose_name='dbGaP description', blank=True)),
                ('i_dcc_description', models.TextField(verbose_name='DCC description', blank=True)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='source study version id')),
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
                ('i_trait_id', models.PositiveIntegerField(primary_key=True, db_column='i_trait_id', serialize=False, verbose_name='phenotype id')),
                ('i_trait_name', models.CharField(verbose_name='phenotype name', max_length=100)),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_detected_type', models.CharField(verbose_name='detected type', max_length=100, blank=True)),
                ('i_dbgap_type', models.CharField(verbose_name='dbGaP type', max_length=100, blank=True)),
                ('i_visit_number', models.CharField(verbose_name='visit number', max_length=45, blank=True)),
                ('i_dbgap_variable_accession', models.PositiveIntegerField(verbose_name='dbGaP variable accession')),
                ('i_dbgap_variable_version', models.PositiveIntegerField(verbose_name='dbGaP variable version')),
                ('i_dbgap_comment', models.TextField(verbose_name='dbGaP comment', blank=True)),
                ('i_dbgap_unit', models.CharField(verbose_name='dbGaP unit', max_length=45, blank=True)),
                ('i_n_records', models.PositiveIntegerField(null=True, verbose_name='n records', blank=True)),
                ('i_n_missing', models.PositiveIntegerField(null=True, verbose_name='n missing', blank=True)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='id')),
                ('i_category', models.CharField(verbose_name='category', max_length=45)),
                ('i_value', models.CharField(verbose_name='value', max_length=1000)),
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
                ('i_accession', models.PositiveIntegerField(primary_key=True, db_column='i_accession', serialize=False, verbose_name='study accession')),
                ('i_study_name', models.CharField(verbose_name='study name', max_length=200)),
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
                ('i_id', models.PositiveIntegerField(primary_key=True, db_column='i_id', serialize=False, verbose_name='id')),
                ('i_name', models.CharField(verbose_name='name', max_length=45)),
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
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('search_string', models.CharField(max_length=100, db_index=True)),
                ('selected_studies', models.CommaSeparatedIntegerField(null=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='savedsearch',
            unique_together=set([('search_string', 'selected_studies')]),
        ),
        migrations.AddField(
            model_name='savedsearch',
            name='times_saved',
            field=models.IntegerField(default=1),
        ),
        migrations.RenameModel(
            old_name='SavedSearch',
            new_name='Searches',
        ),
    ]
