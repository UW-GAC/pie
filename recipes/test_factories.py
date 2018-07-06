"""Test the factory functions, which are used for testing."""

from django.test import TestCase


from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory

from . import models
from . import factories


class UnitRecipeFactoryTest(TestCase):

    def test_unit_recipe_factory_build(self):
        """A UnitRecipe instance is returned by UnitRecipeFactory.build()."""
        unit_recipe = factories.UnitRecipeFactory.build()
        self.assertIsInstance(unit_recipe, models.UnitRecipe)

    def test_unit_recipe_factory_create(self):
        """A UnitRecipe instance is returned by UnitRecipeFactory.create()."""
        unit_recipe = factories.UnitRecipeFactory.create()
        self.assertIsInstance(unit_recipe, models.UnitRecipe)

    def test_unit_recipe_factory_build_batch(self):
        """A UnitRecipe instance is returned by UnitRecipeFactory.build_batch(5)."""
        unit_recipes = factories.UnitRecipeFactory.build_batch(5)
        for one in unit_recipes:
            self.assertIsInstance(one, models.UnitRecipe)

    def test_unit_recipe_factory_create_batch(self):
        """A UnitRecipe instance is returned by UnitRecipeFactory.create_batch(5)."""
        unit_recipes = factories.UnitRecipeFactory.create_batch(5)
        for one in unit_recipes:
            self.assertIsInstance(one, models.UnitRecipe)

    def test_unit_recipe_factory_create_with_variables(self):
        """Passing variables of all kinds to UnitRecipeFactory creates a UnitRecipe with non-empty variables."""
        age_vars = SourceTraitFactory.create_batch(
            2, source_dataset__source_study_version__study__global_study__i_id=1)
        batch_vars = SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        pheno_vars = SourceTraitFactory.create_batch(
            6, source_dataset__source_study_version__study__global_study__i_id=1)
        unit_recipe = factories.UnitRecipeFactory.create(
            age_variables=age_vars, batch_variables=batch_vars, phenotype_variables=pheno_vars)
        self.assertEqual(age_vars, list(unit_recipe.age_variables.all()))
        self.assertEqual(batch_vars, list(unit_recipe.batch_variables.all()))
        self.assertEqual(pheno_vars, list(unit_recipe.phenotype_variables.all()))


class HarmonizationRecipeFactoryTest(TestCase):

    def test_harmonization_recipe_factory_build(self):
        """A HarmonizationRecipe instance is returned by HarmonizationRecipeFactory.build()."""
        harmonization_recipe = factories.HarmonizationRecipeFactory.build()
        self.assertIsInstance(harmonization_recipe, models.HarmonizationRecipe)

    def test_harmonization_recipe_factory_create(self):
        """A HarmonizationRecipe instance is returned by HarmonizationRecipeFactory.create()."""
        harmonization_recipe = factories.HarmonizationRecipeFactory.create()
        self.assertIsInstance(harmonization_recipe, models.HarmonizationRecipe)

    def test_harmonization_recipe_factory_build_batch(self):
        """A HarmonizationRecipe instance is returned by HarmonizationRecipeFactory.build_batch(5)."""
        harmonization_recipes = factories.HarmonizationRecipeFactory.build_batch(5)
        for one in harmonization_recipes:
            self.assertIsInstance(one, models.HarmonizationRecipe)

    def test_harmonization_recipe_factory_create_batch(self):
        """A HarmonizationRecipe instance is returned by HarmonizationRecipeFactory.create_batch(5)."""
        harmonization_recipes = factories.HarmonizationRecipeFactory.create_batch(5)
        for one in harmonization_recipes:
            self.assertIsInstance(one, models.HarmonizationRecipe)

    def test_harmonization_recipe_factory_create_with_units(self):
        """Passing UnitRecipes to HarmonizationRecipeFactory creates a HarmonizationRecipe with non-empty units."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(8, creator=user)
        harmonization_recipe = factories.HarmonizationRecipeFactory.create(units=unit_recipes)
        self.assertEqual(unit_recipes, list(harmonization_recipe.units.all()))
