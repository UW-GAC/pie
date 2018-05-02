"""Test the functions and classes for views.py."""

from django.urls import reverse
from django.test import TestCase

from core.utils import (DCCAnalystLoginTestCase, LoginRequiredTestCase, RecipeSubmitterLoginTestCase,
                        PhenotypeTaggerLoginTestCase, UserLoginTestCase)
from recipes.factories import HarmonizationRecipeFactory, UnitRecipeFactory
from tags.factories import TaggedTraitFactory
from trait_browser.factories import StudyFactory


class ProfileTest(UserLoginTestCase):

    def setUp(self):
        super(ProfileTest, self).setUp()

    def get_url(self, *args):
        return reverse('profiles:profile')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertFalse(context['show_tabs'])
        self.assertFalse(context['show_recipes'])
        self.assertFalse(context['show_my_tagged'])
        self.assertFalse(context['show_study_tagged'])
        self.assertNotIn('unit_recipe_table', context)
        self.assertNotIn('harmonization_recipe_table', context)
        self.assertNotIn('user_tagged_tables', context)
        self.assertNotIn('taggable_study_tagged_tables', context)
        self.assertEqual(context['user'], self.user)

    def test_no_tagged_phenotypes(self):
        """Regular user does not see My Tagged Phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertNotContains(response, 'id="user_tagged_phenotypes"')
        self.assertNotContains(response, 'id="study_tagged_phenotypes"')

    def test_no_recipes(self):
        """Regular user does not see any recipes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertFalse(context['show_recipes'])
        self.assertNotContains(response, 'id="unitrecipes"')
        self.assertNotContains(response, 'id="harmonizationrecipes"')


class DCCAnalystLoginTestCaseProfileTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(DCCAnalystLoginTestCaseProfileTest, self).setUp()

    def get_url(self, *args):
        return reverse('profiles:profile')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_tabs'])
        self.assertTrue(context['show_recipes'])
        self.assertTrue(context['show_my_tagged'])
        self.assertFalse(context['show_study_tagged'])
        self.assertIn('unit_recipe_table', context)
        self.assertEqual(len(context['unit_recipe_table'].rows), 0)
        self.assertIn('harmonization_recipe_table', context)
        self.assertEqual(len(context['harmonization_recipe_table'].rows), 0)
        self.assertIn('user_tagged_tables', context)
        self.assertEqual(len(context['user_tagged_tables']), 0)
        self.assertNotIn('taggable_study_tagged_tables', context)

    def test_has_tagged_phenotypes(self):
        """Staff user does see My Tagged Phenotypes, but not study tagged phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertContains(response, 'id="user_tagged_phenotypes"')
        self.assertNotContains(response, 'id="study_tagged_phenotypes"')

    def test_has_recipes(self):
        """Staff user does see any recipes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_recipes'])
        self.assertContains(response, 'id="unitrecipes"')
        self.assertContains(response, 'id="harmonizationrecipes"')

    def test_has_correct_recipe_count(self):
        """Tables of recipes have the correct number of rows for this user."""
        unit_recipes = UnitRecipeFactory.create_batch(10, creator=self.user)
        harmonization_recipes = HarmonizationRecipeFactory.create_batch(10, creator=self.user)
        other_unit_recipe = UnitRecipeFactory.create()
        other_harmonization_recipe = HarmonizationRecipeFactory.create()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertNotIn(other_unit_recipe, context['unit_recipe_table'].data)
        self.assertNotIn(other_harmonization_recipe, context['harmonization_recipe_table'].data)
        self.assertEqual(len(context['unit_recipe_table'].rows), len(unit_recipes))
        self.assertEqual(len(context['harmonization_recipe_table'].rows), len(harmonization_recipes))

    def test_has_correct_taggedtrait_count(self):
        """Table of tagged traits has the correct number of rows for this user."""
        # There are no tables at all (an empty tab) when there are no tagged traits for this DCC analyst.
        response = self.client.get(self.get_url())
        context = response.context
        self.assertEqual(context['user_tagged_tables'], [])
        # Count in one table is correct when the user has tagged studies.
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            10, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        other_tagged_trait = TaggedTraitFactory.create(trait__source_dataset__source_study_version__study=study)
        response = self.client.get(self.get_url())
        context = response.context
        user_table = context['user_tagged_tables'][0][1]
        self.assertNotIn(other_tagged_trait, user_table.data)
        self.assertEqual(len(tagged_traits), len(user_table.rows))


class RecipeSubmitterLoginTestCaseProfileTest(RecipeSubmitterLoginTestCase):

    def setUp(self):
        super(RecipeSubmitterLoginTestCaseProfileTest, self).setUp()

    def get_url(self, *args):
        return reverse('profiles:profile')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('show_tabs', context)
        self.assertTrue(context['show_tabs'])
        self.assertIn('show_recipes', context)
        self.assertIn('unit_recipe_table', context)
        self.assertIn('harmonization_recipe_table', context)
        self.assertNotIn('user_tagged_tables', context)
        self.assertNotIn('taggable_study_tagged_tables', context)

    def test_no_tagged_phenotypes(self):
        """Regular user does not see My Tagged Phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertNotContains(response, 'id="user_tagged_phenotypes"')
        self.assertNotContains(response, 'id="study_tagged_phenotypes"')

    def test_no_recipes(self):
        """Regular user does not see any recipes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_recipes'])
        self.assertContains(response, 'id="unitrecipes"')
        self.assertContains(response, 'id="harmonizationrecipes"')

    def test_has_correct_recipe_count(self):
        """Tables of recipes have the correct number of rows for this user."""
        unit_recipes = UnitRecipeFactory.create_batch(10, creator=self.user)
        harmonization_recipes = HarmonizationRecipeFactory.create_batch(10, creator=self.user)
        other_unit_recipe = UnitRecipeFactory.create()
        other_harmonization_recipe = HarmonizationRecipeFactory.create()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertNotIn(other_unit_recipe, context['unit_recipe_table'].data)
        self.assertNotIn(other_harmonization_recipe, context['harmonization_recipe_table'].data)
        self.assertEqual(len(context['unit_recipe_table'].rows), len(unit_recipes))
        self.assertEqual(len(context['harmonization_recipe_table'].rows), len(harmonization_recipes))


class PhenotypeTaggerLoginTestCaseProfileTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(PhenotypeTaggerLoginTestCaseProfileTest, self).setUp()

    def get_url(self, *args):
        return reverse('profiles:profile')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_tabs'])
        self.assertFalse(context['show_recipes'])
        self.assertTrue(context['show_my_tagged'])
        self.assertTrue(context['show_study_tagged'])
        self.assertNotIn('unit_recipe_table', context)
        self.assertNotIn('harmonization_recipe_table', context)
        self.assertIn('user_tagged_tables', context)
        self.assertIn('taggable_study_tagged_tables', context)

    def test_no_tagged_phenotypes(self):
        """Tagger user does see My Tagged Phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertContains(response, 'id="user_tagged_phenotypes"')
        self.assertContains(response, 'id="study_tagged_phenotypes"')

    def test_no_recipes(self):
        """Regular user does not see any recipes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertFalse(context['show_recipes'])
        self.assertNotContains(response, 'id="unitrecipes"')
        self.assertNotContains(response, 'id="harmonizationrecipes"')

    def test_has_correct_taggedtrait_count(self):
        """Table of tagged traits by user and by study have the correct number of rows."""
        # There are no tables at all (an empty tab) when there are no tagged traits for this DCC analyst.
        response = self.client.get(self.get_url())
        context = response.context
        self.assertEqual(context['user_tagged_tables'], [])
        # Count in one table is correct when the user has tagged studies.
        tagged_traits = TaggedTraitFactory.create_batch(
            10, creator=self.user,
            trait__source_dataset__source_study_version__study=self.study)
        other_tagged_trait = TaggedTraitFactory.create(trait__source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url())
        context = response.context
        user_table = context['user_tagged_tables'][0][1]
        self.assertNotIn(other_tagged_trait, user_table.data)
        self.assertEqual(len(tagged_traits), len(user_table.rows))
        study_table = context['taggable_study_tagged_tables'][0][1]
        self.assertIn(other_tagged_trait, study_table.data)
        self.assertEqual(len(tagged_traits) + 1, len(study_table.rows))


class ProfilesLoginRequiredTestCase(LoginRequiredTestCase):

    def test_profiles_login_required(self):
        """All profiles urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('profiles')
