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
                ('i_id', models.PositiveIntegerField(verbose_name='allowed update reason id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_abbreviation', models.CharField(verbose_name='abbreviation', unique=True, max_length=45)),
                ('i_description', models.CharField(verbose_name='description', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='HarmonizedTraitSetVersion',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('i_date_added', models.DateTimeField()),
                ('i_date_changed', models.DateTimeField()),
                ('i_id', models.PositiveIntegerField(verbose_name='harmonized trait set version id', db_column='i_id', primary_key=True, serialize=False)),
                ('i_version', models.PositiveIntegerField(verbose_name='version')),
                ('i_git_commit_hash', models.CharField(verbose_name='git commit hash', max_length=40)),
                ('i_harmonized_by', models.CharField(verbose_name='harmonized by', max_length=45)),
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
            field=models.CharField(verbose_name='TOPMed abbreviation', blank=True, default='', max_length=45),
        ),
        migrations.AddField(
            model_name='globalstudy',
            name='i_topmed_accession',
            field=models.PositiveIntegerField(verbose_name='TOPMed accession', null=True, blank=True, unique=True),
        ),
        migrations.AddField(
            model_name='sourcetrait',
            name='i_are_values_truncated',
            field=models.NullBooleanField(verbose_name='are values truncated?', default=None),
        ),
        migrations.AlterField(
            model_name='globalstudy',
            name='i_name',
            field=models.CharField(verbose_name='global study name', unique=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='harmonizedtraitset',
            name='i_is_longitudinal',
            field=models.BooleanField(verbose_name='is longitudinal?', default=False),
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
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSetVersion', default=None, null=True),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='component_harmonized_trait_set_versions',
            field=models.ManyToManyField(related_name='harmonized_component_of_harmonized_trait', to='trait_browser.HarmonizedTraitSetVersion'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='harmonized_trait_set_version',
            field=models.ForeignKey(to='trait_browser.HarmonizedTraitSetVersion', default=None, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='harmonizedtrait',
            unique_together=set([('harmonized_trait_set_version', 'i_trait_name')]),
        ),
    ]
