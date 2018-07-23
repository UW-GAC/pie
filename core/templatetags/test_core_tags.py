"""Test the functions for core.core_tags."""

# dcc_analysts, dcc_developers, recipe_submitters, phenotype_taggers

from core.utils import (DCCAnalystLoginTestCase, DCCDeveloperLoginTestCase, PhenotypeTaggerLoginTestCase,
                        RecipeSubmitterLoginTestCase)

from . import core_tags


class HasGroupDCCAnalystTest(DCCAnalystLoginTestCase):

    def test_correct_group_true(self):
        """Returns true when testing for belonging to true group."""
        self.assertTrue(core_tags.has_group(self.user, 'dcc_analysts'))

    def test_incorrect_group_false(self):
        """Returns false when testing for belonging to a false group."""
        self.assertFalse(core_tags.has_group(self.user, 'dcc_developers'))


class HasGroupDCCDeveloperTest(DCCDeveloperLoginTestCase):

    def test_correct_group_true(self):
        """Returns true when testing for belonging to true group."""
        self.assertTrue(core_tags.has_group(self.user, 'dcc_developers'))

    def test_incorrect_group_false(self):
        """Returns false when testing for belonging to a false group."""
        self.assertFalse(core_tags.has_group(self.user, 'dcc_analysts'))


class HasGroupPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def test_correct_group_true(self):
        """Returns true when testing for belonging to true group."""
        self.assertTrue(core_tags.has_group(self.user, 'phenotype_taggers'))

    def test_incorrect_group_false(self):
        """Returns false when testing for belonging to a false group."""
        self.assertFalse(core_tags.has_group(self.user, 'dcc_developers'))


class HasGroupRecipeSubmitterTest(RecipeSubmitterLoginTestCase):

    def test_correct_group_true(self):
        """Returns true when testing for belonging to true group."""
        self.assertTrue(core_tags.has_group(self.user, 'recipe_submitters'))

    def test_incorrect_group_false(self):
        """Returns false when testing for belonging to a false group."""
        self.assertFalse(core_tags.has_group(self.user, 'dcc_developers'))
