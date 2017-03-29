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
                ('i_id', models.PositiveIntegerField(db_column='study_id', verbose_name='global study id', primary_key=True, serialize=False)),
                ('i_name', models.CharField(max_length=200, verbose_name='global study name')),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='harmonization unit id', primary_key=True, serialize=False)),
                ('i_tag', models.CharField(max_length=100, verbose_name='tag')),
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
                ('i_trait_id', models.PositiveIntegerField(db_column='i_trait_id', verbose_name='phenotype id', primary_key=True, serialize=False)),
                ('i_trait_name', models.CharField(max_length=100, verbose_name='phenotype name')),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_data_type', models.CharField(max_length=45, verbose_name='data type')),
                ('i_unit', models.CharField(max_length=100, verbose_name='unit', blank=True)),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='id', primary_key=True, serialize=False)),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='harmonized trait set id', primary_key=True, serialize=False)),
                ('i_trait_set_name', models.CharField(max_length=45, verbose_name='trait set name')),
                ('i_flavor', models.PositiveIntegerField(verbose_name='flavor')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_description', models.CharField(max_length=1000, verbose_name='description')),
                ('i_harmonized_by', models.CharField(max_length=45, verbose_name='harmonized by')),
                ('i_git_commit_hash', models.CharField(max_length=40, verbose_name='git commit hash')),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='dataset id', primary_key=True, serialize=False)),
                ('i_accession', models.PositiveIntegerField(verbose_name='dataset accession')),
                ('i_version', models.PositiveIntegerField(verbose_name='dataset version')),
                ('i_visit_code', models.CharField(max_length=100, verbose_name='visit code', blank=True)),
                ('i_visit_number', models.CharField(max_length=45, verbose_name='visit number', blank=True)),
                ('i_is_subject_file', models.BooleanField(verbose_name='is subject file?')),
                ('i_study_subject_column', models.CharField(max_length=45, verbose_name='study subject column name', blank=True)),
                ('i_is_medication_dataset', models.NullBooleanField(default=None, verbose_name='is medication dataset?')),
                ('i_dbgap_date_created', models.DateTimeField(verbose_name='dbGaP date created', blank=True, null=True)),
                ('i_date_visit_reviewed', models.DateTimeField(verbose_name='date visit was reviewed', blank=True, null=True)),
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
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='source study version id', primary_key=True, serialize=False)),
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
                ('i_trait_id', models.PositiveIntegerField(db_column='i_trait_id', verbose_name='phenotype id', primary_key=True, serialize=False)),
                ('i_trait_name', models.CharField(max_length=100, verbose_name='phenotype name')),
                ('i_description', models.TextField(verbose_name='description')),
                ('i_detected_type', models.CharField(max_length=100, verbose_name='detected type', blank=True)),
                ('i_dbgap_type', models.CharField(max_length=100, verbose_name='dbGaP type', blank=True)),
                ('i_visit_number', models.CharField(max_length=45, verbose_name='visit number', blank=True)),
                ('i_dbgap_variable_accession', models.PositiveIntegerField(verbose_name='dbGaP variable accession')),
                ('i_dbgap_variable_version', models.PositiveIntegerField(verbose_name='dbGaP variable version')),
                ('i_dbgap_description', models.TextField(verbose_name='dbGaP description')),
                ('i_dbgap_comment', models.TextField(verbose_name='dbGaP comment', blank=True)),
                ('i_dbgap_unit', models.CharField(max_length=45, verbose_name='dbGaP unit', blank=True)),
                ('i_n_records', models.PositiveIntegerField(verbose_name='n records', blank=True, null=True)),
                ('i_n_missing', models.PositiveIntegerField(verbose_name='n missing', blank=True, null=True)),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='id', primary_key=True, serialize=False)),
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
                ('i_accession', models.PositiveIntegerField(db_column='i_accession', verbose_name='study accession', primary_key=True, serialize=False)),
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
                ('i_id', models.PositiveIntegerField(db_column='i_id', verbose_name='id', primary_key=True, serialize=False)),
                ('i_name', models.CharField(max_length=45, verbose_name='name')),
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
