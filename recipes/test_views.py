"""Test the functions and classes for recipes.views."""

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from core.utils import ViewsAutoLoginTestCase

from trait_browser.factories import SourceTraitFactory
from .factories import HarmonizationRecipeFactory, UnitRecipeFactory
from .models import HarmonizationRecipe, UnitRecipe
from .views import CreateHarmonizationRecipe, UpdateHarmonizationRecipe, HarmonizationRecipeDetail
from .views import CreateUnitRecipe, UpdateUnitRecipe, UnitRecipeDetail


class UnitRecipeViewsTestCase(ViewsAutoLoginTestCase):
    
    def test_create_unit_recipe(self):
        """Test that CreateUnitRecipe view can be navigated to."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_unit_recipe_creates_new_object(self):
        """Test that CreateUnitRecipe view can be used to create a new UnitRecipe.."""
        new_unit_name = 'Example study name, subcohort 5.'
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': new_unit_name,
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        url = reverse('recipes:unit:create')
        response = self.client.post(url, input)
        new_unit = UnitRecipe.objects.filter(name=new_unit_name)
        self.assertTrue(len(new_unit) == 1)
        new_unit = new_unit[0]
        self.assertRedirects(response, new_unit.get_absolute_url())
        self.assertIsInstance(new_unit, UnitRecipe)