"""Test the functions and classes for views.py."""

from django.urls import reverse

from core.utils import (DCCAnalystLoginTestCase, LoginRequiredTestCase, RecipeSubmitterLoginTestCase,
                        PhenotypeTaggerLoginTestCase, UserLoginTestCase)
from recipes.factories import HarmonizationRecipeFactory, UnitRecipeFactory
from tags.factories import DCCReviewFactory, TaggedTraitFactory
from tags.models import DCCReview, TaggedTrait
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
        self.assertNotIn('user_taggedtraits', context)
        self.assertNotIn('study_taggedtrait_counts', context)
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
        self.assertIn('user_taggedtraits', context)
        self.assertEqual(len(context['user_taggedtraits']), 0)
        self.assertNotIn('study_taggedtrait_counts', context)

    def test_has_correct_tagged_phenotypes_tabs(self):
        """Staff user does see My Tagged Phenotypes, but not study tagged phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertContains(response, 'id="user_tagged_phenotypes"')
        self.assertNotContains(response, 'id="study_tagged_phenotypes"')

    def test_has_recipes_tabs(self):
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

    def test_my_tagged_variables_correct_empty(self):
        """The list of 'my tagged traits' is correct when the user has no taggedtraits."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertEqual(context['user_taggedtraits'], [])

    def test_my_tagged_variables_correct_count(self):
        """The list of 'my tagged traits' has the correct count of taggedtraits."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_correct_count_with_archived_tagged_trait(self):
        """The list of 'my tagged traits' has the correct count of taggedtraits when there is one archived."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        archived_tagged_trait = TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=study, creator=self.user, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_excludes_trait_tagged_by_other_user(self):
        """The list of 'my tagged traits' does not include traits tagged by another user."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        other_tagged_trait = TaggedTraitFactory.create(trait__source_dataset__source_study_version__study=study)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        self.assertNotIn(other_tagged_trait.pk, all_tagged_trait_pks)
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_excludes_archived_tagged_trait(self):
        """The list of 'my tagged traits' does not include an archived tagged trait."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        archived_tagged_trait = TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=study, creator=self.user, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        self.assertNotIn(archived_tagged_trait.pk, all_tagged_trait_pks)
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_delete_link_present_for_unreviewed_taggedtrait(self):
        """The taggedtrait delete link is present in the html for a taggedtrait that is not reviewed."""
        tagged_trait = TaggedTraitFactory.create(creator=self.user)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertContains(response, tagged_trait_delete_url)

    def test_delete_link_not_present_for_confirmed_taggedtrait(self):
        """The taggedtrait delete link is not present in the html for a taggedtrait that is confirmed."""
        dcc_review = DCCReviewFactory.create(status=DCCReview.STATUS_CONFIRMED, tagged_trait__creator=self.user)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[dcc_review.tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertNotContains(response, tagged_trait_delete_url)

    def test_delete_link_not_present_for_needsfollowup_taggedtrait(self):
        """The taggedtrait delete link is not present in the html for a taggedtrait that needs followup."""
        dcc_review = DCCReviewFactory.create(status=DCCReview.STATUS_FOLLOWUP, tagged_trait__creator=self.user)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[dcc_review.tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertNotContains(response, tagged_trait_delete_url)


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
        self.assertNotIn('user_taggedtraits', context)
        self.assertNotIn('study_taggedtrait_counts', context)

    def test_has_no_tagged_phenotypes_tabs(self):
        """Recipe submitter does not see 'my tagged variables' or 'tagged variables in my studies'."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertNotContains(response, 'id="user_tagged_phenotypes"')
        self.assertNotContains(response, 'id="study_tagged_phenotypes"')

    def test_has_recipes_tabs(self):
        """Recipe submitter sees both recipes tabs."""
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
        self.assertIn('user_taggedtraits', context)
        self.assertIn('study_taggedtrait_counts', context)

    def test_has_correct_tagged_phenotypes_tabs(self):
        """Tagger user does see My Tagged Phenotypes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertContains(response, 'id="user_tagged_phenotypes"')
        self.assertContains(response, 'id="study_tagged_phenotypes"')

    def test_has_no_recipes_tabs(self):
        """Regular user does not see any recipes."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertFalse(context['show_recipes'])
        self.assertNotContains(response, 'id="unitrecipes"')
        self.assertNotContains(response, 'id="harmonizationrecipes"')

    def test_my_tagged_variables_correct_empty(self):
        """The list of 'my tagged traits' is correct when the user has no taggedtraits."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertEqual(context['user_taggedtraits'], [])

    def test_my_tagged_variables_correct_count(self):
        """The list of 'my tagged traits' has the correct count of taggedtraits."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_correct_count_with_archived_tagged_trait(self):
        """The list of 'my tagged traits' has the correct count of taggedtraits when one is archived."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        archived_tagged_trait = TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=study, creator=self.user, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_excludes_trait_tagged_by_other_user(self):
        """The list of 'my tagged traits' does not include traits tagged by another user."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        other_tagged_trait = TaggedTraitFactory.create(trait__source_dataset__source_study_version__study=study)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        self.assertNotIn(other_tagged_trait.pk, all_tagged_trait_pks)
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_my_tagged_variables_excludes_archived_tagged_trait(self):
        """The list of 'my tagged traits' does not include an archived tagged trait."""
        study = StudyFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(
            2, creator=self.user,
            trait__source_dataset__source_study_version__study=study)
        archived_tagged_trait = TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=study, creator=self.user, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['user_taggedtraits'][0][0]
        study_tag_data = context['user_taggedtraits'][0][1]
        all_tagged_trait_pks = [[[el['taggedtrait_pk'] for el in taggedtraits] for tag, taggedtraits in tag_taggedtraits] for study, tag_taggedtraits in context['user_taggedtraits']]  # noqa
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest once.
        all_tagged_trait_pks = [x for y in all_tagged_trait_pks for x in y]  # Unnest twice.
        self.assertNotIn(archived_tagged_trait.pk, all_tagged_trait_pks)
        expected_pks = list(TaggedTrait.objects.non_archived().filter(creator=self.user).values_list('pk', flat=True))
        self.assertEqual(sorted(all_tagged_trait_pks), expected_pks)

    def test_study_tagged_variables_correct_empty(self):
        """The counts of 'tagged variables from my studies' is correct when the study and user have no taggedtraits."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertEqual(context['study_taggedtrait_counts'], [])

    def test_study_tagged_variables_correct_count(self):
        """The counts of 'tagged variables from my studies' has the correct count of taggedtraits."""
        user_tagged_trait = TaggedTraitFactory.create(creator=self.user,
                                                      trait__source_dataset__source_study_version__study=self.study)
        other_study_taggedtrait = TaggedTraitFactory.create()
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['study_taggedtrait_counts']
        self.assertEqual(self.user.profile.taggable_studies.count(), len(study_data))
        study1_tag_pks = [el['tag_pk'] for el in study_data[0][1]]
        self.assertIn(user_tagged_trait.tag.pk, study1_tag_pks)
        self.assertNotIn(other_study_taggedtrait.tag.pk, study1_tag_pks)
        self.assertEqual(study_data[0][1][0]['tt_count'], 1)

    def test_study_tagged_variables_correct_count_with_archived_tagged_trait(self):
        """The counts of 'tagged variables from my studies' does not include an archived tagged trait."""
        user_tagged_trait = TaggedTraitFactory.create(
            creator=self.user, trait__source_dataset__source_study_version__study=self.study)
        archived_taggedtrait = TaggedTraitFactory.create(
            creator=self.user, trait__source_dataset__source_study_version__study=self.study, archived=True,
            tag=user_tagged_trait.tag)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['study_taggedtrait_counts']
        self.assertEqual(self.user.profile.taggable_studies.count(), len(study_data))
        study1_tag_pks = [el['tag_pk'] for el in study_data[0][1]]
        self.assertIn(user_tagged_trait.tag.pk, study1_tag_pks)
        self.assertEqual(study_data[0][1][0]['tt_count'], 1)

    def test_study_tagged_variables_includes_trait_tagged_by_other_user(self):
        """The counts of 'tagged variables from my studies' does include traits tagged by another user."""
        user_tagged_trait = TaggedTraitFactory.create(creator=self.user,
                                                      trait__source_dataset__source_study_version__study=self.study)
        other_user_taggedtrait = TaggedTraitFactory.create(
            tag=user_tagged_trait.tag,
            trait__source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['study_taggedtrait_counts']
        self.assertEqual(self.user.profile.taggable_studies.count(), len(study_data))
        study1_tag_pks = [el['tag_pk'] for el in study_data[0][1]]
        self.assertIn(user_tagged_trait.tag.pk, study1_tag_pks)
        self.assertEqual(study_data[0][1][0]['tt_count'], 2)

    def test_study_tagged_variables_excludes_archived_tagged_trait(self):
        """The counts of 'tagged variables from my studies' does not include an archived tagged trait."""
        user_tagged_trait = TaggedTraitFactory.create(
            creator=self.user, trait__source_dataset__source_study_version__study=self.study)
        archived_taggedtrait = TaggedTraitFactory.create(
            creator=self.user, trait__source_dataset__source_study_version__study=self.study, archived=True,
            tag=user_tagged_trait.tag)
        response = self.client.get(self.get_url())
        context = response.context
        study_data = context['study_taggedtrait_counts']
        self.assertEqual(self.user.profile.taggable_studies.count(), len(study_data))
        study1_tag_pks = [el['tag_pk'] for el in study_data[0][1]]
        self.assertIn(user_tagged_trait.tag.pk, study1_tag_pks)
        self.assertEqual(study_data[0][1][0]['tt_count'], 1)

    def test_delete_link_present_for_unreviewed_taggedtrait(self):
        """The taggedtrait delete link is present in the html for a taggedtrait that is not reviewed."""
        tagged_trait = TaggedTraitFactory.create(creator=self.user,
                                                 trait__source_dataset__source_study_version__study=self.study)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertContains(response, tagged_trait_delete_url)

    def test_delete_link_not_present_for_confirmed_taggedtrait(self):
        """The taggedtrait delete link is not present in the html for a taggedtrait that is confirmed."""
        dcc_review = DCCReviewFactory.create(
            status=DCCReview.STATUS_CONFIRMED,
            tagged_trait__creator=self.user,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[dcc_review.tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertNotContains(response, tagged_trait_delete_url)

    def test_delete_link_not_present_for_needsfollowup_taggedtrait(self):
        """The taggedtrait delete link is not present in the html for a taggedtrait that needs followup."""
        dcc_review = DCCReviewFactory.create(
            status=DCCReview.STATUS_FOLLOWUP,
            tagged_trait__creator=self.user,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        tagged_trait_delete_url = reverse('tags:tagged-traits:pk:delete', args=[dcc_review.tagged_trait.pk])
        response = self.client.get(self.get_url())
        self.assertNotContains(response, tagged_trait_delete_url)


class ProfilesLoginRequiredTestCase(LoginRequiredTestCase):

    def test_profiles_login_required(self):
        """All profiles urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('profiles')
