# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trait_browser', '0003_harmonizedtraitset_i_is_demographic'),
    ]

    operations = [
        migrations.AddField(
            model_name='harmonizationunit',
            name='component_harmonized_trait_sets',
            field=models.ManyToManyField(to='trait_browser.HarmonizedTraitSet', related_name='harmonized_set_component_of_harmonization_unit'),
        ),
        migrations.AddField(
            model_name='harmonizedtrait',
            name='component_harmonized_trait_sets',
            field=models.ManyToManyField(to='trait_browser.HarmonizedTraitSet', related_name='harmonized_set_component_of_harmonized_trait'),
        ),
    ]
