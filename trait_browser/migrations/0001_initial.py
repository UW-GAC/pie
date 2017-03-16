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
                ('i_id', models.PositiveIntegerField(verbose_name='global study id', db_column='study_id', primary_key=True, serialize=False)),
                ('i_name', models.CharField(verbose_name='global study name', max_length=200)),
            ],
            options={
                'verbose_name_plural': 'GlobalStudies',
            },
        ),
        migrations.CreateModel(
            name='HarmonizationUnit',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='harmonization unit id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_tag', models.CharField(verbose_name='tag', max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HarmonizedTrait',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_trait_id', models.PositiveIntegerField(verbose_name='phenotype id', db_column='i_trait_id', primary_key=True, serialize=False)),
                ('i_trait_name', models.CharField(verbose_name='phenotype name', max_length=100)),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_data_type', models.CharField(verbose_name='data type', max_length=45)),
                ('i_unit', models.CharField(blank=True, verbose_name='unit', max_length=100)),
                ('i_has_batch', models.BooleanField(verbose_name='has batch?')),
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
                ('i_id', models.PositiveIntegerField(verbose_name='id', db_column='i_id', primary_key=True, serialize=False)),
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
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='harmonized trait set id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_trait_set_name', models.CharField(verbose_name='trait set name', max_length=45)),
                ('i_flavor', models.PositiveIntegerField(verbose_name='flavor')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_description', models.CharField(verbose_name='description', max_length=1000)),
                ('i_harmonized_by', models.CharField(verbose_name='harmonized by', max_length=45)),
                ('i_git_commit_hash', models.CharField(verbose_name='git commit hash', max_length=40)),
                ('i_is_longitudinal', models.BooleanField(verbose_name='is longitudinal?')),
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
                ('i_id', models.PositiveIntegerField(verbose_name='dataset id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_accession', models.PositiveIntegerField(verbose_name='dataset accession')),
                ('i_version', models.PositiveIntegerField(verbose_name='dataset version')),
                ('i_visit_code', models.CharField(blank=True, verbose_name='visit code', max_length=100)),
                ('i_visit_number', models.CharField(blank=True, verbose_name='visit number', max_length=45)),
                ('i_is_subject_file', models.BooleanField(verbose_name='is subject file?')),
                ('i_study_subject_column', models.CharField(blank=True, verbose_name='study subject column name', max_length=45)),
                ('i_is_medication_dataset', models.NullBooleanField(verbose_name='is medication dataset?')),
                ('i_dbgap_date_created', models.DateTimeField(blank=True, verbose_name='dbGaP date created', null=True)),
                ('i_date_visit_reviewed', models.DateTimeField(blank=True, verbose_name='date visit was reviewed', null=True)),
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
                ('i_id', models.PositiveIntegerField(verbose_name='source study version id', db_column='i_id', primary_key=True, serialize=False)),
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
                ('i_trait_id', models.PositiveIntegerField(verbose_name='phenotype id', db_column='i_trait_id', primary_key=True, serialize=False)),
                ('i_trait_name', models.CharField(verbose_name='phenotype name', max_length=100)),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_detected_type', models.CharField(blank=True, verbose_name='detected type', max_length=100)),
                ('i_dbgap_type', models.CharField(blank=True, verbose_name='dbGaP type', max_length=100)),
                ('i_visit_number', models.CharField(blank=True, verbose_name='visit number', max_length=45)),
                ('i_dbgap_variable_accession', models.PositiveIntegerField(verbose_name='dbGaP variable accession')),
                ('i_dbgap_variable_version', models.PositiveIntegerField(verbose_name='dbGaP variable version')),
                ('i_dbgap_description', models.TextField(verbose_name='dbGaP description')),
                ('i_dbgap_comment', models.TextField(blank=True, verbose_name='dbGaP comment')),
                ('i_dbgap_unit', models.CharField(blank=True, verbose_name='dbGaP unit', max_length=45)),
                ('i_n_records', models.PositiveIntegerField(blank=True, verbose_name='n records', null=True)),
                ('i_n_missing', models.PositiveIntegerField(blank=True, verbose_name='n missing', null=True)),
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
                ('i_id', models.PositiveIntegerField(verbose_name='id', db_column='i_id', primary_key=True, serialize=False)),
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
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_accession', models.PositiveIntegerField(verbose_name='study accession', db_column='i_accession', primary_key=True, serialize=False)),
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
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_name', models.CharField(verbose_name='name', max_length=45)),
                ('global_study', models.ForeignKey(to='trait_browser.GlobalStudy')),
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
            model_name='harmonizedtrait',
            name='component_batch_traits',
            field=models.ManyToManyField(related_name='batch_component_of_harmonized_trait', to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='component_harmonized_traits',
            field=models.ManyToManyField(related_name='harmonized_component_of_harmonized_trait', to='trait_browser.HarmonizedTrait'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='component_source_traits',
            field=models.ManyToManyField(related_name='source_component_of_harmonized_trait', to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='harmonization_units',
            field=models.ManyToManyField(to='trait_browser.HarmonizationUnit'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='harmonized_trait_set',
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSet'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_age_traits',
            field=models.ManyToManyField(related_name='age_component_of_harmonization_unit', to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_batch_traits',
            field=models.ManyToManyField(related_name='batch_component_of_harmonization_unit', to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_harmonized_traits',
            field=models.ManyToManyField(related_name='harmonized_component_of_harmonization_unit', to='trait_browser.HarmonizedTrait'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_source_traits',
            field=models.ManyToManyField(related_name='source_component_of_harmonization_unit', to='trait_browser.SourceTrait'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='harmonized_trait_set',
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSet'),
        ),
    ]
