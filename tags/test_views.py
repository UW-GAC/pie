"""Tests of views in the tags app."""

import copy
from faker import Faker

from django.contrib.auth.models import Group
from django.urls import reverse

from core.factories import UserFactory
from core.utils import (LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase,
                        DCCAnalystLoginTestCase, DCCDeveloperLoginTestCase, get_autocomplete_view_ids)
from trait_browser.factories import SourceStudyVersionFactory, SourceTraitFactory, StudyFactory
from trait_browser.models import SourceTrait

from . import factories
from . import forms
from . import models
from . import tables
from . import views

fake = Faker()


class TagDetailTestsMixin(object):
    """Mixin to run standard tests for the TagDetail view, for use with TestCase or subclass of TestCase."""

    def get_url(self, *args):
        return reverse('tags:tag:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study_counts', context)

    def test_no_archived_taggedtraits(self):
        """A non-archived tagged trait is in the study counts, but not an archived one."""
        archived_tagged_trait = factories.TaggedTraitFactory.create(archived=True, tag=self.tag)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(archived=False, tag=self.tag)
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        study_names = [el['study_name'] for el in context['study_counts']]
        self.assertIn(
            non_archived_tagged_trait.trait.source_dataset.source_study_version.study.i_study_name, study_names)
        self.assertNotIn(
            archived_tagged_trait.trait.source_dataset.source_study_version.study.i_study_name, study_names)


class TagDetailTest(TagDetailTestsMixin, UserLoginTestCase):

    def setUp(self):
        super(TagDetailTest, self).setUp()
        self.tag = factories.TagFactory.create()

    def test_no_tagging_button(self):
        """Regular user does not see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertNotContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagDetailPhenotypeTaggerTest(TagDetailTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TagDetailPhenotypeTaggerTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_has_tagging_button(self):
        """A phenotype tagger does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagDetailDCCAnalystTest(TagDetailTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(TagDetailDCCAnalystTest, self).setUp()
        self.study = StudyFactory.create()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_has_tagging_button(self):
        """A DCC analyst does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(TagAutocompleteTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(10)

    def get_url(self, *args):
        return reverse('tags:autocomplete')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the tags with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([tag.pk for tag in self.tags]), sorted(pks))

    def test_proper_tag_in_queryset(self):
        """Queryset returns only the proper tag by title."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_upper_case(self):
        """Queryset returns only the proper tag by title when query is in upper case."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title.upper()})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_lower_case(self):
        """Queryset returns only the proper tag by title when query is in lower case."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title.lower()})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_partial_query(self):
        """The results contain the desired trait when a single letter is used for the query."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title[0]})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) >= 1)
        self.assertIn(tag.pk, pks)


class TagListTest(UserLoginTestCase):

    def setUp(self):
        super(TagListTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(20)

    def get_url(self, *args):
        return reverse('tags:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('tag_table' in context)
        self.assertIsInstance(context['tag_table'], tables.TagTable)


class TaggedTraitDetailTestsMixin(object):
    """Mixin to run standard tests for the TaggedTraitDetail view, for use with TestCase or subclass of TestCase."""

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_no_other_tags(self):
        """Other tags linked to the same trait are not included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertNotIn('show_other_tags', context)
        content = str(response.content)
        self.assertNotIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_delete_button_unreviewed(self):
        """Delete button is shown for unreviewed tagged trait."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_no_delete_button_needfollowup_reviewed_tagged_trait(self):
        """Shows no button to delete a need_followup tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_no_delete_button_confirmed_reviewed_tagged_trait(self):
        """Shows no button to delete a confirmed tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_no_delete_button_archived_tagged_trait(self):
        """Shows no button to delete an archived tagged trait."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))


class TaggedTraitDetailPhenotypeTaggerTest(TaggedTraitDetailTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            creator=self.user
        )
        self.user.refresh_from_db()

    def test_no_review_button(self):
        """No review button is shown for a phenotype tagger."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))

    def test_reviewed_tagged_trait_missing_udpate_review_button(self):
        """A reviewed tagged trait does not include a link to update the DCCReview for Phenotype taggers."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:dcc-review:update',
                                                 args=[self.tagged_trait.pk]))

    def test_context_with_unreviewed_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertFalse(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])

    def test_context_with_confirmed_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertTrue(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertFalse(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_needs_followup_no_response_nonarchived_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_needs_followup_no_response_archived_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_context_with_followup_agree_nonarchived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, agree, and nonarchived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertTrue(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_followup_agree_archived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, agree, and archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        dcc_review.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertTrue(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_context_with_followup_disagree_nonarchived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, disagree, and nonarchived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertTrue(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_followup_disagree_archived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, disagree, and archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_review.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertTrue(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.clear()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_wrong_taggable_study(self):
        """View returns 403 code when the user is from a different study."""
        other_study_tagged_trait = factories.TaggedTraitFactory.create()
        response = self.client.get(self.get_url(other_study_tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitDetailDCCAnalystTest(TaggedTraitDetailTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()
        self.user.refresh_from_db()

    def test_context_with_unreviewed_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertTrue(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertFalse(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_confirmed_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertTrue(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertFalse(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_needs_followup_no_response_nonarchived_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_needs_followup_no_response_archived_tagged_trait(self):
        """The context contains the proper flags for the add/update review buttons."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertFalse(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_context_with_followup_agree_nonarchived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, agree, and non-archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertTrue(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_followup_agree_archived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, agree, and archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        dcc_review.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertTrue(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertFalse(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_context_with_followup_disagree_nonarchived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, disagree, and non-archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertTrue(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertFalse(context['show_archived'])

    def test_context_with_followup_disagree_archived_tagged_trait(self):
        """Correct context flags for tagged trait needs followup, disagree, and archived."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_review.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('show_quality_review_panel', context)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertIn('show_dcc_review_add_button', context)
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertIn('show_dcc_review_update_button', context)
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertIn('show_confirmed_status', context)
        self.assertFalse(context['show_confirmed_status'])
        self.assertIn('show_needs_followup_status', context)
        self.assertTrue(context['show_needs_followup_status'])
        self.assertIn('show_study_response_status', context)
        self.assertTrue(context['show_study_response_status'])
        self.assertIn('show_study_agrees', context)
        self.assertFalse(context['show_study_agrees'])
        self.assertIn('show_study_disagrees', context)
        self.assertTrue(context['show_study_disagrees'])
        self.assertIn('show_archived', context)
        self.assertTrue(context['show_archived'])

    def test_archived_tagged_trait_missing_link_to_review(self):
        """An archived tagged trait does not include a link to review for DCC users."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))

    def test_unreviewed_tagged_trait_includes_link_to_review(self):
        """An unreviewed tagged trait includes a link to review for DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))

    def test_reviewed_tagged_trait_includes_link_to_udpate(self):
        """The context contains the proper flags when the tagged trait has not been reviewed.."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))

    def test_archived_tagged_trait_missing_link_to_udpate(self):
        """An archived tagged trait does not include a link to update the dcc review."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(
            response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))


class TaggedTraitTagCountsByStudyTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitTagCountsByStudyTest, self).setUp()

    def make_fake_data(self):
        self.tags = factories.TagFactory.create_batch(2)
        self.studies = StudyFactory.create_batch(2)
        self.taggedtraits = []
        for tag in self.tags:
            for study in self.studies:
                self.taggedtraits.extend(
                    factories.TaggedTraitFactory.create_batch(
                        2, tag=tag, trait__source_dataset__source_study_version__study=study)
                )

    def get_url(self, *args):
        return reverse('tags:tagged-traits:by-study')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('taggedtrait_tag_counts_by_study', context)

    def test_context_data_is_correct(self):
        """Data in the context is correct."""
        self.make_fake_data()
        response = self.client.get(self.get_url())
        context = response.context
        for study in context['taggedtrait_tag_counts_by_study']:
            for tag in study[1]:
                tag_study_count = models.TaggedTrait.objects.filter(
                    tag__pk=tag['tag_pk'],
                    trait__source_dataset__source_study_version__study__pk=study[0]['study_pk']).count()
                self.assertEqual(tag['tt_count'], tag_study_count)

    def test_count_does_not_include_archived_taggedtraits(self):
        """Counts do not include archived tagged traits."""
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=study, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=study, archived=False)
        response = self.client.get(self.get_url())
        counts = response.context['taggedtrait_tag_counts_by_study']
        self.assertEqual(counts[0][1][0]['tt_count'], 1)


class TaggedTraitStudyCountsByTagTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitStudyCountsByTagTest, self).setUp()

    def make_fake_data(self):
        self.tags = factories.TagFactory.create_batch(2)
        self.studies = StudyFactory.create_batch(2)
        self.taggedtraits = []
        for tag in self.tags:
            for study in self.studies:
                self.taggedtraits.append(
                    factories.TaggedTraitFactory.create_batch(
                        2, tag=tag, trait__source_dataset__source_study_version__study=study)
                )

    def get_url(self, *args):
        return reverse('tags:tagged-traits:by-tag')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('taggedtrait_study_counts_by_tag', context)

    def test_context_data_is_correct(self):
        """Data in the context is correct."""
        self.make_fake_data()
        response = self.client.get(self.get_url())
        context = response.context
        for tag in context['taggedtrait_study_counts_by_tag']:
            for study in tag[1]:
                study_tag_count = models.TaggedTrait.objects.filter(
                    tag__pk=tag[0]['tag_pk'],
                    trait__source_dataset__source_study_version__study__pk=study['study_pk']).count()
                self.assertEqual(study['tt_count'], study_tag_count)

    def test_count_does_not_include_archived_taggedtraits(self):
        """Counts do not include archived tagged traits."""
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=study, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=study, archived=False)
        response = self.client.get(self.get_url())
        counts = response.context['taggedtrait_study_counts_by_tag']
        self.assertEqual(counts[0][1][0]['tt_count'], 1)


class TaggedTraitByTagAndStudyListTestsMixin(object):

    def get_url(self, *args):
        return reverse('tags:tag:study:list', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_table_contains_correct_records(self):
        """All expected tagged traits are in the table."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertEqual(len(table.data), len(self.tagged_traits))
        for tagged_trait in self.tagged_traits:
            self.assertIn(tagged_trait, table.data, msg='tagged_trait_table does not contain {}'.format(tagged_trait))

    def test_works_with_no_tagged_traits_in_study(self):
        """Table has zero rows when there are no tagged traits."""
        other_study = StudyFactory.create()
        other_tag = factories.TagFactory.create()
        response = self.client.get(self.get_url(other_tag.pk, other_study.pk))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(len(context['tagged_trait_table'].data), 0)

    def test_does_not_show_tagged_traits_from_a_different_study(self):
        """Table does not include tagged trait from a different study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=other_study)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_does_not_show_tagged_traits_from_a_different_tag(self):
        """Table does not include tagged trait with a different tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag, trait__source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)


class TaggedTraitByTagAndStudyListTest(TaggedTraitByTagAndStudyListTestsMixin, UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListTest, self).setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, tag=self.tag, trait__source_dataset__source_study_version__study=self.study)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('show_review_button', context)
        self.assertFalse(context['show_review_button'])

    def test_table_class(self):
        """For non-taggers, the tagged trait table class does not have delete buttons."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTable)

    def test_no_detail_page_links(self):
        """Contains no links to the TaggedTraitDetail view."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        for tagged_trait in self.tagged_traits:
            self.assertNotIn(tagged_trait.get_absolute_url(), str(response.content))

    def test_no_archived_taggedtraits(self):
        """Archived tagged traits do not appear in the table."""
        models.TaggedTrait.objects.all().delete()
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=False)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIn('tagged_trait_table', response.context)
        table = response.context['tagged_trait_table']
        self.assertNotIn(archived_tagged_trait, table.data)
        self.assertIn(non_archived_tagged_trait, table.data)


class TaggedTraitByTagAndStudyListPhenotypeTaggerTest(TaggedTraitByTagAndStudyListTestsMixin,
                                                      PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListPhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study, tag=self.tag)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.study)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('show_review_button', context)
        self.assertFalse(context['show_review_button'])

    def test_table_class(self):
        """For taggers, the tagged trait table class is correct."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableForStudyTaggers)

    def test_contains_detail_page_links(self):
        """Contains links to the TaggedTraitDetail view."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        for tagged_trait in self.tagged_traits:
            self.assertIn(tagged_trait.get_absolute_url(), str(response.content))

    def test_no_archived_taggedtraits(self):
        """Archived tagged traits do not appear in the table."""
        models.TaggedTrait.objects.all().delete()
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=False)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIn('tagged_trait_table', response.context)
        table = response.context['tagged_trait_table']
        self.assertNotIn(archived_tagged_trait, table.data)
        self.assertIn(non_archived_tagged_trait, table.data)


class TaggedTraitByTagAndStudyListDCCAnalystTest(TaggedTraitByTagAndStudyListTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListDCCAnalystTest, self).setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study, tag=self.tag)
        self.user.refresh_from_db()

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('show_review_button', context)
        self.assertTrue(context['show_review_button'])

    def test_table_class(self):
        """For DCC Analysts, the tagged trait table class has delete buttons."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableForDCCStaff)

    def test_contains_detail_page_links(self):
        """Contains links to the TaggedTraitDetail view."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        for tagged_trait in self.tagged_traits:
            self.assertIn(tagged_trait.get_absolute_url(), str(response.content))

    def test_includes_archived_taggedtraits(self):
        """Archived tagged traits do appear in the table."""
        models.TaggedTrait.objects.all().delete()
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=False)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIn('tagged_trait_table', response.context)
        table = response.context['tagged_trait_table']
        self.assertIn(archived_tagged_trait, table.data)
        self.assertIn(non_archived_tagged_trait, table.data)


class TaggedTraitCreateTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertRedirects(response, reverse('tags:tag:detail', args=[new_object.tag.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.all_traits.all())
        self.assertIn(self.tag, self.trait.all_tags.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_tags_traits_from_two_studies(self):
        """Correctly able to tag traits from two different studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        # Tag the two traits.
        response1 = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        response2 = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response1, self.tag.get_absolute_url())
        self.assertRedirects(response2, self.tag.get_absolute_url())
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in [self.trait.pk, trait2.pk]:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['trait'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.all_tags.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged_but_archived(self):
        """Tagging a trait fails when the trait has already been tagged with this tag and archived."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, archived=True)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class TaggedTraitCreatePhenotypeTaggerTest(TaggedTraitCreateTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreatePhenotypeTaggerTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)


class TaggedTraitCreateDCCAnalystTest(TaggedTraitCreateTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_tag_other_study_trait(self):
        """Tagging a trait from another study works since the analyst doesn't have taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # View redirects to success url.
        self.assertRedirects(response, reverse('tags:tag:detail', args=[self.tag.pk]))
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)


class TaggedTraitDeleteTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:delete', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertEqual(context['next_url'], None)

    def test_deletes_unreviewed(self):
        """Posting 'submit' to the form correctly deletes the tagged_trait."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_post_anything_deletes_unreviewed(self):
        """Posting anything at all, even an empty dict, deletes the object."""
        # Is this really the behavior I want? I'm not sure...
        # Sounds like it might be:
        # https://stackoverflow.com/questions/17678689/how-to-add-a-cancel-button-to-deleteview-in-django
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_confirmed_tagged_trait_get_request_redirects_before_confirmation_view(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 302)
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.CONFIRMED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_does_not_delete_confirmed(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertEqual(response.status_code, 302)
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.CONFIRMED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_needs_followup_tagged_trait_get_request_reaches_confirmation_view(self):
        """Confirmation view has success code when trying to delete a needs followup reviewed TaggedTrait."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())

    def test_archives_need_followup(self):
        """Archives a TaggedTrait that was reviewed with needs followup."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertEqual(response.status_code, 302)
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertNotIn(views.CONFIRMED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_next_url(self):
        """next_url in context matches the starting url."""
        starting_url = reverse('trait_browser:source:traits:detail', args=[self.trait.pk])
        url_with_next = self.get_url(self.tagged_trait.pk) + '?next={}'.format(starting_url)
        response = self.client.get(url_with_next)
        context = response.context
        self.assertEqual(context['next_url'], starting_url)

    def test_success_url_sourcetraitdetail(self):
        """Redirects to the source trait detail page as expected."""
        starting_url = reverse('trait_browser:source:traits:detail', args=[self.trait.pk])
        url_with_next = self.get_url(self.tagged_trait.pk) + '?next={}'.format(starting_url)
        response = self.client.post(url_with_next, {'submit': ''})
        self.assertRedirects(response, starting_url)

    def test_success_url_taggedtraitdetail(self):
        """Redirects to the TaggedTraitByTagAndStudyList view as expected."""
        starting_url = reverse('tags:tagged-traits:pk:detail', args=[self.tagged_trait.pk])
        tag_study_list_url = reverse(
            'tags:tag:study:list',
            kwargs={'pk_study': self.trait.source_dataset.source_study_version.study.pk,
                    'pk': self.tag.pk}
        )
        url_with_next = self.get_url(self.tagged_trait.pk) + '?next={}'.format(starting_url)
        response = self.client.post(url_with_next, {'submit': ''})
        self.assertRedirects(response, tag_study_list_url)

    def test_success_url_profile(self):
        """Redirects to the profile page as expected."""
        starting_url = reverse('profiles:profile')
        url_with_next = self.get_url(self.tagged_trait.pk) + '?next={}'.format(starting_url)
        response = self.client.post(url_with_next, {'submit': ''})
        self.assertRedirects(response, starting_url)

    def test_success_url_no_starting_url(self):
        """Redirects to the profile page as expected."""
        tag_study_list_url = reverse(
            'tags:tag:study:list',
            kwargs={'pk_study': self.trait.source_dataset.source_study_version.study.pk,
                    'pk': self.tag.pk}
        )
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, tag_study_list_url)


class TaggedTraitDeletePhenotypeTaggerTest(TaggedTraitDeleteTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitDeletePhenotypeTaggerTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()
        self.tagged_trait = models.TaggedTrait.objects.create(trait=self.trait, tag=self.tag, creator=self.user)

    def test_deletes_unreviewed_tagged_by_other_user(self):
        """User can delete a tagged trait that was created by someone else from the same study."""
        trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        other_user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        other_user.groups.add(phenotype_taggers)
        other_user.profile.taggable_studies.add(self.study)
        other_user_tagged_trait = models.TaggedTrait.objects.create(trait=trait, tag=self.tag, creator=other_user)
        response = self.client.post(self.get_url(other_user_tagged_trait.pk), {'submit': ''})
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            other_user_tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 1)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_wrong_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitDeleteDCCAnalystTest(TaggedTraitDeleteTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitDeleteDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()
        self.tagged_trait = models.TaggedTrait.objects.create(trait=self.trait, tag=self.tag, creator=self.user)

    def test_deletes_unreviewed_tagged_by_other_user(self):
        """User can delete a tagged trait that was created by someone else from the same study."""
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version__study=self.trait.source_dataset.source_study_version.study)
        other_user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        other_user.groups.add(phenotype_taggers)
        other_user.profile.taggable_studies.add(self.trait.source_dataset.source_study_version.study)
        other_user_tagged_trait = models.TaggedTrait.objects.create(trait=trait, tag=self.tag, creator=other_user)
        response = self.client.post(self.get_url(other_user_tagged_trait.pk), {'submit': ''})
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            other_user_tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 1)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """DCC user can access the view even when they're not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """DCC user can access the view even with no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)


class TaggedTraitCreateByTagTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('tag' in context)
        self.assertEqual(context['tag'], self.tag)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        form_data = {'trait': self.trait.pk, }
        response = self.client.post(self.get_url(self.tag.pk), form_data)
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.all_traits.all())
        self.assertIn(self.tag, self.trait.all_tags.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_tags_traits_from_two_studies(self):
        """Correctly able to tag traits from two different studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        # Tag the two traits.
        response1 = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        response2 = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response1, self.tag.get_absolute_url())
        self.assertRedirects(response2, self.tag.get_absolute_url())
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in [self.trait.pk, trait2.pk]:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('trait'))
        self.assertNotIn(self.tag, self.trait.all_tags.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'trait': self.trait.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged_but_archived(self):
        """Tagging a trait fails when the trait has already been tagged with this tag but archived."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, archived=True)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class TaggedTraitCreateByTagPhenotypeTaggerTest(TaggedTraitCreateByTagTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateByTagPhenotypeTaggerTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitCreateByTagDCCAnalystTest(TaggedTraitCreateByTagTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateByTagDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def test_tag_other_study_trait(self):
        """DCC user can tag a trait even when it's not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # View redirects to success url.
        self.assertRedirects(response, reverse('tags:tag:detail', args=[self.tag.pk]))
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group_taggers(self):
        """DCC user can access the view even though they're not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """DCC user can access the view even without any taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)


class ManyTaggedTraitsCreateTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_single_trait(self):
        """Posting valid data to the form correctly tags a single trait."""
        this_trait = self.traits[0]
        form_data = {'traits': [this_trait.pk], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        tagged_trait = models.TaggedTrait.objects.get(trait=this_trait, tag=self.tag)
        self.assertIn(this_trait, self.tag.all_traits.all())
        self.assertIn(self.tag, this_trait.all_tags.all())

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(),
                                    {'traits': [str(t.pk) for t in some_traits], 'tag': self.tag.pk})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'traits': '', 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_all_traits(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': [], 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].all_tags.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)], 'tag': self.tag.pk})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged_but_archived(self):
        """Tagging traits fails when a selected trait is already tagged with the tag but archived."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class ManyTaggedTraitsCreatePhenotypeTaggerTest(ManyTaggedTraitsCreateTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreatePhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()

    def test_creates_all_new_objects_from_multiple_studies(self):
        """Correctly tags traits from two different studies in the user's taggable_studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        more_traits = SourceTraitFactory.create_batch(2, source_dataset__source_study_version__study=study2)
        more_traits = self.traits[:2] + more_traits
        form_data = {'traits': [x.pk for x in more_traits], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(
            self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)


class ManyTaggedTraitsCreateDCCAnalystTest(ManyTaggedTraitsCreateTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateDCCAnalystTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, )
        self.user.refresh_from_db()

    def test_tag_other_study_traits(self):
        """DCC user can tag traits without any taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects_from_multiple_studies(self):
        """Correctly tags traits from two different studies in the user's taggable_studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        more_traits = SourceTraitFactory.create_batch(2, source_dataset__source_study_version__study=study2)
        more_traits = self.traits[:2] + more_traits
        form_data = {'traits': [x.pk for x in more_traits], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)


class ManyTaggedTraitsCreateByTagTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(self.traits[0].pk)]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.traits[0])
        self.assertIn(self.traits[0], self.tag.all_traits.all())
        self.assertIn(self.tag, self.traits[0].all_tags.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(t.pk) for t in some_traits]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(t.pk) for t in self.traits], })
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in self.traits:
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].all_tags.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(self.traits[0].pk)], })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged(self):
        """Tagging traits fails when two selected traits are already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged_but_archived(self):
        """Tagging traits fails when a selected trait is already tagged with the tag but archived."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged_but_archived(self):
        """Tagging traits fails when two selected traits are already tagged with the tag but archived."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1], archived=True)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class ManyTaggedTraitsCreateByTagPhenotypeTaggerTest(ManyTaggedTraitsCreateByTagTestsMixin,
                                                     PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagPhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()

    def test_creates_all_new_objects_from_multiple_studies(self):
        """Correctly tags traits from two different studies in the user's taggable_studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        more_traits = SourceTraitFactory.create_batch(2, source_dataset__source_study_version__study=study2)
        more_traits = self.traits[:2] + more_traits
        form_data = {'traits': [x.pk for x in more_traits], }
        response = self.client.post(self.get_url(self.tag.pk), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.all_traits.all())
            self.assertIn(self.tag, trait.all_tags.all())

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(
            self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)


class ManyTaggedTraitsCreateByTagDCCAnalystTest(ManyTaggedTraitsCreateByTagTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagDCCAnalystTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, )
        self.user.refresh_from_db()

    def test_tag_other_study_traits(self):
        """DCC user can tag traits without any taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)


class DCCReviewByTagAndStudySelectDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10,
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:select', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)
        self.assertIsInstance(context['form'], forms.DCCReviewTagAndStudySelectForm)

    def test_post_blank_trait(self):
        """Posting bad data to the form shows a form error and doesn't set session variables."""
        response = self.client.post(self.get_url(), {'tag': '', 'study': ''})
        self.assertFormError(response, 'form', 'tag', 'This field is required.')
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_post_valid_form(self):
        """Posting valid data to the form sets session variables and redirects appropriately."""
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_session_variable_tagged_with_tag(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_session_variable_tagged_with_study(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_session_variable_tagged_with_study_and_tag(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given study and tag."""
        other_tag = factories.TagFactory.create()
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_no_tagged_traits_with_study_and_tag(self):
        """Redirects to list view of no tagged traits for this study and tag."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        response = self.client.post(self.get_url(), {'tag': tag.pk, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # Form errors.
        self.assertIn('form', response.context)
        self.assertFormError(response, 'form', None, forms.DCCReviewTagAndStudySelectForm.ERROR_NO_TAGGED_TRAITS)
        # Make sure no variables were set.
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_resets_session_variables(self):
        """A preexisting session variable is overwritten with new data upon successful form submission."""
        self.client.session['tagged_trait_review_by_tag_and_study_info'] = {
            'study_pk': self.study.pk + 1,
            'tag_pk': self.tag.pk + 1,
            'tagged_trait_pks': [],
        }
        self.client.session.save()
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))

    def test_link_to_review_views(self):
        """The link to review tagged traits appears on the home page for DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))

    def test_no_archived_taggedtraits_in_session_variable(self):
        """Sets session variable, without including archived tagged traits."""
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=True)
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(archived_tagged_trait.pk, session_info['tagged_trait_pks'])
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)


class DCCReviewByTagAndStudySelectDCCAnalystTest(DCCReviewByTagAndStudySelectDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudySelectDCCTestsMixin, as a DCC analyst.
    pass


class DCCReviewByTagAndStudySelectDCCDeveloperTest(DCCReviewByTagAndStudySelectDCCTestsMixin,
                                                   DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudySelectDCCTestsMixin, as a DCC developer.
    pass


class DCCReviewByTagAndStudySelectOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:select', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_link_not_in_navbar(self):
        """The link to review tagged traits doesn't appear on the home page for non-DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewByTagAndStudySelectFromURLDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10,
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )

    def get_url(self, *args):
        return reverse('tags:tag:study:begin-dcc-review', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_nonexistent_study_404(self):
        """View returns 404 if study does not exist."""
        study_pk = self.study.pk
        self.study.delete()
        response = self.client.get(self.get_url(self.tag.pk, study_pk), follow=False)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_tag_404(self):
        """View returns 404 if tag does not exist."""
        tag_pk = self.tag.pk
        self.tag.delete()
        response = self.client.get(self.get_url(tag_pk, self.study.pk), follow=False)
        self.assertEqual(response.status_code, 404)

    def test_sets_session_variables(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_only_tagged_traits_from_requested_tag(self):
        """tagged_trait_pks is set to only those from the given tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_only_tagged_traits_from_requested_study(self):
        """tagged_trait_pks is set to only those from the given study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_session_variable_tagged_with_study_and_tag(self):
        """tagged_trait_pks is set to only those from the given study and tag."""
        other_tag = factories.TagFactory.create()
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_resets_session_variables(self):
        """A preexisting session variable is overwritten with new data."""
        self.client.session['tagged_trait_review_by_tag_and_study_info'] = {
            'study_pk': self.study.pk + 1,
            'tag_pk': self.tag.pk + 1,
            'tagged_trait_pks': [],
        }
        self.client.session.save()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))

    def test_continue_reviewing_link_in_navbar_after_successful_load(self):
        """The link to continue reviewing appears in the navbar after loading this page."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(reverse('tags:tagged-traits:dcc-review:next')))

    def test_no_tagged_traits_to_review(self):
        """View redirects and displays message when there are no tagged traits to review for the tag+study."""
        models.TaggedTrait.objects.all().delete()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 302)
        # Check for message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('No tagged variables to review', str(messages[0]))

    def test_no_archived_taggedtraits_in_session_variable(self):
        """Does not include archived tagged traits in session variables."""
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study, archived=True)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(archived_tagged_trait.pk, session_info['tagged_trait_pks'])
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)


class DCCReviewByTagAndStudySelectFromURLDCCAnalystTest(DCCReviewByTagAndStudySelectFromURLDCCTestsMixin,
                                                        DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudySelectFromURLDCCTestsMixin as a DCC analyst.
    pass


class DCCReviewByTagAndStudySelectFromURLDCCDeveloperTest(DCCReviewByTagAndStudySelectFromURLDCCTestsMixin,
                                                          DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudySelectFromURLDCCTestsMixin as a DCC developer.
    pass


class DCCReviewByTagAndStudySelectFromURLOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10,
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )

    def get_url(self, *args):
        return reverse('tags:tag:study:begin-dcc-review', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class DCCReviewByTagAndStudyNextDCCTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:next', args=args)

    def test_view_success_with_no_session_variables(self):
        """View redirects correctly when no session variables are set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_view_success_with_tagged_traits_to_review(self):
        """View redirects correctly when there are tagged traits to review."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        response = self.client.get(self.get_url())
        # Make sure a pk session variable was set
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        self.assertIn('pk', session['tagged_trait_review_by_tag_and_study_info'])
        self.assertEqual(session['tagged_trait_review_by_tag_and_study_info']['pk'], tagged_trait.pk)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:review'))
        # Check messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('You have 1 tagged variable left to review.', str(messages[0]))

    def test_view_success_with_no_tagged_traits_left(self):
        """View redirects correctly when no tagged traits are left to review."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tag:study:list', args=[tag.pk, study.pk]))
        # Check that there are no messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_session_variables_are_unset_when_reviewing_completed(self):
        """View unsets session variables when no tagged traits are left to review."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)

    def test_skips_tagged_trait_that_has_been_reviewed(self):
        """Skips a tagged trait that has been reviewed after starting the loop."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits],
        }
        session.save()
        factories.DCCReviewFactory.create(tagged_trait=tagged_traits[0])
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)
        # Check that there are no messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_skips_deleted_tagged_trait(self):
        """Skips a tagged trait that has been deleted after starting the loop."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits],
        }
        session.save()
        # Now delete it and try loading the view.
        tagged_traits[0].delete()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_skips_archived_tagged_trait(self):
        """Skips a tagged trait that has been archived after starting the loop."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits],
        }
        session.save()
        # Now archive it and try loading the view.
        tagged_traits[0].archive()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_session_variables_are_not_properly_set(self):
        """Redirects to select view if expected session variable is not set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_required_keys(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        template = {
            'study_pk': study.pk,
            'tag_pk': tag.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits]
        }
        for key in template.keys():
            session_info = copy.copy(template)
            session_info.pop(key)
            session = self.client.session
            session['tagged_trait_review_by_tag_and_study_info'] = session_info
            session.save()
            response = self.client.get(self.get_url())
            self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
            self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'),
                                 msg_prefix='did not redirect when missing {} in session'.format(key))

    def test_continue_reviewing_link_in_navbar_if_session_variable_is_present(self):
        """The link to continue reviewing traits appears on the home page for DCC users if session variable exists."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))

    def test_continue_reviewing_link_not_in_navbar_if_session_variable_is_missing(self):
        """The link to continue reviewing doesn't appear on the home page for DCC users if no session variable."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewByTagAndStudyNextDCCAnalystTest(DCCReviewByTagAndStudyNextDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudyNextDCCTestsMixin, as a DCC analyst.
    pass


class DCCReviewByTagAndStudyNextDCCDeveloperTest(DCCReviewByTagAndStudyNextDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudyNextDCCTestsMixin, as a DCC developer.
    pass


class DCCReviewByTagAndStudyNextOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:next', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_continue_reviewing_link_in_navbar_if_session_variable_is_present(self):
        """The link to continue reviewing traits doesn't appear on the home page for non-DCC users."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewByTagAndStudyDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        # Set expected session variables.
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'study_pk': self.study.pk,
            'tag_pk': self.tag.pk,
            'tagged_trait_pks': [self.tagged_trait.pk],
            'pk': self.tagged_trait.pk,
        }
        session.save()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:review', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], 1)

    def test_context_data_with_multiple_remaining_tagged_traits(self):
        """View has appropriate data in the context if there are multiple tagged traits to review."""
        session = self.client.session
        info = session['tagged_trait_review_by_tag_and_study_info']
        info['tagged_trait_pks'] = [self.tagged_trait.pk, self.tagged_trait.pk + 1]
        session.save()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], 2)

    def test_successful_post_with_confirmed_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'foo'}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_post_bad_data(self):
        """Posting bad data to the form shows a form error and doesn't unset session variables."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # The pk session variable is not unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('pk', session_info)
        self.assertEqual(session_info['pk'], self.tagged_trait.pk)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_skip_tagged_trait(self):
        """Skipping a TaggedTrait unsets pk and redirects to the next view."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_SKIP: 'Skip'}
        response = self.client.post(self.get_url(), form_data)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # Session variables are properly set/unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # The redirect view unsets some session variables, so check it at the end.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_non_existent_tagged_trait(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        self.tagged_trait.delete()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 404)

    def test_already_reviewed_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_archived_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is archived."""
        self.tagged_trait.archive()
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_already_reviewed_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is already reviewed, even if there's a form error."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_CONFIRMED,
            comment=''
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_archived_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is archived, even if there's a form error."""
        self.tagged_trait.archive()
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_can_skip_already_reviewed_tagged_trait(self):
        """Redirects without a message if an already-reviewed tagged trait is skipped."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_CONFIRMED,
            comment=''
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_SKIP: 'Skip', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check that no message was generated.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_session_variables_are_not_properly_set_with_get_request(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variables_are_not_properly_set_with_post_request(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_tag_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_study_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_tagged_trait_pks_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_session_variable_missing_key_tag_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_study_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_tagged_trait_pks_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_session_variable_missing_key_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_shows_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_archived_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)


class DCCReviewByTagAndStudyDCCAnalystTest(DCCReviewByTagAndStudyDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudyDCCTestsMixin, as a DCC analyst.
    pass


class DCCReviewByTagAndStudyDCCDeveloperTest(DCCReviewByTagAndStudyDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewByTagAndStudyDCCTestsMixin, as a DCC developer.
    pass


class DCCReviewByTagAndStudyOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-review:review', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_link_not_in_navbar(self):
        """The link to continue reviewing traits doesn't appear on the home page for non-DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewCreateDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-review:new', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_successful_post_with_confirmed_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'foo'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_post_bad_data(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_non_existent_tagged_trait(self):
        """Returns a 404 page with a get request if the tagged trai doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_non_existent_tagged_trait(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.delete()
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_already_reviewed_tagged_trait(self):
        """Shows warning message and redirects to update page if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        # Now try to review it through the web interface.
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)

    def test_post_already_reviewed_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)

    def test_post_already_reviewed_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)

    def test_get_archived_tagged_trait(self):
        """Returns a 404 page with a get request if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """Returns a 404 page if the session variable pk doesn't exist."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_shows_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_archived_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait, archived=True)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)


class DCCReviewCreateDCCAnalystTest(DCCReviewCreateDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewCreateDCCTestsMixin, as a DCC analyst.
    pass


class DCCReviewCreateDCCDeveloperTest(DCCReviewCreateDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewCreateDCCTestsMixin, as a DCC developer.
    pass


class DCCReviewCreateOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-review:new', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_forbidden_get_request_with_existing_review(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request_with_existing_review(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class DCCReviewUpdateDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-review:update', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_successful_post_with_confirmed_tagged_trait(self):
        """Posting valid data to the form correctly updates an existing DCCReview."""
        self.tagged_trait.dcc_review.delete()
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly updates the DCCReview for this TaggedTrait.
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertEqual(self.tagged_trait.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(self.tagged_trait.dcc_review.comment, '')
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly updates a DCCReview."""
        comment = 'a new comment'
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Confirm', 'comment': comment}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly updates the DCCReview for this TaggedTrait.
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertEqual(self.tagged_trait.dcc_review.status, models.DCCReview.STATUS_FOLLOWUP)
        self.assertEqual(self.tagged_trait.dcc_review.comment, comment)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_post_bad_data(self):
        """Posting bad data to the form shows a form error."""
        existing_review = self.tagged_trait.dcc_review
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not update the DCCReview for this TaggedTrait.
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertEqual(self.tagged_trait.dcc_review, existing_review)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_non_existent_tagged_trait(self):
        """GET returns a 404 page if the tagged trait doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.hard_delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_non_existent_tagged_trait(self):
        """POST returns a 404 page if the tagged trait doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.hard_delete()
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_dcc_review(self):
        """GET redirects to the create view with a warning if the DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('has not been reviewed yet', str(messages[0]))

    def test_post_nonexistent_dcc_review(self):
        """POST redirects to the create view with a warning if the DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('has not been reviewed yet', str(messages[0]))

    def test_get_archived_tagged_trait(self):
        """GET redirects to detail page if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('archived', str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """POST redirects to detail page if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('archived', str(messages[0]))

    def test_cant_get_dcc_review_if_study_has_responded(self):
        """Posting data redirects with a message if the study has responded."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Did not update the DCCReview for this TaggedTrait.
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertEqual(self.tagged_trait.dcc_review.status, models.DCCReview.STATUS_FOLLOWUP)
        # Check for error message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Oops!', str(messages[0]))

    def test_get_redirect_if_study_has_responded(self):
        """Loading the page redirects with a message if the study has responded."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Check for error message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Oops!', str(messages[0]))

    def test_shows_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_archived_other_tags(self):
        """Other tags linked to the same trait are included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait, archived=True)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)


class DCCReviewUpdateDCCAnalystTest(DCCReviewUpdateDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCReviewDCCTestsMixin, as a DCC analyst.
    pass


class DCCReviewUpdateDCCDeveloperTest(DCCReviewUpdateDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCReviewDCCTestsMixin, as a DCC developer.
    pass


class DCCReviewUpdateOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-review:update', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class DCCReviewNeedFollowupCountsPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_view_success(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_get_context_data_one_study_with_no_need_followup_traits(self):
        """Counts are correct with no TaggedTraits."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_get_context_data_one_study_one_tagged_trait_with_study_response(self):
        """Count include TaggedTraits that have a study response in the tt_completed_count field."""
        tag = factories.TagFactory.create()
        factories.StudyResponseFactory.create(
            dcc_review__tagged_trait__tag=tag,
            dcc_review__status=models.DCCReview.STATUS_FOLLOWUP,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 0)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 1)

    def test_get_context_data_one_study_with_one_need_followup_tagged_trait(self):
        """Counts are correct with one TaggedTrait that needs followup."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 1)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)

    def test_get_context_data_one_study_with_two_need_followup_tagged_traits(self):
        """Counts are correct with two TaggedTraits that need followup."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 2)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)

    def test_get_context_data_archived_in_tt_completed_and_not_tt_remaining_counts(self):
        """Counts are correct with two TaggedTraits that need followup."""
        tag = factories.TagFactory.create()
        dcc_reviews = factories.DCCReviewFactory.create_batch(
            3, tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP)
        archived_tagged_trait = dcc_reviews[0].tagged_trait
        archived_tagged_trait.archive()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 2)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 1)

    def test_get_context_data_one_study_two_tags(self):
        """Counts are correct with one study and two tags."""
        tag1 = factories.TagFactory.create(title='tag1')
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag1,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        tag2 = factories.TagFactory.create(title='tag2')
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag2,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 2)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag1.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 2)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)
        self.assertEqual(counts[0][1][1]['tag_pk'], tag2.pk)
        self.assertEqual(counts[0][1][1]['tt_remaining_count'], 1)
        self.assertEqual(counts[0][1][1]['tt_completed_count'], 0)

    def test_get_context_data_two_studies_same_tag(self):
        """Counts are correct with two studies and one tag."""
        # Make sure the second study comes last by appending zzz to the name.
        other_study = StudyFactory.create(i_study_name=self.study.i_study_name + 'zzz')
        self.user.profile.taggable_studies.add(other_study)
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=other_study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 2)
        # Check first study.
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 2)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)
        # Check second study.
        self.assertEqual(counts[1][0]['study_pk'], other_study.pk)
        self.assertEqual(len(counts[1][1]), 1)
        self.assertEqual(counts[1][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[1][1][0]['tt_remaining_count'], 1)
        self.assertEqual(counts[1][1][0]['tt_completed_count'], 0)

    def test_context_excludes_confirmed_trait(self):
        """Count does not include a TaggedTrait that is confirmed."""
        factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_CONFIRMED
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_only_taggable_studies(self):
        """Only studies that the user can tag are included."""
        other_study = StudyFactory.create()
        factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=other_study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_context_does_not_include_tags_with_no_followup_traits(self):
        """Tags are not in context data when they have no TaggedTraits that need followup."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        tag2 = factories.TagFactory.create()
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag2,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_CONFIRMED
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 1)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)

    def test_context_does_not_include_tags_with_no_followup_traits_different_studies(self):
        """Tag for one study is not in context data when they have no TaggedTraits that need followup."""
        other_study = StudyFactory.create(i_study_name=self.study.i_study_name + 'zzz')
        self.user.profile.taggable_studies.add(other_study)
        tag1 = factories.TagFactory.create()
        tag2 = factories.TagFactory.create()
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag1,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag2,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_CONFIRMED
        )
        factories.DCCReviewFactory.create(
            tagged_trait__tag=tag1,
            tagged_trait__trait__source_dataset__source_study_version__study=other_study,
            status=models.DCCReview.STATUS_CONFIRMED
        )
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag2,
            tagged_trait__trait__source_dataset__source_study_version__study=other_study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 2)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag1.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], 1)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], 0)
        # Check second study.
        self.assertEqual(counts[1][0]['study_pk'], other_study.pk)
        self.assertEqual(len(counts[1][1]), 1)
        self.assertEqual(counts[1][1][0]['tag_pk'], tag2.pk)
        self.assertEqual(counts[1][1][0]['tt_remaining_count'], 2)
        self.assertEqual(counts[1][1][0]['tt_completed_count'], 0)

    def test_context_with_tagged_traits_with_and_without_responses(self):
        """Counts are correct with a mix of tagged traits that are reviewed or require review."""
        n_confirmed = 15
        n_need_review = 20
        n_review_completed = 32
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            n_confirmed,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_CONFIRMED
        )
        factories.DCCReviewFactory.create_batch(
            n_need_review,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        factories.StudyResponseFactory.create_batch(
            n_review_completed,
            dcc_review__tagged_trait__tag=tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            dcc_review__status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0][0]['study_pk'], self.study.pk)
        self.assertEqual(len(counts[0][1]), 1)
        self.assertEqual(counts[0][1][0]['tag_pk'], tag.pk)
        self.assertEqual(counts[0][1][0]['tt_remaining_count'], n_need_review)
        self.assertEqual(counts[0][1][0]['tt_completed_count'], n_review_completed)

    def test_begin_review_button_is_not_present_if_no_tagged_traits_need_review(self):
        """Final column says 'quality review completed' instead of link to quality review page if completed."""
        tag = factories.TagFactory.create()
        factories.StudyResponseFactory.create_batch(
            2,
            dcc_review__tagged_trait__tag=tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            dcc_review__status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        self.assertNotContains(response, reverse('tags:tag:study:quality-review', args=[tag.pk, self.study.pk]))
        self.assertContains(response, "Quality review completed")

    def test_begin_review_button_is_not_present_if_all_tagged_traits_are_archived_without_study_response(self):
        """Final column says 'quality review completed' instead of link to quality review page if all archived."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2, tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        models.TaggedTrait.objects.update(archived=True)
        response = self.client.get(self.get_url())
        self.assertNotContains(response, reverse('tags:tag:study:quality-review', args=[tag.pk, self.study.pk]))
        self.assertContains(response, "Quality review completed")

    def test_begin_review_button_is_present_if_some_tagged_traits_need_review(self):
        """Final column has link to quality review page if tagged traits remain to be responded to."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        self.assertContains(response, reverse('tags:tag:study:quality-review', args=[tag.pk, self.study.pk]))
        self.assertNotContains(response, "Quality review completed")

    def test_navbar_does_not_contain_link(self):
        """Phenotype taggers do see a link to the main quality review page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewNeedFollowupCountsDCCAnalystTest(DCCAnalystLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_forbidden(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """DCC analysts do not see a link to the main quality review page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewNeedFollowupCountsOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_forbidden(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """Regular users do not see a link to the main quality review page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class DCCReviewNeedFollowupListMixin(object):
    """Tests to include in all user type test cases for this view."""

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)

    def test_table_class(self):
        """The table class is appropriate."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.DCCReviewTable)

    def test_view_contains_tagged_traits_that_need_followup(self):
        """Table contains TaggedTraits that need followup."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertEqual(len(table.data), len(self.dcc_reviews))
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))

    def test_view_table_does_not_contain_unreviewed_tagged_traits(self):
        """Table does not contains unreviewed TaggedTraits."""
        unreviewed_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(unreviewed_tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews))

    def test_view_works_with_no_matching_tagged_traits(self):
        """Successful response code when there are no TaggedTraits to inclue."""
        other_tag = factories.TagFactory.create()
        response = self.client.get(self.get_url(other_tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(len(context['tagged_trait_table'].data), 0)

    def test_view_does_not_show_tagged_traits_from_a_different_study(self):
        """Table does not include TaggedTraits from a different study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=other_study)
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_view_does_not_show_tagged_traits_from_a_different_tag(self):
        """Table does not contain TaggedTraits from a different tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag, trait__source_dataset__source_study_version__study=self.study)
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)


class DCCReviewNeedFollowupListPhenotypeTaggerTest(DCCReviewNeedFollowupListMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.dcc_reviews = factories.DCCReviewFactory.create_batch(
            10,
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )

    def get_url(self, *args):
        return reverse('tags:tag:study:quality-review', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_table_class(self):
        """Table class is correct."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIs(type(response.context['tagged_trait_table']), tables.DCCReviewTableWithStudyResponseButtons)

    def test_forbidden_for_other_study(self):
        """View returns forbidden response code for a study that the user can't tag."""
        other_study = StudyFactory.create()
        response = self.client.get(self.get_url(self.tag.pk, other_study.pk))
        self.assertEqual(response.status_code, 403)

    def test_csrf_token(self):
        """View contains a csrf token when study response buttons are present."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertContains(response, "name='csrfmiddlewaretoken'")

    def test_buttons_for_need_followup_tagged_trait(self):
        """Buttons are shown for TaggedTraits that need followup and have no StudyResponse."""
        models.TaggedTrait.objects.hard_delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        tagged_trait = dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        expected_url = reverse('tags:tagged-traits:pk:quality-review:remove', args=[tagged_trait.pk])
        self.assertContains(response, expected_url)
        expected_url = reverse('tags:tagged-traits:pk:quality-review:explain', args=[tagged_trait.pk])
        self.assertContains(response, expected_url)

    def test_no_buttons_for_need_followup_tagged_trait_with_agree_response(self):
        """Buttons are not shown for TaggedTraits that need followup and have an "agree" StudyResponse."""
        models.TaggedTrait.objects.hard_delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review,
            status=models.StudyResponse.STATUS_AGREE
        )
        tagged_trait = dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        expected_url = reverse('tags:tagged-traits:pk:quality-review:remove', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)
        expected_url = reverse('tags:tagged-traits:pk:quality-review:explain', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)

    def test_no_buttons_for_need_followup_tagged_trait_with_disagree_response(self):
        """Buttons are not shown for TaggedTraits that need followup and have a "disagree" StudyResponse."""
        models.TaggedTrait.objects.hard_delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review,
            status=models.StudyResponse.STATUS_DISAGREE
        )
        tagged_trait = dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        expected_url = reverse('tags:tagged-traits:pk:quality-review:remove', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)
        expected_url = reverse('tags:tagged-traits:pk:quality-review:explain', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)

    def test_no_buttons_for_need_followup_tagged_trait_no_response_and_archived(self):
        """Buttons are not shown for TaggedTraits that need followup, have no StudyResponse, and are archived."""
        models.TaggedTrait.objects.hard_delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        tagged_trait = dcc_review.tagged_trait
        tagged_trait.archive()
        tagged_trait.refresh_from_db()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        expected_url = reverse('tags:tagged-traits:pk:quality-review:remove', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)
        expected_url = reverse('tags:tagged-traits:pk:quality-review:explain', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)

    def test_no_buttons_for_need_followup_tagged_trait_with_response_and_archived(self):
        """Buttons are not shown for TaggedTraits that need followup, have an agree StudyResponse, and are archived."""
        models.TaggedTrait.objects.hard_delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review,
            status=models.StudyResponse.STATUS_AGREE)
        tagged_trait = dcc_review.tagged_trait
        tagged_trait.archive()
        tagged_trait.refresh_from_db()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        expected_url = reverse('tags:tagged-traits:pk:quality-review:remove', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)
        expected_url = reverse('tags:tagged-traits:pk:quality-review:explain', args=[tagged_trait.pk])
        self.assertNotContains(response, expected_url)

    def test_table_includes_archived_tagged_trait(self):
        """An archived tagged trait that needs followup is included in the table."""
        archived_tagged_trait = models.TaggedTrait.objects.first()
        archived_tagged_trait.archive()
        archived_tagged_trait.refresh_from_db()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        table = response.context['tagged_trait_table']
        self.assertIn(archived_tagged_trait, table.data)


class DCCReviewNeedFollowupListDCCAnalystTest(DCCReviewNeedFollowupListMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.dcc_reviews = factories.DCCReviewFactory.create_batch(
            10,
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )

    def get_url(self, *args):
        return reverse('tags:tag:study:quality-review', args=args)

    def test_table_class(self):
        """Table class is correct."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIs(type(response.context['tagged_trait_table']), tables.DCCReviewTable)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)


class DCCReviewNeedFollowupListOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.dcc_reviews = factories.DCCReviewFactory.create_batch(
            10,
            tagged_trait__tag=self.tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )

    def get_url(self, *args):
        return reverse('tags:tag:study:quality-review', args=args)

    def test_forbidden(self):
        """View returns forbidden response code for non-taggers and non-staff."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class StudyResponseCreateAgreeOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:remove', args=args)

    def test_post_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class StudyResponseCreateAgreePhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:remove', args=args)

    def test_get_method_not_allowed(self):
        """Returns a method not allowed status code for get requests."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 405)

    def test_can_create_study_response(self):
        """Creates a study response as expected."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertTrue(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        study_response = self.tagged_trait.dcc_review.study_response
        self.assertEqual(study_response.status, models.StudyResponse.STATUS_AGREE)
        self.assertEqual(study_response.comment, '')
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_missing_tagged_trait(self):
        """Returns 404 status with missing tagged trait."""
        response = self.client.post(self.get_url(self.tagged_trait.pk + 1), {})
        self.assertEqual(response.status_code, 404)

    def test_missing_dcc_review(self):
        """Redirects with warning message if DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has not been reviewed' in str(messages[0]))

    def test_archived_tagged_trait(self):
        """Redirects with warning message if the tagged trait has been archived."""
        self.tagged_trait.archive()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('removed' in str(messages[0]))

    def test_confirmed_dcc_review(self):
        """Redirects with warning message if DCCReview status is confirmed."""
        self.tagged_trait.dcc_review.delete()
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has been confirmed' in str(messages[0]))

    def test_studyresponse_exists(self):
        """Redirects with warning message if a StudyResponse already exists."""
        factories.StudyResponseFactory.create(dcc_review=self.tagged_trait.dcc_review,
                                              status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertTrue(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        study_response = self.tagged_trait.dcc_review.study_response
        # Make sure it was not updated.
        self.assertEqual(study_response.status, models.StudyResponse.STATUS_DISAGREE)
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_cant_create_study_response_for_other_study_tagged_trait(self):
        """Can't review tagged traits from a different study."""
        # This is a suggested test, but we need to decide on the expected behavior.
        other_tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.post(self.get_url(other_tagged_trait.pk), {})
        self.assertFalse(hasattr(other_tagged_trait.dcc_review, 'study_response'))
        self.assertEqual(response.status_code, 403)

    def test_adds_user(self):
        """When a StudyResponse is successfully created, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(self.tagged_trait.dcc_review.study_response.creator, self.user)

    def test_archives_tagged_trait(self):
        """When a StudyResponse is successfully created, the tagged trait is archived."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)


class StudyResponseCreateAgreeDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:remove', args=args)

    def test_post_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class StudyResponseCreateDisagreeOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:explain', args=args)

    def test_post_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class StudyResponseCreateDisagreePhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:explain', args=args)

    def test_view_success(self):
        """View loads correctly."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """Context contains the correct values."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.StudyResponseDisagreeForm)
        self.assertFalse(context['form'].is_bound)

    def test_can_create_study_response(self):
        """Creates a study response as expected."""
        comment = 'a comment'
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': comment})
        self.assertTrue(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        study_response = self.tagged_trait.dcc_review.study_response
        self.assertEqual(study_response.status, models.StudyResponse.STATUS_DISAGREE)
        self.assertEqual(study_response.comment, comment)
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_post_invalid_form(self):
        """Posting an invalid form does not create a study response."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': ''})
        self.assertEqual(response.status_code, 200)
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        form = response.context['form']
        self.assertTrue(form.has_error('comment'))

    def test_get_missing_tagged_trait(self):
        """Returns 404 status with missing tagged trait."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_post_missing_tagged_trait(self):
        """Returns 404 status with missing tagged trait."""
        response = self.client.post(self.get_url(self.tagged_trait.pk + 1), {'comment': 'a comment'})
        self.assertEqual(response.status_code, 404)

    def test_get_missing_dcc_review(self):
        """Redirects with warning message if DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has not been reviewed' in str(messages[0]))

    def test_post_missing_dcc_review(self):
        """Redirects with warning message if a DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_get_archived_tagged_trait(self):
        """Redirects with warning message if the tagged trait has been archived."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('removed' in str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """Redirects with warning message if the tagged trait has been archived."""
        self.tagged_trait.archive()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_confirmed_dcc_review(self):
        """Redirects with warning message if DCCReview status is confirmed."""
        self.tagged_trait.dcc_review.delete()
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has been confirmed' in str(messages[0]))

    def test_get_studyresponse_exists(self):
        """Redirects with warning message if a StudyResponse already exists."""
        factories.StudyResponseFactory.create(dcc_review=self.tagged_trait.dcc_review,
                                              status=models.StudyResponse.STATUS_AGREE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertTrue(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_studyresponse_exists(self):
        """Redirects with warning message if a StudyResponse already exists."""
        factories.StudyResponseFactory.create(dcc_review=self.tagged_trait.dcc_review,
                                              status=models.StudyResponse.STATUS_AGREE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertTrue(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        study_response = self.tagged_trait.dcc_review.study_response
        # Make sure it was not updated.
        self.assertEqual(study_response.status, models.StudyResponse.STATUS_AGREE)
        self.assertEqual(study_response.comment, '')
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_get_cant_create_study_response_for_other_study_tagged_trait(self):
        """Can't review tagged traits from a different study."""
        # This is a suggested test, but we need to decide on the expected behavior.
        other_tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(other_tagged_trait.pk))
        self.assertFalse(hasattr(other_tagged_trait.dcc_review, 'study_response'))
        self.assertEqual(response.status_code, 403)

    def test_post_cant_create_study_response_for_other_study_tagged_trait(self):
        """Can't review tagged traits from a different study."""
        # This is a suggested test, but we need to decide on the expected behavior.
        other_tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.post(self.get_url(other_tagged_trait.pk), {})
        self.assertFalse(hasattr(other_tagged_trait.dcc_review, 'study_response'))
        self.assertEqual(response.status_code, 403)

    def test_adds_user(self):
        """When a StudyResponse is successfully created, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment', })
        self.assertEqual(self.tagged_trait.dcc_review.study_response.creator, self.user)

    def test_does_not_archive_tagged_trait(self):
        """When a disagree StudyResponse is successfully created, the tagged trait is not archived."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment', })
        self.tagged_trait.refresh_from_db()
        self.assertFalse(self.tagged_trait.archived)

    def test_no_other_tags(self):
        """Other tags linked to the same trait are not included in the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertNotIn('show_other_tags', context)
        content = str(response.content)
        self.assertNotIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)


class StudyResponseCreateDisagreeDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:explain', args=args)

    def test_post_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Returns a 403 forbidden status code for non-taggers."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitsNeedDCCDecisionSummaryDCCAnalystTest(DCCAnalystLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:need-decision', args=args)

    def test_view_success(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_get_context_data(self):
        """Context contains expected variables."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)

    def test_counts_blank_with_zero_tagged_traits(self):
        """Correct count when there are no tagged traits."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_counts_exclude_confirmed_tagged_trait(self):
        """Count does not include tagged trait with DCCReview status confirmed."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_counts_exclude_needfollowup_noresponse_tagged_trait(self):
        """Count does not include tagged trait of status need followup with no study response."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_counts_exclude_needfollowup_agree_tagged_trait(self):
        """Count does not include tagged trait of status need followup with agree study response."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_AGREE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_counts_for_needfollowup_disagree_tagged_trait(self):
        """Correct counts when only one tagged trait needs a decision."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 1)

    def test_counts_for_needfollowup_disagree_tagged_trait_with_remove_decision(self):
        """Correct counts when only one tagged trait needed a decision, and it's been decided to remove."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 0)  # Decision has been made.

    def test_counts_for_needfollowup_disagree_tagged_trait_with_confirm_decision(self):
        """Correct counts when only one tagged trait needed a decision, and it's been decided to confirm."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 0)  # Decision has been made.

    def test_counts_for_needfollowup_disagree_tagged_trait_with_remove_decision_archived(self):
        """Correct counts when only one tagged trait needed a decision, and it's been decided to remove, and it's archived."""  # noqa
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        study_response.dcc_review.tagged_trait.archive()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 0)  # Decision has been made.

    def test_counts_for_needfollowup_disagree_tagged_traits_from_two_studies(self):
        """Correct counts when tagged traits from two studies need decisions."""
        study_response1 = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        study_response2 = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 2)  # Two studies.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 1)
        study2 = counts[1]
        self.assertEqual(study2[1][0]['tt_total'], 1)
        self.assertEqual(study2[1][0]['tt_decision_required_count'], 1)

    def test_counts_for_two_needfollowup_disagree_tagged_traits_from_same_study_and_tag(self):
        """Correct counts when two tagged traits from the same study and tag need decisions."""
        study_version = SourceStudyVersionFactory.create()
        tag = factories.TagFactory.create()
        study_responses = factories.StudyResponseFactory.create_batch(
            2, status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version=study_version,
            dcc_review__tagged_trait__tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 2)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 2)

    def test_counts_for_two_needfollowup_disagree_tagged_traits_with_remove_decision_from_same_study_and_tag(self):
        """Correct counts when two tagged traits from the same study and tag already have decisions to remove."""
        study_version = SourceStudyVersionFactory.create()
        tag = factories.TagFactory.create()
        study_responses = factories.StudyResponseFactory.create_batch(
            2, status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version=study_version,
            dcc_review__tagged_trait__tag=tag)
        decisions = [factories.DCCDecisionFactory.create(dcc_review=sr.dcc_review) for sr in study_responses]
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 2)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 0)  # Decision has been made.

    def test_counts_for_two_studies_and_two_tags(self):
        """Correct counts in a complex set of tagged traits that need decisions and already have decisions."""
        # There are two studies, two tags, and some decided and some not decided for each tag+study.
        study_versions_of_two_studies = SourceStudyVersionFactory.create_batch(2)
        tags = factories.TagFactory.create_batch(2)
        # Start with making three tagged traits need a decision (one without decision, and one of each decision type).
        to_decide = 3
        counts_to_match = []
        for sv in study_versions_of_two_studies:
            study_dict = {'study_name': sv.study.i_study_name, 'study_pk': sv.study.pk}
            tag_list = []
            for t in tags:
                # Make tagged traits for each tag + study.
                tagged_traits = factories.TaggedTraitFactory.create_batch(
                    5, tag=t, trait__source_dataset__source_study_version=sv)
                # Make some that need decisions.
                study_responses = factories.StudyResponseFactory.create_batch(
                    to_decide, status=models.StudyResponse.STATUS_DISAGREE,
                    dcc_review__tagged_trait__trait__source_dataset__source_study_version=sv,
                    dcc_review__tagged_trait__tag=t)
                # Make one that has each decision type.
                factories.DCCDecisionFactory.create(
                    dcc_review=study_responses[0].dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
                factories.DCCDecisionFactory.create(
                    dcc_review=study_responses[1].dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
                tag_dict = {'tt_total': to_decide, 'tag_name': t.title, 'study_pk': sv.study.pk, 'tag_pk': t.pk,
                            'study_name': sv.study.i_study_name, 'tt_decision_required_count': to_decide - 2}
                tag_list.append(tag_dict)
                to_decide += 1  # Increment this every time so the counts are distinguishable.
            counts_to_match.append((study_dict, tag_list))
        # counts_to_match = tuple(counts_to_match)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        # Sometimes the order of the studies wasn't quite right, and sorting didn't work due to dicts.
        # So that's why this study-by-study matching was needed.
        for study in counts:
            study_to_match = [el for el in counts_to_match if el[0] == study[0]][0]
            self.assertEqual(study, study_to_match)

    def test_counts_exclude_tag_without_decisions_needed(self):
        """Counts exclude a tag that lacks tagged traits requiring decisions."""
        extra_tag = factories.TagFactory.create()
        extra_tagged_trait = factories.TaggedTraitFactory.create()
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)  # One study.
        study1 = counts[0]
        self.assertEqual(study1[1][0]['tt_total'], 1)
        self.assertEqual(study1[1][0]['tt_decision_required_count'], 1)
        self.assertEqual(len(study1[1]), 1)  # Only one tag.

    def test_button_changes_from_make_to_view(self):
        """Button to the tag+study page says 'make' when no decisions exist."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url())
        self.assertNotContains(response, "View final decisions", html=True)
        decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url())
        self.assertContains(response, "View final decisions", html=True)

    def test_navbar_does_contain_link(self):
        """DCC users do see a link to the dcc decisions summary page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.get_url())


class TaggedTraitsNeedDCCDecisionSummaryOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:need-decision', args=args)

    def test_forbidden(self):
        """Returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """Groupless users do not see a link to the dcc decisions summary page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.get_url())


class TaggedTraitsNeedDCCDecisionSummaryPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:need-decision', args=args)

    def test_forbidden(self):
        """Returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """Phenotype taggers do not see a link to the dcc decisions summary page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.get_url())


class TaggedTraitsNeedDCCDecisionByTagAndStudyListDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            3, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        return reverse('tags:tag:study:dcc-decision', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)

    def test_table_class(self):
        """The table class is appropriate."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitDCCDecisionTable)

    def test_view_contains_tagged_traits_that_need_decision(self):
        """Table contains TaggedTraits that need dcc decisions."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertEqual(len(table.data), len(self.study_responses))
        for study_response in self.study_responses:
            self.assertIn(study_response.dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(study_response.dcc_review.tagged_trait))

    def test_view_table_does_not_contain_unreviewed_tagged_traits(self):
        """Table does not contain unreviewed TaggedTraits."""
        unreviewed_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(unreviewed_tagged_trait, table.data)
        for study_response in self.study_responses:
            self.assertIn(study_response.dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(study_response.dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.study_responses))

    def test_view_table_does_not_contain_tagged_trait_with_no_study_response(self):
        """Table does not contain TaggedTrait without a study response."""
        no_response_dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            tagged_trait__tag=self.tag,
            status=models.DCCReview.STATUS_FOLLOWUP)
        no_response_tagged_trait = no_response_dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(no_response_tagged_trait, table.data)
        for study_response in self.study_responses:
            self.assertIn(study_response.dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(study_response.dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.study_responses))

    def test_view_table_does_not_contain_tagged_trait_with_agree_response(self):
        """Table does not contain tagged trait with agree study response."""
        agree_response = factories.StudyResponseFactory.create(
            dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.StudyResponse.STATUS_AGREE)
        agree_tagged_trait = agree_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(agree_tagged_trait, table.data)
        for study_response in self.study_responses:
            self.assertIn(study_response.dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(study_response.dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.study_responses))

    def test_view_works_with_no_matching_tagged_traits(self):
        """Successful response code when there are no TaggedTraits to include."""
        other_tag = factories.TagFactory.create()
        response = self.client.get(self.get_url(other_tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(len(context['tagged_trait_table'].data), 0)

    def test_view_does_not_show_tagged_traits_from_a_different_study(self):
        """Table does not include TaggedTraits from a different study."""
        other_study = StudyFactory.create()
        other_study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=other_study)
        other_tagged_trait = other_study_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_view_does_not_show_tagged_traits_from_a_different_tag(self):
        """Table does not contain TaggedTraits from a different tag."""
        other_tag = factories.TagFactory.create()
        other_study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__tag=other_tag)
        other_tagged_trait = other_study_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_decision_links_present_for_nodecision_tagged_traits(self):
        """Decision buttons are shown for tagged trait without decision."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        pass
        # TODO: add tests once decision create views are added.

    def test_update_link_present_for_decision_confirm_tagged_traits(self):
        """Update button is shown for tagged trait with confirm."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.study_responses[0].dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        pass

    def test_update_link_present_for_decision_remove_tagged_traits(self):
        """Update button is shown for tagged trait with remove."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.study_responses[0].dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        pass


class TaggedTraitsNeedDCCDecisionByTagAndStudyListOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            3, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        return reverse('tags:tag:study:dcc-decision', args=args)

    def test_forbidden(self):
        """Returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitsNeedDCCDecisionByTagAndStudyListPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            3, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        return reverse('tags:tag:study:dcc-decision', args=args)

    def test_forbidden(self):
        """Returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class TagsLoginRequiredTest(LoginRequiredTestCase):

    def test_tags_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('tags')
