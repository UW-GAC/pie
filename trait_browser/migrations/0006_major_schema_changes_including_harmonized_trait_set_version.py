# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0005_remove_component_harmonized_traits_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedUpdateReason',
            fields=[
                ('i_id', models.PositiveIntegerField(serialize=False, primary_key=True, verbose_name='allowed update reason id', db_column='i_id')),
                ('i_abbreviation', models.CharField(max_length=45, unique=True, verbose_name='abbreviation')),
                ('i_description', models.CharField(max_length=1000, verbose_name='description')),
            ],
        ),
        migrations.CreateModel(
            name='HarmonizedTraitSetVersion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(serialize=False, primary_key=True, verbose_name='harmonized trait set version id', db_column='i_id')),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_git_commit_hash', models.CharField(max_length=40, verbose_name='git commit hash')),
                ('i_harmonized_by', models.CharField(max_length=45, verbose_name='harmonized by')),
                ('i_is_deprecated', models.BooleanField(verbose_name='is deprecated?')),
                ('component_html_detail', models.TextField(default='')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='harmonizationunit',
            name='component_harmonized_trait_sets',
        ),
        migrations.RemoveField(
            model_name='harmonizationunit',
            name='harmonized_trait_set',
        ),
        migrations.RemoveField(
            model_name='harmonizedtraitset',
            name='component_html_detail',
        ),
        migrations.RemoveField(
            model_name='harmonizedtraitset',
            name='i_description',
        ),
        migrations.RemoveField(
            model_name='harmonizedtraitset',
            name='i_git_commit_hash',
        ),
        migrations.RemoveField(
            model_name='harmonizedtraitset',
            name='i_harmonized_by',
        ),
        migrations.RemoveField(
            model_name='harmonizedtraitset',
            name='i_version',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='i_date_visit_reviewed',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='i_dcc_description',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='i_is_medication_dataset',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='i_visit_code',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='i_visit_number',
        ),
        migrations.RemoveField(
            model_name='sourcedataset',
            name='subcohorts',
        ),
        migrations.RemoveField(
            model_name='sourcetrait',
            name='i_dbgap_description',
        ),
        migrations.RemoveField(
            model_name='sourcetrait',
            name='i_is_visit_column',
        ),
        migrations.RemoveField(
            model_name='sourcetrait',
            name='i_visit_number',
        ),
        migrations.AddField(
            model_name='globalstudy',
            name='i_topmed_abbreviation',
            field=models.CharField(default='', max_length=45, verbose_name='TOPMed abbreviation', blank=True),
        ),
        migrations.AddField(
            model_name='globalstudy',
            name='i_topmed_accession',
            field=models.PositiveIntegerField(null=True, unique=True, blank=True, verbose_name='TOPMed accession'),
        ),
        migrations.AddField(
            model_name='sourcetrait',
            name='i_are_values_truncated',
            field=models.NullBooleanField(default=None, verbose_name='are values truncated?'),
        ),
        migrations.AlterField(
            model_name='globalstudy',
            name='i_id',
            field=models.PositiveIntegerField(serialize=False, primary_key=True, verbose_name='global study id', db_column='i_id'),
        ),
        migrations.AlterField(
            model_name='globalstudy',
            name='i_name',
            field=models.CharField(max_length=200, unique=True, verbose_name='global study name'),
        ),
        migrations.AlterField(
            model_name='harmonizedtraitset',
            name='i_is_longitudinal',
            field=models.BooleanField(default=False, verbose_name='is longitudinal?'),
        ),
        migrations.AddField(
            model_name='harmonizedtraitsetversion',
            name='harmonized_trait_set',
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSet'),
        ),
        migrations.AddField(
            model_name='harmonizedtraitsetversion',
            name='update_reasons',
            field=models.ManyToManyField(to='trait_browser.AllowedUpdateReason'),
        ),
        migrations.RemoveField(
            model_name='harmonizedtrait',
            name='component_harmonized_trait_sets',
        ),
        migrations.RemoveField(
            model_name='harmonizedtrait',
            name='harmonized_trait_set',
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_harmonized_trait_set_versions',
            field=models.ManyToManyField(related_name='harmonized_component_of_harmonization_unit', to='trait_browser.HarmonizedTraitSetVersion'),
        ),
        migrations.AddField(
            model_name='harmonizationunit',
            name='harmonized_trait_set_version',
            field=models.ForeignKey(default=None, null=True, to='trait_browser.HarmonizedTraitSetVersion'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='component_harmonized_trait_set_versions',
            field=models.ManyToManyField(related_name='harmonized_component_of_harmonized_trait', to='trait_browser.HarmonizedTraitSetVersion'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='harmonized_trait_set_version',
            field=models.ForeignKey(default=None, null=True, to='trait_browser.HarmonizedTraitSetVersion'),
        ),
        migrations.AlterUniqueTogether(
            name='harmonizedtrait',
            unique_together=set([('harmonized_trait_set_version', 'i_trait_name')]),
        ),
    ]
