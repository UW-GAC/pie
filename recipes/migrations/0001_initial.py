# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('trait_browser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HarmonizationRecipe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(verbose_name='harmonization recipe name', max_length=255)),
                ('version', models.IntegerField(default=1)),
                ('target_name', models.CharField(verbose_name='target phenotype variable name', validators=[django.core.validators.RegexValidator(regex='^[0-9a-zA-Z_]*$', message='Only letters, numbers, and underscores (_) are allowed.')], max_length=50)),
                ('target_description', models.TextField(verbose_name='target phenotype variable description')),
                ('encoded_values', models.TextField(verbose_name='definition of encoded values for target variable', blank=True, validators=[django.core.validators.RegexValidator(regex='^(.*: .*\\n)*(.*: .*)$', message='Invalid format for encoded values definitions.')])),
                ('type', models.CharField(verbose_name='harmonization type', choices=[('unit_recode', 'recode variable for different units of measurement'), ('category_recode', 'recode variable for new encoded value category definitions'), ('formula', 'calculate variable from a formula'), ('other', 'other')], max_length=100)),
                ('measurement_unit', models.CharField(verbose_name='unit of measurement', max_length=100)),
                ('creator', models.ForeignKey(related_name='harmonization_recipes_created_by', to=settings.AUTH_USER_MODEL)),
                ('last_modifier', models.ForeignKey(related_name='harmonization_recipes_last_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UnitRecipe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('instructions', models.TextField(verbose_name='harmonization instructions')),
                ('version', models.IntegerField(default=1)),
                ('name', models.CharField(verbose_name='harmonization unit name', max_length=255)),
                ('age_variables', models.ManyToManyField(related_name='units_as_age_trait', to='trait_browser.SourceTrait')),
                ('batch_variables', models.ManyToManyField(blank=True, related_name='units_as_batch_trait', to='trait_browser.SourceTrait')),
                ('creator', models.ForeignKey(related_name='units_created_by', to=settings.AUTH_USER_MODEL)),
                ('last_modifier', models.ForeignKey(related_name='units_last_modified_by', to=settings.AUTH_USER_MODEL)),
                ('phenotype_variables', models.ManyToManyField(related_name='units_as_phenotype_trait', to='trait_browser.SourceTrait')),
            ],
            options={
                'verbose_name': 'harmonization unit recipe',
            },
        ),
        migrations.AddField(
            model_name='harmonizationrecipe',
            name='units',
            field=models.ManyToManyField(verbose_name='harmonization units', to='recipes.UnitRecipe'),
        ),
        migrations.AlterUniqueTogether(
            name='unitrecipe',
            unique_together=set([('creator', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='harmonizationrecipe',
            unique_together=set([('creator', 'name')]),
        ),
    ]
