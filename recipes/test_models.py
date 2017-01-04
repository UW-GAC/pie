"""Test functions and classes for recipes.models."""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from .factories import UnitRecipeFactory, HarmonizationRecipeFactory
from .models import HarmonizationRecipe, UnitRecipe
from core.factories import UserFactory


class UnitRecipeTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        unit_recipe = UnitRecipeFactory.create()
        self.assertIsInstance(UnitRecipe.objects.get(pk=unit_recipe.pk), UnitRecipe)

    def test_printing(self):
        """Test the custom __str__ method."""
        unit_recipe = UnitRecipeFactory.build()
        self.assertIsInstance(unit_recipe.__str__(), str)
    
    def test_timestamps_added(self):
        """Test that timestamps are added."""
        unit_recipe = UnitRecipeFactory.create()
        self.assertIsInstance(unit_recipe.created, datetime)
        self.assertIsInstance(unit_recipe.modified, datetime)


class HarmonizationRecipeTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a HarmonizationRecipe object."""
        harmonization_recipe = HarmonizationRecipeFactory.create()
        self.assertIsInstance(HarmonizationRecipe.objects.get(pk=harmonization_recipe.pk), HarmonizationRecipe)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonization_recipe = HarmonizationRecipeFactory.build()
        self.assertIsInstance(harmonization_recipe.__str__(), str)
    
    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonization_recipe = HarmonizationRecipeFactory.create()
        self.assertIsInstance(harmonization_recipe.created, datetime)
        self.assertIsInstance(harmonization_recipe.modified, datetime)
        
    def test_get_encoded_values_dict(self):
        """Test that a dict of encoded values is returned."""
        harmonization_recipe = HarmonizationRecipeFactory.create(encoded_values='1: red\r\n2: blue\r\n3: orange')
        expected = {'1': 'red', '2': 'blue', '3': 'orange'}
        self.assertEqual(harmonization_recipe.get_encoded_values_dict(), expected)
    
    def test_get_config(self):
        """ """
        pass
    
    def test_target_name_validation_spaces(self):
        """Test that the validator for target_name raises an error when spaces are in the given target name."""
        harmonization_recipe = HarmonizationRecipeFactory.build(name=' bad variable name ')
        with self.assertRaises(ValidationError):
            harmonization_recipe.full_clean()

    def test_target_name_validation_symbols(self):
        """Test that the validator for target_name raises an error when symbols are in the target name."""
        harmonization_recipe = HarmonizationRecipeFactory.build(name='variable@#')
        with self.assertRaises(ValidationError):
            harmonization_recipe.full_clean()

    def test_encoded_values_validation(self):
        """Test that the validator for encoded_values raises an error when the wrong separator is used."""
        harmonization_recipe = HarmonizationRecipeFactory.build(encoded_values='1- blue\r\n2- red')
        with self.assertRaises(ValidationError):
            harmonization_recipe.full_clean()