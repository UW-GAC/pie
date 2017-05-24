# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_component_harmonized_trait_to_component_harmonized_trait_set(apps, schema_editor):
    '''Copy data from the old M2M field to the new one.
    
    topmed_pheno replaced component_harmonized_trait table with
    component_harmonized_trait_set table. So copy data from the old matching
    M2M field to the new one.
    '''
    HarmonizationUnit = apps.get_model('trait_browser', 'HarmonizationUnit')
    # Copy data in the HarmonizationUnit model.
    for hunit in HarmonizationUnit.objects.all():
        for htrait in hunit.component_harmonized_traits.all():
            hunit.component_harmonized_trait_sets.add(htrait.harmonized_trait_set)
        hunit.save()
    # Copy data in the HarmonizedTrait model.
    HarmonizedTrait = apps.get_model('trait_browser', 'HarmonizedTrait')
    for target_htrait in HarmonizedTrait.objects.all():
        for htrait in target_htrait.component_harmonized_traits.all():
            target_htrait.component_harmonized_trait_sets.add(htrait.harmonized_trait_set)
        target_htrait.save()


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0004_add_component_harmonized_trait_sets'),
    ]

    operations = [
        migrations.RunPython(copy_component_harmonized_trait_to_component_harmonized_trait_set)
    ]
