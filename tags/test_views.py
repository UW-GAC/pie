"""Tests of views in the tags app."""

import copy
from faker import Faker

from django.contrib.auth.models import Group
from django.urls import reverse

from core.factories import UserFactory
from core.utils import (LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase,
                        DCCAnalystLoginTestCase, DCCDeveloperLoginTestCase, get_autocomplete_view_ids)
from trait_browser.factories import SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, StudyFactory
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
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study_counts', context)
        self.assertIn('traits_tagged_count', context)

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

    def test_no_deprecated_traits(self):
        """Counts exclude traits tagged from deprecated study versions."""
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=self.tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=self.tag)
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertEqual(context['study_counts'][0]['study_pk'], study.pk)
        self.assertEqual(context['study_counts'][0]['tt_count'], 1)
        self.assertEqual(context['traits_tagged_count'], 1)

    def test_no_deprecated_traits_with_same_version_number(self):
        """Counts exclude traits tagged from deprecated study versions even with same version number."""
        # This directly addresses the unusual CARDIA situation where there are two study versions with the
        # same version number, one of which is deprecated.
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=self.tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=self.tag)
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertEqual(context['study_counts'][0]['study_pk'], study.pk)
        self.assertEqual(context['study_counts'][0]['tt_count'], 1)
        self.assertEqual(context['traits_tagged_count'], 1)


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
        """Returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_tags(self):
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

    def test_unreviewed_only_returns_no_tags_without_tagged_traits(self):
        """Queryset returns only tags with unreviewed tagged traits, with unreviewed_only argument."""
        url = self.get_url()
        response = self.client.get(url, {'q': '', 'forward': ['{"unreviewed_only":true}']})
        pks = get_autocomplete_view_ids(response)
        self.assertEqual([], pks)

    def test_unreviewed_only_returns_correct_tag(self):
        """Queryset returns only tags with unreviewed tagged traits, with unreviewed_only argument."""
        unreviewed_tagged_trait = factories.TaggedTraitFactory.create(tag=self.tags[0])
        reviewed_tagged_trait = factories.TaggedTraitFactory.create(tag=self.tags[1])
        factories.DCCReviewFactory.create(tagged_trait=reviewed_tagged_trait)
        url = self.get_url()
        response = self.client.get(url, {'q': '', 'forward': ['{"unreviewed_only":true}']})
        pks = get_autocomplete_view_ids(response)
        self.assertEqual([unreviewed_tagged_trait.tag.pk], pks)

    def test_unreviewed_only_returns_all_tags(self):
        """Queryset returns only tags with unreviewed tagged traits, with unreviewed_only argument."""
        for tag in self.tags:
            factories.TaggedTraitFactory.create(tag=tag)
        url = self.get_url()
        response = self.client.get(url, {'q': '', 'forward': ['{"unreviewed_only":true}']})
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([tag.pk for tag in self.tags]), sorted(pks))


class TagListTest(UserLoginTestCase):

    def setUp(self):
        super(TagListTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(20)

    def get_url(self, *args):
        return reverse('tags:list')

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('tag_table' in context)
        self.assertIsInstance(context['tag_table'], tables.TagTable)

    def test_no_deprecated_traits(self):
        """Counts exclude traits tagged from deprecated study versions."""
        tag = self.tags[0]
        models.Tag.objects.exclude(pk=tag.pk).delete()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        tag_table = context['tag_table']
        row = tag_table.rows[0]
        count = row.get_cell('number_tagged_traits')
        self.assertEqual(count, 1)

    def test_no_deprecated_traits_with_same_version_number(self):
        """Counts exclude traits tagged from deprecated study versions even with same version number."""
        # This directly addresses the unusual CARDIA situation where there are two study versions with the
        # same version number, one of which is deprecated.
        tag = self.tags[0]
        models.Tag.objects.exclude(pk=tag.pk).delete()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        tag_table = context['tag_table']
        row = tag_table.rows[0]
        count = row.get_cell('number_tagged_traits')
        self.assertEqual(count, 1)


class TaggedTraitDetailTestsMixin(object):
    """Mixin to run standard tests for the TaggedTraitDetail view, for use with TestCase or subclass of TestCase."""

    def setUp(self):
        super().setUp()
        if self.user.profile.taggable_studies.count() > 0:
            user_study = self.study
        else:
            user_study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        # Create a tagged trait of each possible status combination.
        self.tagged_traits = {}
        self.tagged_traits['unreviewed'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)

        self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'],
            status=models.DCCReview.STATUS_FOLLOWUP)

        self.tagged_traits[
            'followup_dccreview_disagree_studyresponse_no_dccdecision'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(
            dcc_review=self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].dcc_review,
            status=models.StudyResponse.STATUS_DISAGREE)

        self.tagged_traits['confirmed_dccreview'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['confirmed_dccreview'],
            status=models.DCCReview.STATUS_CONFIRMED)

        self.tagged_traits[
            'followup_dccreview_no_studyresponse_remove_dccdecision_archived'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_traits[
                'followup_dccreview_no_studyresponse_remove_dccdecision_archived'].dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE)
        self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].archive()

        self.tagged_traits[
            'followup_dccreview_no_studyresponse_confirm_dccdecision'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].dcc_review,
            decision=models.DCCDecision.DECISION_CONFIRM)

        self.tagged_traits['followup_dccreview_agree_studyresponse_archived'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_agree_studyresponse_archived'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(
            dcc_review=self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].dcc_review,
            status=models.StudyResponse.STATUS_AGREE)
        self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].archive()

        self.tagged_traits[
            'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
        ] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(
            dcc_review=self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].dcc_review,
            status=models.StudyResponse.STATUS_DISAGREE)
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE)
        self.tagged_traits['followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].archive()

        self.tagged_traits[
            'followup_dccreview_disagree_studyresponse_confirm_dccdecision'] = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=user_study)
        factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'],
            status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(
            dcc_review=self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review,
            status=models.StudyResponse.STATUS_DISAGREE)
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review,
            decision=models.DCCDecision.DECISION_CONFIRM)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:detail', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
        unreviewed_pk = self.tagged_traits['unreviewed'].pk
        self.tagged_traits['unreviewed'].delete()
        response = self.client.get(self.get_url(unreviewed_pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """Expected context variables exist."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_traits['unreviewed'])
        self.assertIn('show_quality_review_panel', context)
        self.assertIn('show_dcc_review_add_button', context)
        self.assertIn('show_dcc_review_update_button', context)
        self.assertIn('show_dcc_review_confirmed', context)
        self.assertIn('show_dcc_review_needs_followup', context)
        self.assertIn('show_study_response_status', context)
        self.assertIn('show_study_agrees', context)
        self.assertIn('show_study_disagrees', context)
        self.assertIn('show_dcc_decision', context)
        self.assertIn('show_dcc_decision_add_button', context)
        self.assertIn('show_dcc_decision_update_button', context)
        self.assertIn('show_decision_remove', context)
        self.assertIn('show_decision_confirm', context)
        self.assertIn('show_decision_comment', context)
        self.assertIn('show_delete_button', context)
        self.assertIn('show_archived', context)
        self.assertIn('quality_review_panel_color', context)
        self.assertIn('is_deprecated', context)
        self.assertIn('show_removed_text', context)
        self.assertIn('new_version_link', context)

    def test_no_other_tags(self):
        """Other tags linked to the same trait are not included in the page."""
        another_tag = factories.TagFactory.create()
        another_tagged_trait = factories.TaggedTraitFactory.create(
            trait=self.tagged_traits['unreviewed'].trait, tag=another_tag)
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        context = response.context
        self.assertNotIn('show_other_tags', context)
        content = str(response.content)
        self.assertNotIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_traits['unreviewed'].tag.title, content)

    def test_delete_link_present_for_unreviewed_tagged_trait(self):
        """Delete button is shown for unreviewed tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        self.assertContains(
            response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_traits['unreviewed'].pk}))

    def test_delete_link_not_shown_for_all_reviewed_tagged_traits(self):
        """Shows no button to delete the rest of tagged traits, which all have reviews."""
        del self.tagged_traits['unreviewed']
        for tt_type in self.tagged_traits:
            tagged_trait = self.tagged_traits[tt_type]
            response = self.client.get(self.get_url(tagged_trait.pk))
            self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': tagged_trait.pk}))

    def test_deprecated_tagged_trait_no_new_version(self):
        """Context variables are set properly for deprecated tagged trait with no new version."""
        study = StudyFactory.create()
        self.user.profile.taggable_studies.add(study)
        self.user.refresh_from_db()
        source_study_version1 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=True, i_version=1)
        source_study_version2 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=False, i_version=2)
        trait1 = SourceTraitFactory.create(source_dataset__source_study_version=source_study_version1)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=trait1)
        response = self.client.get(self.get_url(deprecated_tagged_trait.pk))
        context = response.context
        self.assertTrue(context['is_deprecated'])
        self.assertTrue(context['show_removed_text'])
        self.assertIsNone(context['new_version_link'])
        self.assertContains(response, '<div class="alert alert-danger" role="alert" id="removed_deprecated_trait">')
        self.assertNotContains(response, '<div class="alert alert-danger" role="alert" id="updated_deprecated_trait">')

    def test_deprecated_tagged_trait_with_new_version(self):
        """Correct context variables for deprecated tagged trait with new version."""
        study = StudyFactory.create()
        self.user.profile.taggable_studies.add(study)
        self.user.refresh_from_db()
        tag = factories.TagFactory.create()
        source_study_version1 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=True, i_version=1)
        source_study_version2 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=False, i_version=2)
        source_dataset1 = SourceDatasetFactory.create(source_study_version=source_study_version1)
        source_dataset2 = SourceDatasetFactory.create(
            source_study_version=source_study_version2,
            i_accession=source_dataset1.i_accession,
            i_version=source_dataset1.i_version,
            i_is_subject_file=source_dataset1.i_is_subject_file,
            i_study_subject_column=source_dataset1.i_study_subject_column,
            i_dbgap_description=source_dataset1.i_dbgap_description
        )
        trait1 = SourceTraitFactory.create(source_dataset=source_dataset1)
        trait2 = SourceTraitFactory.create(
            source_dataset=source_dataset2,
            i_detected_type=trait1.i_detected_type,
            i_dbgap_type=trait1.i_dbgap_type,
            i_dbgap_variable_accession=trait1.i_dbgap_variable_accession,
            i_dbgap_variable_version=trait1.i_dbgap_variable_version,
            i_dbgap_comment=trait1.i_dbgap_comment,
            i_dbgap_unit=trait1.i_dbgap_unit,
            i_n_records=trait1.i_n_records,
            i_n_missing=trait1.i_n_missing,
            i_is_unique_key=trait1.i_is_unique_key,
            i_are_values_truncated=trait1.i_are_values_truncated
        )
        tagged_trait1 = factories.TaggedTraitFactory.create(trait=trait1, tag=tag)
        tagged_trait2 = factories.TaggedTraitFactory.create(trait=trait2, tag=tag, previous_tagged_trait=tagged_trait1)
        response = self.client.get(self.get_url(tagged_trait1.pk))
        context = response.context
        self.assertTrue(context['is_deprecated'])
        self.assertFalse(context['show_removed_text'])
        self.assertEqual(context['new_version_link'], tagged_trait2.get_absolute_url())
        self.assertContains(response, context['new_version_link'])
        self.assertNotContains(response, '<div class="alert alert-danger" role="alert" id="removed_deprecated_trait">')
        self.assertContains(response, '<div class="alert alert-danger" role="alert" id="updated_deprecated_trait">')

    def test_deprecated_tagged_trait_with_two_new_versions(self):
        """Correct context variables for deprecated tagged trait with two new versions."""
        study = StudyFactory.create()
        self.user.profile.taggable_studies.add(study)
        self.user.refresh_from_db()
        tag = factories.TagFactory.create()
        source_study_version1 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=True, i_version=1)
        source_study_version2 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=True, i_version=2)
        source_study_version3 = SourceStudyVersionFactory.create(study=study, i_is_deprecated=False, i_version=3)
        source_dataset1 = SourceDatasetFactory.create(source_study_version=source_study_version1)
        source_dataset2 = SourceDatasetFactory.create(
            source_study_version=source_study_version2,
            i_accession=source_dataset1.i_accession,
            i_version=source_dataset1.i_version,
            i_is_subject_file=source_dataset1.i_is_subject_file,
            i_study_subject_column=source_dataset1.i_study_subject_column,
            i_dbgap_description=source_dataset1.i_dbgap_description
        )
        source_dataset3 = SourceDatasetFactory.create(
            source_study_version=source_study_version3,
            i_accession=source_dataset1.i_accession,
            i_version=source_dataset1.i_version,
            i_is_subject_file=source_dataset1.i_is_subject_file,
            i_study_subject_column=source_dataset1.i_study_subject_column,
            i_dbgap_description=source_dataset1.i_dbgap_description
        )
        trait1 = SourceTraitFactory.create(source_dataset=source_dataset1)
        trait2 = SourceTraitFactory.create(
            source_dataset=source_dataset2,
            i_detected_type=trait1.i_detected_type,
            i_dbgap_type=trait1.i_dbgap_type,
            i_dbgap_variable_accession=trait1.i_dbgap_variable_accession,
            i_dbgap_variable_version=trait1.i_dbgap_variable_version,
            i_dbgap_comment=trait1.i_dbgap_comment,
            i_dbgap_unit=trait1.i_dbgap_unit,
            i_n_records=trait1.i_n_records,
            i_n_missing=trait1.i_n_missing,
            i_is_unique_key=trait1.i_is_unique_key,
            i_are_values_truncated=trait1.i_are_values_truncated
        )
        trait3 = SourceTraitFactory.create(
            source_dataset=source_dataset3,
            i_detected_type=trait1.i_detected_type,
            i_dbgap_type=trait1.i_dbgap_type,
            i_dbgap_variable_accession=trait1.i_dbgap_variable_accession,
            i_dbgap_variable_version=trait1.i_dbgap_variable_version,
            i_dbgap_comment=trait1.i_dbgap_comment,
            i_dbgap_unit=trait1.i_dbgap_unit,
            i_n_records=trait1.i_n_records,
            i_n_missing=trait1.i_n_missing,
            i_is_unique_key=trait1.i_is_unique_key,
            i_are_values_truncated=trait1.i_are_values_truncated
        )
        tagged_trait1 = factories.TaggedTraitFactory.create(trait=trait1, tag=tag)
        tagged_trait2 = factories.TaggedTraitFactory.create(trait=trait2, tag=tag, previous_tagged_trait=tagged_trait1)
        tagged_trait3 = factories.TaggedTraitFactory.create(trait=trait3, tag=tag, previous_tagged_trait=tagged_trait2)
        response = self.client.get(self.get_url(tagged_trait1.pk))
        context = response.context
        self.assertTrue(context['is_deprecated'])
        self.assertFalse(context['show_removed_text'])
        self.assertEqual(context['new_version_link'], tagged_trait3.get_absolute_url())
        self.assertContains(response, context['new_version_link'])
        self.assertNotContains(response, '<div class="alert alert-danger" role="alert" id="removed_deprecated_trait">')
        self.assertContains(response, '<div class="alert alert-danger" role="alert" id="updated_deprecated_trait">')


class TaggedTraitDetailPhenotypeTaggerTest(TaggedTraitDetailTestsMixin, PhenotypeTaggerLoginTestCase):

    def test_context_unreviewed(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response, reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response, reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response, reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertTrue(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_no_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_disagree_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_no_dccdecision'].dcc_review.study_response.comment)
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        # self.assertNotContains(response, self.tagged_traits[''].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_confirmed_dccreview(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['confirmed_dccreview'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertTrue(context['show_dcc_review_confirmed'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_no_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertNotContains(
            response,
            self.tagged_traits[
                'followup_dccreview_no_studyresponse_remove_dccdecision_archived'].dcc_review.dcc_decision.comment)
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_no_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertNotContains(
            response, self.tagged_traits[
                'followup_dccreview_no_studyresponse_confirm_dccdecision'].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_agree_studyresponse_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertTrue(context['show_study_agrees'])
        self.assertContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertFalse(context['show_decision_comment'])
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
            ].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertFalse(context['show_decision_comment'])
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(
            self.get_url(self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'
            ].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertNotContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'
            ].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')


class TaggedTraitDetailDCCAnalystTest(TaggedTraitDetailTestsMixin, DCCAnalystLoginTestCase):

    def test_context_unreviewed(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertTrue(context['show_dcc_review_add_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertTrue(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_no_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_disagree_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_no_dccdecision'
            ].dcc_review.study_response.comment)
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        # self.assertNotContains(response, self.tagged_traits[''].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_add_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_confirmed_dccreview(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['confirmed_dccreview'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertTrue(context['show_dcc_review_confirmed'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_no_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_no_studyresponse_remove_dccdecision_archived'].dcc_review.dcc_decision.comment)
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_no_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_no_studyresponse_confirm_dccdecision'].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_agree_studyresponse_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertTrue(context['show_study_agrees'])
        self.assertContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertFalse(context['show_decision_comment'])
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
            ].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
            ].dcc_review.dcc_decision.comment)
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
                    ].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
                    ].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
                    ].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
                    ].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')


class TaggedTraitDetailDCCDeveloperTest(TaggedTraitDetailTestsMixin, DCCDeveloperLoginTestCase):

    def test_context_unreviewed(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['unreviewed'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertTrue(context['show_dcc_review_add_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['unreviewed'].pk]))
        self.assertTrue(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_no_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_followup_dccreview_disagree_studyresponse_no_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_no_dccdecision'].dcc_review.study_response.comment)
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        # self.assertNotContains(response, self.tagged_traits[''].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_add_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_no_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], '')

    def test_context_confirmed_dccreview(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(self.tagged_traits['confirmed_dccreview'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertTrue(context['show_dcc_review_confirmed'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_dcc_review_needs_followup'])
        self.assertNotContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertFalse(context['show_decision_comment'])
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertTrue(context['show_dcc_review_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_traits['confirmed_dccreview'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_no_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_no_studyresponse_remove_dccdecision_archived'].dcc_review.dcc_decision.comment)
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_no_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        # self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertFalse(context['show_study_response_status'])
        self.assertNotContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_no_studyresponse_confirm_dccdecision'].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_no_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')

    def test_context_followup_dccreview_agree_studyresponse_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertTrue(context['show_study_agrees'])
        self.assertContains(response, 'should be removed')
        self.assertFalse(context['show_study_disagrees'])
        self.assertNotContains(response, 'should remain tagged')
        self.assertFalse(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertFalse(context['show_decision_comment'])
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_agree_studyresponse_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_remove_dccdecision_archived(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertNotContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
            ].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertTrue(context['show_decision_remove'])
        self.assertContains(response, 'will be removed by the DCC')
        self.assertFalse(context['show_decision_confirm'])
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'
            ].dcc_review.dcc_decision.comment)
        self.assertTrue(context['show_archived'])
        self.assertContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits[
                        'followup_dccreview_disagree_studyresponse_remove_dccdecision_archived'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-danger')

    def test_context_followup_dccreview_disagree_studyresponse_confirm_dccdecision(self):
        """Context variables and page content are as expected for this type of tagged trait."""
        response = self.client.get(self.get_url(
            self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context['show_quality_review_panel'])
        self.assertContains(response, '#collapse-reviewstatus')
        self.assertNotContains(response, 'not yet been reviewed')
        self.assertFalse(context['show_dcc_review_confirmed'])
        self.assertTrue(context['show_dcc_review_needs_followup'])
        self.assertContains(response, 'flagged for removal')
        self.assertTrue(context['show_study_response_status'])
        self.assertContains(response, 'The study')
        self.assertFalse(context['show_study_agrees'])
        self.assertNotContains(response, 'should be removed')
        self.assertTrue(context['show_study_disagrees'])
        self.assertContains(response, 'should remain tagged')
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review.study_response.comment)
        self.assertTrue(context['show_dcc_decision'])
        self.assertFalse(context['show_decision_remove'])
        self.assertNotContains(response, 'will be removed by the DCC')
        self.assertTrue(context['show_decision_confirm'])
        self.assertContains(response, 'confirmed by the DCC')
        self.assertTrue(context['show_decision_comment'])
        self.assertContains(
            response,
            self.tagged_traits[
                'followup_dccreview_disagree_studyresponse_confirm_dccdecision'].dcc_review.dcc_decision.comment)
        self.assertFalse(context['show_archived'])
        self.assertNotContains(response, 'has been removed by the DCC')
        self.assertFalse(context['show_dcc_review_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_review_update_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-review:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_dcc_decision_add_button'])
        self.assertNotContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:new',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertTrue(context['show_dcc_decision_update_button'])
        self.assertContains(
            response,
            reverse('tags:tagged-traits:pk:dcc-decision:update',
                    args=[self.tagged_traits['followup_dccreview_disagree_studyresponse_confirm_dccdecision'].pk]))
        self.assertFalse(context['show_delete_button'])
        self.assertEqual(context['quality_review_panel_color'], 'bg-success')


class TaggedTraitDetailOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:detail', args=args)

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def test_forbidden_non_taggers(self):
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.clear()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_wrong_taggable_study(self):
        """Returns 403 code when the user is from a different study."""
        other_study_tagged_trait = factories.TaggedTraitFactory.create()
        response = self.client.get(self.get_url(other_study_tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


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
        """Returns successful response code."""
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

    def test_no_deprecated_traits(self):
        """Counts exclude traits tagged from deprecated study versions."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        counts = response.context['taggedtrait_tag_counts_by_study']
        self.assertEqual(counts[0][1][0]['tt_count'], 1)

    def test_no_deprecated_traits_with_same_version_number(self):
        """Counts exclude traits tagged from deprecated study versions even with same version number."""
        # This directly addresses the unusual CARDIA situation where there are two study versions with the
        # same version number, one of which is deprecated.
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
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
        """Returns successful response code."""
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

    def test_no_deprecated_traits(self):
        """Counts exclude traits tagged from deprecated study versions."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        counts = response.context['taggedtrait_study_counts_by_tag']
        self.assertEqual(counts[0][1][0]['tt_count'], 1)

    def test_no_deprecated_traits_with_same_version_number(self):
        """Counts exclude traits tagged from deprecated study versions even with same version number."""
        # This directly addresses the unusual CARDIA situation where there are two study versions with the
        # same version number, one of which is deprecated.
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url())
        context = response.context
        counts = response.context['taggedtrait_study_counts_by_tag']
        self.assertEqual(counts[0][1][0]['tt_count'], 1)


class TaggedTraitByTagAndStudyListTestsMixin(object):

    def get_url(self, *args):
        return reverse('tags:tag:study:list', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """Returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
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

    def test_no_deprecated_traits(self):
        """Counts exclude traits tagged from deprecated study versions."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url(tag.pk, study.pk))
        context = response.context
        self.assertIn(current_tagged_trait, context['tagged_trait_table'].data)
        self.assertNotIn(old_tagged_trait, context['tagged_trait_table'].data)

    def test_no_deprecated_traits_with_same_version_number(self):
        """Counts exclude traits tagged from deprecated study versions even with same version number."""
        # This directly addresses the unusual CARDIA situation where there are two study versions with the
        # same version number, one of which is deprecated.
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        response = self.client.get(self.get_url(tag.pk, study.pk))
        context = response.context
        self.assertIn(current_tagged_trait, context['tagged_trait_table'].data)
        self.assertNotIn(old_tagged_trait, context['tagged_trait_table'].data)


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
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableForPhenotypeTaggersFromStudy)

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
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableForStaffByStudy)

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
        """Returns successful response code."""
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
        self.assertFormError(response, 'form', 'trait', 'This field is required.')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        self.assertFormError(response, 'form', 'trait', 'This field is required.')
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
        expected_error = forms.EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=self.tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
        self.assertFormError(response, 'form', 'trait', expected_error)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged_but_archived(self):
        """Tagging a trait fails when the trait has already been tagged with this tag and archived."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, archived=True)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        expected_error = forms.ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=self.tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_deprecated(self):
        """Can't tag a deprecated source trait."""
        sv = self.trait.source_dataset.source_study_version
        sv.i_is_deprecated = True
        sv.save()
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        self.assertFormError(response, 'form', 'trait',
                             'Select a valid choice. That choice is not one of the available choices.')
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
        self.assertFormError(
            response, 'form', 'trait',
            'Select a valid choice. That choice is not one of the available choices.')
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
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
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
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
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_wrong_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
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
        """Returns successful response code."""
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
        self.assertFormError(response, 'form', 'trait', 'This field is required.')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        self.assertFormError(response, 'form', 'trait', 'This field is required.')
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
        expected_error = forms.EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=self.tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
        self.assertFormError(response, 'form', 'trait', expected_error)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged_but_archived(self):
        """Tagging a trait fails when the trait has already been tagged with this tag but archived."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, archived=True)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        expected_error = forms.ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=self.tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
        self.assertFormError(response, 'form', 'trait', expected_error)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_deprecated(self):
        """Can't tag a deprecated source trait."""
        sv = self.trait.source_dataset.source_study_version
        sv.i_is_deprecated = True
        sv.save()
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'trait',
            'Select a valid choice. That choice is not one of the available choices.')
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
        self.assertFormError(
            response, 'form', 'trait',
            'Select a valid choice. That choice is not one of the available choices.')
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
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
        """Returns successful response code."""
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
        self.assertFormError(response, 'form', 'traits', '"" is not a valid value for a primary key.')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_all_traits(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': [], 'tag': self.tag.pk})
        self.assertFormError(response, 'form', 'traits', 'This field is required.')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
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
        expected_error = forms.EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=already_tagged.tag.title,
            phv=already_tagged.trait.full_accession,
            trait_name=already_tagged.trait.i_trait_name)
        self.assertFormError(response, 'form', 'traits', expected_error)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged_but_archived(self):
        """Tagging traits fails when a selected trait is already tagged with the tag but archived."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        expected_error = forms.ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=already_tagged.tag.title,
            phv=already_tagged.trait.full_accession,
            trait_name=already_tagged.trait.i_trait_name)
        self.assertFormError(response, 'form', 'traits', expected_error)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_deprecated(self):
        """Can't tag one deprecated source trait."""
        sv = self.traits[0].source_dataset.source_study_version
        sv.i_is_deprecated = True
        sv.save()
        response = self.client.post(self.get_url(), {'traits': [self.traits[0].pk], })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(self.traits[0].pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_of_two_traits_is_deprecated(self):
        """Can't tag one deprecated source trait."""
        deprecated_trait = SourceTraitFactory.create(source_dataset__source_study_version__i_is_deprecated=True)
        self.user.profile.taggable_studies.add(deprecated_trait.source_dataset.source_study_version.study)
        response = self.client.post(self.get_url(), {'traits': [self.traits[0].pk, deprecated_trait.pk], })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(deprecated_trait.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_deprecated(self):
        """Can't tag two deprecated source traits."""
        sv = self.traits[0].source_dataset.source_study_version
        sv.i_is_deprecated = True
        sv.save()
        response = self.client.post(self.get_url(), {'traits': self.traits[0].pk, 'tag': self.tag.pk, })
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(self.traits[0].pk))
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class ManyTaggedTraitsCreatePhenotypeTaggerTest(ManyTaggedTraitsCreateTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreatePhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study_version = SourceStudyVersionFactory.create(study=self.study)
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version=study_version)
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

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        other_trait = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [other_trait.pk], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(other_trait.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
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
        """Returns successful response code."""
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
        self.assertFormError(response, 'form', 'traits', '"" is not a valid value for a primary key.')
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [], })
        self.assertFormError(response, 'form', 'traits', 'This field is required.')
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
        expected_error = forms.EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=already_tagged.tag.title,
            phv=already_tagged.trait.full_accession,
            trait_name=already_tagged.trait.i_trait_name)
        self.assertFormError(response, 'form', 'traits', expected_error)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged_but_archived(self):
        """Tagging traits fails when a selected trait is already tagged with the tag but archived."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        expected_error = forms.ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
            tag_name=already_tagged.tag.title,
            phv=already_tagged.trait.full_accession,
            trait_name=already_tagged.trait.i_trait_name)
        self.assertFormError(response, 'form', 'traits', expected_error)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_deprecated(self):
        """Can't tag one deprecated source trait."""
        sv = self.traits[0].source_dataset.source_study_version
        sv.i_is_deprecated = True
        sv.save()
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [self.traits[0].pk], })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(self.traits[0].pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_of_two_traits_is_deprecated(self):
        """Can't tag one deprecated source trait."""
        deprecated_trait = SourceTraitFactory.create(source_dataset__source_study_version__i_is_deprecated=True)
        self.user.profile.taggable_studies.add(deprecated_trait.source_dataset.source_study_version.study)
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [self.traits[0].pk, deprecated_trait.pk], })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(deprecated_trait.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))


class ManyTaggedTraitsCreateByTagPhenotypeTaggerTest(ManyTaggedTraitsCreateByTagTestsMixin,
                                                     PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagPhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study_version = SourceStudyVersionFactory.create(study=self.study)
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version=study_version)
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
        other_trait = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [other_trait.pk], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'traits',
            'Select a valid choice. {} is not one of the available choices.'.format(other_trait.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """Returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """Returns 403 code when the user has no taggable_studies."""
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
        """DCC user can tag traits without any taggable_studies."""
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
        """Returns success code even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """Returns success code even when the DCC user has no taggable_studies."""
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
        """Returns successful response code."""
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

    def test_error_no_unreviewed_tagged_traits_with_study_and_tag(self):
        """Form has non-field error if there are no unreviewed tagged traits for this study with this tag."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        # Other unreviewed tagged traits for this tag must exist or you'll get an error on the tags field.
        other_study_unreviewed_tagged_trait = factories.TaggedTraitFactory.create(tag=tag)
        response = self.client.post(self.get_url(), {'tag': tag.pk, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # Form errors.
        self.assertIn('form', response.context)
        self.assertFormError(response, 'form', None, forms.DCCReviewTagAndStudySelectForm.ERROR_NO_TAGGED_TRAITS)
        # Make sure no variables were set.
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_error_with_no_tagged_traits_for_tag(self):
        """Form has error on tags if selecting a tag without any tagged traits."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        response = self.client.post(self.get_url(), {'tag': tag.pk, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFormError(response, 'form', 'tag',
                             'Select a valid choice. That choice is not one of the available choices.')
        # Make sure no session variables were set.
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_error_with_tag_with_completed_review(self):
        """Form has error on tags if selecting a tag without any unreviewed tagged traits."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        reviewed_tagged_trait = factories.TaggedTraitFactory.create(tag=tag)
        factories.DCCReviewFactory.create(tagged_trait=reviewed_tagged_trait)
        response = self.client.post(self.get_url(), {'tag': tag.pk, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFormError(response, 'form', 'tag',
                             'Select a valid choice. That choice is not one of the available choices.')
        # Make sure no session variables were set.
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

    def test_no_deprecated_traits_in_session_variable(self):
        """Sets session variable, without including deprecated tagged traits."""
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True)
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
        self.assertNotIn(deprecated_tagged_trait.pk, session_info['tagged_trait_pks'])
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
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
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
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), fetch_redirect_response=False)

    def test_nonexistent_study_404(self):
        """Returns 404 if study does not exist."""
        study_pk = self.study.pk
        self.study.delete()
        response = self.client.get(self.get_url(self.tag.pk, study_pk), follow=False)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_tag_404(self):
        """Returns 404 if tag does not exist."""
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

    def test_redirects_with_message_for_no_tagged_traits_to_review(self):
        """Redirects and displays message when there are no tagged traits to review for the tag+study."""
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

    def test_no_deprecated_traits_in_session_variable(self):
        """Sets session variable, without including deprecated tagged traits."""
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True)
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
        self.assertNotIn(deprecated_tagged_trait.pk, session_info['tagged_trait_pks'])
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
        """Get returns forbidden status code for non-DCC users."""
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

    def test_skips_deprecated_tagged_traits(self):
        """Skips a tagged trait that has been deprecated after starting the loop."""
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
        # Now deprecate one and try loading the view.
        study_version = tagged_traits[0].trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)


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
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
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
        """Returns successful response code."""
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
        dcc_review = models.DCCReview.objects.latest('created')
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
        dcc_review = models.DCCReview.objects.latest('created')
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

    def test_error_missing_comment(self):
        """Posting bad data to the form shows a form error and doesn't unset session variables."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'comment',
            'Comment cannot be blank for tagged variables that require followup.')
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
        """Returns 404 if the tagged trait for the session variable pk doesn't exist."""
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

    def test_deprecated_trait(self):
        """Shows warning message and does not save review if SourceTrait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))
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

    def test_get_session_variables_are_not_properly_set(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_post_session_variables_are_not_properly_set(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_get_session_variable_missing_key_tag_pk(self):
        """Redirects to select view if tag_pk is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_get_session_variable_missing_key_study_pk(self):
        """Redirects to select view if study_pk is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_get_session_variable_missing_key_tagged_trait_pks(self):
        """Redirects to select view if tagged_trait_pks is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_get_session_variable_missing_key_pk(self):
        """Redirects to select view if pk is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:next'), target_status_code=302)

    def test_post_session_variable_missing_key_tag_pk(self):
        """Redirects to select view if tag_pk is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_post_session_variable_missing_key_study_pk(self):
        """Redirects to select view if study_pk is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_post_session_variable_missing_key_tagged_trait_pks(self):
        """Redirects to select view if tagged_trait_pks is missing from session variable keys."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-review:select'))

    def test_post_session_variable_missing_key_pk(self):
        """Redirects to select view if pk is missing from session variable keys."""
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

    def test_shows_tag_only_once_when_it_is_archived(self):
        """The tag is only shown once, even when the tagged variable is archived."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertNotIn(self.tagged_trait.tag, context['other_tags'])
        self.assertNotIn(self.tagged_trait.tag, context['archived_other_tags'])


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
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
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
        """Returns successful response code."""
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
        """Posting valid data to the form correctly creates a confirmed DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly creates a 'need followup' DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'foo'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_form_error_with_missing_comment(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'comment',
            'Comment cannot be blank for tagged variables that require followup.')
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_non_existent_tagged_trait(self):
        """Get returns 404 if the tagged trait doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_non_existent_tagged_trait(self):
        """Post returns 404 if the session varaible pk doesn't exist."""
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
        """Get redirects with an error message if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """Post redirects with an error message if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_get_deprecated_tagged_trait(self):
        """Get redirects with an error message if the trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.tagged_trait.refresh_from_db()
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))

    def test_post_deprecated_tagged_trait(self):
        """Post redirects with an error message if the trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))

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
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_forbidden_get_request_with_existing_review(self):
        """Get returns forbidden status code for non-DCC user when review exists."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request_with_existing_review(self):
        """Post returns forbidden status code for non-DCC user when review exists."""
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
        """Returns successful response code."""
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

    def test_form_error_with_missing_comment(self):
        """Posting bad data to the form shows a form error."""
        existing_review = self.tagged_trait.dcc_review
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'comment',
            'Comment cannot be blank for tagged variables that require followup.')
        # Does not update the DCCReview for this TaggedTrait.
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertEqual(self.tagged_trait.dcc_review, existing_review)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_non_existent_tagged_trait(self):
        """Get returns a 404 page if the tagged trait doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.hard_delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_non_existent_tagged_trait(self):
        """Post returns a 404 page if the tagged trait doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.hard_delete()
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_dcc_review(self):
        """Get redirects to the create view with a warning if the DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('has not been reviewed yet', str(messages[0]))

    def test_post_nonexistent_dcc_review(self):
        """Post redirects to the create view with a warning if the DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('has not been reviewed yet', str(messages[0]))

    def test_get_archived_tagged_trait(self):
        """Get redirects to detail page if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('archived', str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """Post redirects to detail page if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('archived', str(messages[0]))

    def test_get_deprecated_tagged_trait(self):
        """Get redirects to detail page if the tagged trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))

    def test_post_deprecated_tagged_trait(self):
        """Post redirects to detail page if the tagged trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'new test comment'}
        response = self.client.post(url, form_data)
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.dcc_review.comment != 'new test comment')
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))

    def test_cant_update_dcc_review_if_study_has_responded(self):
        """Post redirects with a message if the study has responded."""
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
        """Redirects with a message if the study has responded."""
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

    def test_cant_update_dcc_review_if_dcc_decision_exists(self):
        """Posting data redirects with a message if a dcc decision exists."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review)
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

    def test_get_redirect_if_dcc_decision_exists(self):
        """Loading the page redirects with a message if the study has responded."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review)
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
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class TaggedTraitsNeedStudyResponseSummaryPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_view_success(self):
        """Returns successful response code."""
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

    def test_context_includes_taggedtrait_with_dccdecision_confirm_no_studyresponse(self):
        """Count does not include a TaggedTrait that has a confirm DCCDecision but no StudyResponse."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_context_includes_taggedtrait_with_dccdecision_remove_no_studyresponse(self):
        """Count does not include a TaggedTrait that has a remove DCCDecision but no StudyResponse."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)

    def test_context_includes_taggedtrait_with_dccdecision_confirm_studyresponse_disagree(self):
        """Count does not include a TaggedTrait that has a confirm DCCDecision and a disagree StudyResponse."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)

    def test_context_includes_taggedtrait_with_dccdecision_remove_studyresponse_disagree(self):
        """Count does not include a TaggedTrait that has a remove DCCDecision and a disagree StudyResponse."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 1)

    def test_includes_only_taggable_studies(self):
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

    def test_link_button_says_begin_if_no_tagged_traits_need_review(self):
        """Link button to tag+study study response table says 'begin' if responses are completed."""
        tag = factories.TagFactory.create()
        factories.StudyResponseFactory.create_batch(
            2,
            dcc_review__tagged_trait__tag=tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            dcc_review__status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        self.assertNotContains(response, 'Begin quality review')
        self.assertContains(response, 'View quality review')

    def test_begin_review_button_is_not_present_if_all_tagged_traits_are_archived_without_study_response(self):
        """Link button to tag+study study response table says 'view' if all tagged traits are archived."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2, tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        models.TaggedTrait.objects.update(archived=True)
        response = self.client.get(self.get_url())
        self.assertNotContains(response, 'Begin quality review')
        self.assertContains(response, 'View quality review')

    def test_begin_review_button_is_present_if_some_tagged_traits_need_review(self):
        """Link button to tag+study study response table says 'begin' if some responses need to be completed still."""
        tag = factories.TagFactory.create()
        factories.DCCReviewFactory.create_batch(
            2,
            tagged_trait__tag=tag,
            tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            status=models.DCCReview.STATUS_FOLLOWUP
        )
        response = self.client.get(self.get_url())
        self.assertContains(response, 'Begin quality review')
        self.assertNotContains(response, 'View quality review')

    def test_navbar_does_not_contain_link(self):
        """Phenotype taggers do see a link to the main quality review page in the navbar."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))

    def test_no_deprecated_traits(self):
        """Count does not include TaggedTraits whose SourceTrait has been deprecated."""
        tag = factories.TagFactory.create()
        study_version = SourceStudyVersionFactory.create(study=self.study)
        factories.StudyResponseFactory.create(
            dcc_review__tagged_trait__tag=tag,
            dcc_review__status=models.DCCReview.STATUS_FOLLOWUP,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version=study_version
        )
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)


class TaggedTraitsNeedStudyResponseSummaryDCCAnalystTest(DCCAnalystLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_get_forbidden(self):
        """Get returns forbidden status code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """DCC analysts do not see a link to the main quality review page in the navbar."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitsNeedStudyResponseSummaryOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:quality-review', args=args)

    def test_get_forbidden(self):
        """Get returns forbidden status code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """Regular users do not see a link to the main quality review page in the navbar."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitsNeedStudyResponseByTagAndStudyListTestsMixin(object):
    """Tests to include in all user type test cases for this view."""

    def test_view_with_invalid_study_pk(self):
        """Returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
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
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitDCCReviewTable)

    def test_includes_tagged_traits_that_need_followup(self):
        """Table includes TaggedTraits that need followup."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertEqual(len(table.data), len(self.dcc_reviews))
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))

    def test_excludes_unreviewed_tagged_trait(self):
        """Table excludes unreviewed TaggedTrait."""
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

    def test_excludes_tagged_trait_with_confirm_dccdecision_but_no_studyresponse(self):
        """Table excludes a TaggedTrait with no StudyResponse and a confirm DCCDecision."""
        tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review__tagged_trait=tagged_trait, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews))

    def test_excludes_tagged_trait_with_remove_dccdecision_but_no_studyresponse(self):
        """Table excludes a TaggedTrait with no StudyResponse and a remove DCCDecision."""
        tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review__tagged_trait=tagged_trait, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews))

    def test_includes_tagged_trait_with_confirm_dccdecision_with_studyresponse(self):
        """Table includes a TaggedTrait with disagree StudyResponse and a confirm DCCDecision."""
        tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study)
        study_response = factories.StudyResponseFactory.create(
            dcc_review__tagged_trait=tagged_trait, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertIn(tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews) + 1)

    def test_includes_tagged_trait_with_remove_dccdecision_with_studyresponse(self):
        """Table includes a TaggedTrait with disagree StudyResponse and a remove DCCDecision."""
        tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=self.study)
        study_response = factories.StudyResponseFactory.create(
            dcc_review__tagged_trait=tagged_trait, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertIn(tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews) + 1)

    def test_success_with_no_matching_tagged_traits(self):
        """Successful response code when there are no TaggedTraits to include."""
        other_tag = factories.TagFactory.create()
        response = self.client.get(self.get_url(other_tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(len(context['tagged_trait_table'].data), 0)

    def test_excludes_tagged_traits_from_a_different_study(self):
        """Table does not include TaggedTraits from a different study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=other_study)
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_excludes_tagged_traits_from_a_different_tag(self):
        """Table does not contain TaggedTraits from a different tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag, trait__source_dataset__source_study_version__study=self.study)
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_excludes_deprecated_tagged_trait(self):
        """Table excludes deprecated TaggedTrait."""
        study_version = SourceStudyVersionFactory.create(study=self.study)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version=study_version
        )
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=deprecated_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(deprecated_tagged_trait, table.data)
        for dcc_review in self.dcc_reviews:
            self.assertIn(dcc_review.tagged_trait, table.data,
                          msg='tagged_trait_table does not contain {}'.format(dcc_review.tagged_trait))
        self.assertEqual(len(table.data), len(self.dcc_reviews))


class TaggedTraitsNeedStudyResponseByTagAndStudyListPhenotypeTaggerTest(
        TaggedTraitsNeedStudyResponseByTagAndStudyListTestsMixin, PhenotypeTaggerLoginTestCase):

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
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_table_class(self):
        """Table class is correct."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertIs(type(response.context['tagged_trait_table']),
                      tables.TaggedTraitDCCReviewStudyResponseButtonTable)

    def test_forbidden_for_other_study(self):
        """Returns forbidden response code for a study that the user can't tag."""
        other_study = StudyFactory.create()
        response = self.client.get(self.get_url(self.tag.pk, other_study.pk))
        self.assertEqual(response.status_code, 403)

    def test_csrf_token(self):
        """Response contains a csrf token when study response buttons are present."""
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


class TaggedTraitsNeedStudyResponseByTagAndStudyListDCCAnalystTest(
        TaggedTraitsNeedStudyResponseByTagAndStudyListTestsMixin, DCCAnalystLoginTestCase):

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
        self.assertIs(type(response.context['tagged_trait_table']), tables.TaggedTraitDCCReviewTable)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)


class TaggedTraitsNeedStudyResponseByTagAndStudyListOtherUserTest(UserLoginTestCase):

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

    def test_get_forbidden(self):
        """Get returns forbidden response code for non-taggers and non-staff."""
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
        """Post returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for non-taggers."""
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

    def test_cant_create_study_response_for_tagged_trait_with_dcc_decision_confirm(self):
        """Redirects with warning message if the tagged trait has a confirm dcc decision."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('already has a dcc decision' in str(messages[0]))

    def test_cant_create_study_response_for_tagged_trait_with_dcc_decision_remove(self):
        """Redirects with warning message if the tagged trait has a remove dcc decision."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('already has a dcc decision' in str(messages[0]))

    def test_adds_user(self):
        """When a StudyResponse is successfully created, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(self.tagged_trait.dcc_review.study_response.creator, self.user)

    def test_archives_tagged_trait_after_response(self):
        """When a StudyResponse is successfully created, the tagged trait is archived."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)

    def test_get_deprecated_trait(self):
        """Redirects with warning message if the trait has been deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('newer version' in str(messages[0]))

    def test_post_deprecated_trait(self):
        """Redirects with warning message if the trait has been deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('newer version' in str(messages[0]))


class StudyResponseCreateAgreeDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:remove', args=args)

    def test_post_forbidden(self):
        """Post returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for non-taggers."""
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
        """Post returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for non-taggers."""
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
        self.assertFormError(response, 'form', 'comment', 'This field is required.')
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
        """Get redirects with warning message if DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has not been reviewed' in str(messages[0]))

    def test_post_missing_dcc_review(self):
        """Post redirects with warning message if a DCCReview doesn't exist."""
        self.tagged_trait.dcc_review.delete()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_get_archived_tagged_trait(self):
        """Get redirects with warning message if the tagged trait has been archived."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('removed' in str(messages[0]))

    def test_post_archived_tagged_trait(self):
        """Post redirects with warning message if the tagged trait has been archived."""
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
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('has been confirmed' in str(messages[0]))

    def test_cant_create_study_response_for_tagged_trait_with_dcc_decision_confirm(self):
        """Redirects to quality review page with warning message if the tagged trait has a confirm dcc decision."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('already has a dcc decision' in str(messages[0]))

    def test_cant_create_study_response_for_tagged_trait_with_dcc_decision_remove(self):
        """Redirects to quality review page with warning message if tagged trait has a remove dcc decision."""
        self.tagged_trait.dcc_review.delete()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'a comment'})
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('already has a dcc decision' in str(messages[0]))

    def test_get_studyresponse_exists(self):
        """Get redirects with warning message if a StudyResponse already exists."""
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
        """Post redirects with warning message if a StudyResponse already exists."""
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
        """Get returns forbidden status for tagged trait from a different study."""
        other_tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=other_tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(other_tagged_trait.pk))
        self.assertFalse(hasattr(other_tagged_trait.dcc_review, 'study_response'))
        self.assertEqual(response.status_code, 403)

    def test_post_cant_create_study_response_for_other_study_tagged_trait(self):
        """Post returns forbidden status for tagged trait from a different study."""
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

    def test_get_deprecated_trait(self):
        """Redirects a get request with warning message if the trait has been deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('newer version' in str(messages[0]))

    def test_post_deprecated_trait(self):
        """Redirects a post request with warning message if the trait has been deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'comment': 'foo'})
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'study_response'))
        self.assertRedirects(response, reverse('tags:tag:study:quality-review',
                                               args=[self.tag.pk, self.study.pk]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        self.assertTrue('newer version' in str(messages[0]))


class StudyResponseCreateDisagreeDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag)
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:quality-review:explain', args=args)

    def test_post_forbidden(self):
        """Post returns a 403 forbidden status code for non-taggers."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for non-taggers."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitsNeedDCCDecisionSummaryTestMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:need-decision', args=args)

    def test_view_success(self):
        """Returns successful response code."""
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

    def test_counts_exclude_deprecated_tagged_trait(self):
        study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
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

    def test_make_final_decisions_button_present(self):
        """Button to make final decisions (start the deciding loop) is present when some decisions remain unmade."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        response = self.client.get(self.get_url())
        study_tag_pks = [study_response.dcc_review.tagged_trait.tag.pk,
                         study_response.dcc_review.tagged_trait.trait.source_dataset.source_study_version.study.pk]
        self.assertContains(response, reverse('tags:tag:study:begin-dcc-decision', args=study_tag_pks))

    def test_make_final_decisions_button_not_present(self):
        """Button to make final decisions (start the deciding loop) is not present when all decisions are done."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url())
        study_tag_pks = [study_response.dcc_review.tagged_trait.tag.pk,
                         study_response.dcc_review.tagged_trait.trait.source_dataset.source_study_version.study.pk]
        self.assertNotContains(response, reverse('tags:tag:study:begin-dcc-decision', args=study_tag_pks))

    def test_navbar_does_contain_link(self):
        """DCC users do see a link to the dcc decisions summary page in the navbar."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.get_url())

    def test_counts_for_needfollowup_disagree_tagged_trait_deprecated(self):
        """No counts for a deprecated tagged trait that needs a decision."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        study_version = study_response.dcc_review.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('grouped_study_tag_counts', context)
        counts = context['grouped_study_tag_counts']
        self.assertEqual(len(counts), 0)


class TaggedTraitsNeedDCCDecisionSummaryDCCAnalystTest(TaggedTraitsNeedDCCDecisionSummaryTestMixin,
                                                       DCCAnalystLoginTestCase):

    pass


class TaggedTraitsNeedDCCDecisionSummaryDCCDeveloperTest(TaggedTraitsNeedDCCDecisionSummaryTestMixin,
                                                         DCCDeveloperLoginTestCase):

    pass


class TaggedTraitsNeedDCCDecisionSummaryOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:need-decision', args=args)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for regular users."""
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

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_navbar_does_not_contain_link(self):
        """Phenotype taggers do not see a link to the dcc decisions summary page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.get_url())


class TaggedTraitsNeedDCCDecisionByTagAndStudyListMixin(object):

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
        return reverse('tags:tag:study:need-decision', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """Returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """Returns 404 response code when the pk doesn't exist."""
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

    def test_view_table_does_not_contain_deprecated_tagged_traits(self):
        """Table does not contain deprecated TaggedTraits."""
        deprecated_response = factories.StudyResponseFactory.create(
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__i_is_deprecated=True,
            dcc_review__tagged_trait__tag=self.tag,
            status=models.StudyResponse.STATUS_DISAGREE)
        deprecated_tagged_trait = deprecated_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertNotIn(deprecated_tagged_trait, table.data)
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
        """Decision buttons are shown for tagged traits without decision."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        content = str(response.content)
        for study_response in self.study_responses:
            self.assertIn(
                reverse('tags:tagged-traits:pk:dcc-decision:new', args=[study_response.dcc_review.tagged_trait.pk]),
                content,
                msg='View is missing DCCDecisionCreate link for {}'.format(study_response.dcc_review.tagged_trait)
            )

    def test_update_link_present_for_decision_confirm_tagged_traits(self):
        """Update button is shown for tagged trait with confirm."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.study_responses[0].dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        content = str(response.content)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[dcc_decision.dcc_review.tagged_trait.pk]),
            content
        )

    def test_update_link_present_for_decision_remove_tagged_traits(self):
        """Update button is shown for tagged trait with remove."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.study_responses[0].dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        content = str(response.content)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[dcc_decision.dcc_review.tagged_trait.pk]),
            content
        )


class TaggedTraitsNeedDCCDecisionByTagAndStudyListDCCAnalystTest(TaggedTraitsNeedDCCDecisionByTagAndStudyListMixin,
                                                                 DCCAnalystLoginTestCase):

    pass


class TaggedTraitsNeedDCCDecisionByTagAndStudyListDCCDeveloperTest(TaggedTraitsNeedDCCDecisionByTagAndStudyListMixin,
                                                                   DCCDeveloperLoginTestCase):

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
        return reverse('tags:tag:study:need-decision', args=args)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for regular users."""
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
        return reverse('tags:tag:study:need-decision', args=args)

    def test_get_forbidden(self):
        """Get returns a 403 forbidden status code for regular users."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class DCCDecisionByTagAndStudySelectFromURLDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            10, status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        return reverse('tags:tag:study:begin-dcc-decision', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), fetch_redirect_response=False)

    def test_nonexistent_study_404(self):
        """Returns 404 if study does not exist."""
        study_pk = self.study.pk
        self.study.delete()
        response = self.client.get(self.get_url(self.tag.pk, study_pk), follow=False)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_tag_404(self):
        """Returns 404 if tag does not exist."""
        tag_pk = self.tag.pk
        self.tag.delete()
        response = self.client.get(self.get_url(tag_pk, self.study.pk), follow=False)
        self.assertEqual(response.status_code, 404)

    def test_sets_session_variables(self):
        """View has appropriate data in the context and session variables."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), fetch_redirect_response=False)

    def test_excludes_other_tag(self):
        """List of tagged trait pks does not include a second tag."""
        other_tag = factories.TagFactory.create()
        other_study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=other_tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study
        )
        other_tagged_trait = other_study_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), fetch_redirect_response=False)

    def test_excludes_other_study(self):
        """List of tagged trait pks does not include a different study."""
        other_study = StudyFactory.create()
        other_study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=other_study
        )
        other_tagged_trait = other_study_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk), follow=False)
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), fetch_redirect_response=False)

    def test_excludes_other_study_and_tag(self):
        """List of tagged trait pks does not include tagged traits from another study and tag."""
        other_tag = factories.TagFactory.create()
        other_study = StudyFactory.create()
        other_study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=other_tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=other_study
        )
        other_tagged_trait = other_study_response.dcc_review.tagged_trait
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), fetch_redirect_response=False)

    def test_resets_session_variables(self):
        """Correctly overwrites a preexisting session variable with new data."""
        self.client.session['tagged_trait_decision_by_tag_and_study_info'] = {
            'study_pk': self.study.pk + 1,
            'tag_pk': self.tag.pk + 1,
            'tagged_trait_pks': [],
        }
        self.client.session.save()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))

    def test_no_tagged_traits_remaining_to_decide_on(self):
        """Redirects properly and displays message when there are no tagged traits to decide on for the tag+study."""
        models.TaggedTrait.objects.all().hard_delete()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 302)
        # Check for message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('No tagged variables to decide on', str(messages[0]))

    def test_no_archived_taggedtraits_in_session_variable(self):
        """Does not include archived tagged traits in session variables."""
        archived_tagged_trait = self.tagged_traits[0]
        archived_tagged_trait.archive()
        archived_tagged_trait.refresh_from_db()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits[1:]:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(archived_tagged_trait.pk, session_info['tagged_trait_pks'])
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_deprecated_taggedtraits_in_session_variable(self):
        """Does not include deprecated tagged traits in session variables."""
        deprecated_tagged_trait = self.tagged_traits[0]
        study_version = deprecated_tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        deprecated_tagged_trait.refresh_from_db()
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits[1:]:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(deprecated_tagged_trait.pk, session_info['tagged_trait_pks'])
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)


class DCCDecisionByTagAndStudySelectFromURLDCCAnalystTest(DCCDecisionByTagAndStudySelectFromURLDCCTestsMixin,
                                                          DCCAnalystLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudySelectFromURLDCCTestsMixin as a DCC analyst.
    pass


class DCCDecisionByTagAndStudySelectFromURLDCCDeveloperTest(DCCDecisionByTagAndStudySelectFromURLDCCTestsMixin,
                                                            DCCDeveloperLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudySelectFromURLDCCTestsMixin as a DCC developer.
    pass


class DCCDecisionByTagAndStudySelectFromURLOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            10, status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        return reverse('tags:tag:study:begin-dcc-decision', args=args)

    def test_forbidden_get_request(self):
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 403)


class DCCDecisionByTagAndStudyNextDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            10, status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-decision:next', args=args)

    def test_view_success_with_no_session_variables(self):
        """Redirects to need_decision summary page when no session variables are set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_view_success_with_tagged_traits_to_decision(self):
        """Redirects to decision loop when there are tagged traits to decide on."""
        tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        response = self.client.get(self.get_url())
        # Make sure a pk session variable was set
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        self.assertIn('pk', session['tagged_trait_decision_by_tag_and_study_info'])
        self.assertEqual(session['tagged_trait_decision_by_tag_and_study_info']['pk'], tagged_trait.pk)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:decide'))
        # Check messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('You have 1 tagged variable left to decide on.', str(messages[0]))

    def test_view_success_with_no_tagged_traits_left(self):
        """Redirects to need_decision summary by tag and study when no tagged traits are left to decide on."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tag:study:need-decision', args=[self.tag.pk, self.study.pk]))
        # Check that there are no messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_session_variables_are_unset_when_decisions_completed(self):
        """Unsets session variables when no tagged traits are left to decide on."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)

    def test_skips_tagged_trait_with_decision(self):
        """Skips a tagged trait that has been decided on after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        factories.DCCDecisionFactory.create(dcc_review=first_tagged_trait.dcc_review)
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn('pk', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_skips_deleted_tagged_trait(self):
        """Skips a tagged trait that has been deleted after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_tagged_trait.hard_delete()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_archived_tagged_trait(self):
        """Skips a tagged trait that has been archived after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_tagged_trait.archive()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_no_review_tagged_trait(self):
        """Skips a tagged trait that has no dcc review after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_dcc_review = first_tagged_trait.dcc_review
        first_dcc_review.hard_delete()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_review_confirmed_tagged_trait(self):
        """Skips a tagged trait that has been reviewed as confirmed after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_dcc_review = first_tagged_trait.dcc_review
        first_dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        first_dcc_review.save()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_no_response_tagged_trait(self):
        """Skips a tagged trait that has no study response after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_study_response = first_tagged_trait.dcc_review.study_response
        first_study_response.delete()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_response_agree_tagged_trait(self):
        """Skips a tagged trait that has a study response agree after starting the loop."""
        first_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        first_study_response = first_tagged_trait.dcc_review.study_response
        first_study_response.status = models.StudyResponse.STATUS_AGREE
        first_study_response.save()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(first_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_skips_deprecated_tagged_trait(self):
        """Skips a tagged trait that has been deprecated after starting the loop."""
        deprecated_tagged_trait = self.tagged_traits[0]
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'tag_pk': self.tag.pk,
            'study_pk': self.study.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits],
        }
        session.save()
        study_version = deprecated_tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(deprecated_tagged_trait.pk, session_info['tagged_trait_pks'])
        self.assertEqual(self.tagged_traits[1].pk, session_info['tagged_trait_pks'][0])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_session_variables_are_not_properly_set(self):
        """Redirects to summary view if expected session variable is not set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_session_variable_missing_required_keys(self):
        """Redirects to summary view if expected session variable dictionary keys are missing."""
        template = {
            'study_pk': self.study.pk,
            'tag_pk': self.tag.pk,
            'tagged_trait_pks': [x.pk for x in self.tagged_traits]
        }
        for key in template.keys():
            session_info = copy.copy(template)
            session_info.pop(key)
            session = self.client.session
            session['tagged_trait_decision_by_tag_and_study_info'] = session_info
            session.save()
            response = self.client.get(self.get_url())
            self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
            self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'),
                                 msg_prefix='did not redirect when missing {} in session'.format(key))


class DCCDecisionByTagAndStudyNextDCCAnalystTest(DCCDecisionByTagAndStudyNextDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudyNextDCCTestsMixin, as a DCC analyst.
    pass


class DCCDecisionByTagAndStudyNextDCCDeveloperTest(DCCDecisionByTagAndStudyNextDCCTestsMixin,
                                                   DCCDeveloperLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudyNextDCCTestsMixin, as a DCC developer.
    pass


class DCCDecisionByTagAndStudyNextOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            10, status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_traits = list(models.TaggedTrait.objects.all())

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-decision:next', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)


class DCCDecisionByTagAndStudyDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        # Set expected session variables.
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'study_pk': self.study.pk,
            'tag_pk': self.tag.pk,
            'tagged_trait_pks': [self.tagged_trait.pk],
            'pk': self.tagged_trait.pk,
        }
        session.save()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-decision:decide', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCDecisionByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], 1)

    def test_context_data_with_multiple_remaining_tagged_traits(self):
        """View has appropriate data in the context if there are multiple tagged traits to decide on."""
        more_study_responses = factories.StudyResponseFactory.create_batch(
            3, status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        session = self.client.session
        tagged_trait_list = list(models.TaggedTrait.objects.values_list('pk', flat=True))
        session['tagged_trait_decision_by_tag_and_study_info']['tagged_trait_pks'] = tagged_trait_list
        session.save()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCDecisionByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], models.TaggedTrait.objects.count())

    def test_successful_post_confirm_decision(self):
        """Posting valid data to the form correctly creates a DCCDecision."""
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCDecision for this TaggedTrait.
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully made a final decision', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_successful_post_remove_decision(self):
        """Posting valid data to the form correctly creates a DCCDecision."""
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': 'Definitely remove it.'}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCDecision for this TaggedTrait.
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully made a final decision', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_post_invalid_missing_comment(self):
        """Posting bad data to the form shows a form error and doesn't unset session variables."""
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not create a DCCDecision for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        self.assertFormError(response, 'form', 'comment', 'Comment cannot be blank.')
        # The pk session variable is not unset.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertIn('pk', session_info)
        self.assertEqual(session_info['pk'], self.tagged_trait.pk)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_successfully_skip_tagged_trait(self):
        """Skipping a TaggedTrait unsets pk and redirects to the next view."""
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_SKIP: 'Skip'}
        response = self.client.post(self.get_url(), form_data)
        # Does not create a DCCDecision for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        # Session variables are properly set/unset.
        session = self.client.session
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', session)
        session_info = session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # The redirect view unsets some session variables, so check it at the end.
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_failure_for_non_existent_tagged_trait(self):
        """Returns a 404 page if the session variable pk doesn't exist."""
        self.tagged_trait.hard_delete()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 404)

    def test_message_and_redirect_for_archived_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait is archived."""
        self.tagged_trait.archive()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_archived_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is archived, even if there's a form error."""
        self.tagged_trait.archive()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_no_review_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait is missing dcc review."""
        self.tagged_trait.dcc_review.hard_delete()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('missing a dcc review', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_no_review_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is missing dcc review, even if there's a form error."""
        self.tagged_trait.dcc_review.hard_delete()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('missing a dcc review', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_confirmed_review_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait has review status confirmed."""
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('dcc review status is "confirmed"', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_confirmed_review_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if review status confirmed, even if there's a form error."""
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('dcc review status is "confirmed"', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_no_response_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait is missing study response."""
        self.tagged_trait.dcc_review.study_response.delete()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('missing a study response', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_no_response_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if missing study response, even if there's a form error."""
        self.tagged_trait.dcc_review.study_response.delete()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('missing a study response', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_agree_response_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait study response is agree."""
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('study response status is "agree"', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_agree_response_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if study response is agree, even if there's a form error."""
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('study response status is "agree"', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_tagged_trait_with_decision(self):
        """Shows warning message and does not save decision if TaggedTrait is already decided."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE
        )
        # Now try to decide on it (with different decision) through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already has a decision made', str(messages[0]))
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_tagged_trait_with_decision_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait already has decision, even if there's a form error."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_CONFIRM,
            comment='looks good'
        )
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already has a decision made', str(messages[0]))
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_successful_skip_tagged_trait_with_decision(self):
        """Redirects without a message if an already-decided tagged trait is skipped."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_CONFIRM,
            comment='looks good'
        )
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_SKIP: 'Skip', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check that no message was generated.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_get_redirects_if_session_variables_are_not_properly_set(self):
        """Get redirects to summary view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_decision_by_tag_and_study_info']
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_post_redirects_if_session_variables_are_not_properly_set(self):
        """Post redirects to summary view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_decision_by_tag_and_study_info']
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_get_redirects_if_session_variable_missing_key_tag_pk(self):
        """Get redirects to summary view if tag pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_get_redirects_if_session_variable_missing_key_study_pk(self):
        """Get redirects to select view if study pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_get_redirects_if_session_variable_missing_key_tagged_trait_pks(self):
        """Get redirects to select view if tagged trait pks expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_get_redirects_if_session_variable_missing_key_pk(self):
        """Get redirects to summary view if pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_post_redirects_if_session_variable_missing_key_tag_pk(self):
        """Post redirects to select view if tag pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_post_redirects_if_session_variable_missing_key_study_pk(self):
        """Post redirects to select view if study pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_post_redirects_if_session_variable_missing_key_tagged_trait_pks(self):
        """Post redirects to select view if trait pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:need-decision'))

    def test_post_redirects_if_session_variable_missing_key_pk(self):
        """Post redirects to select view if tagged trait pk expected session variable dictionary key is missing."""
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_shows_other_tags(self):
        """Other tags linked to the same trait are shown on the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_archived_other_tags(self):
        """Other tags linked to the same trait are shown on the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait, archived=True)
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_tag_only_once_when_it_is_archived(self):
        """The tag is only shown once, even when the tagged variable is archived."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertNotIn(self.tagged_trait.tag, context['other_tags'])
        self.assertNotIn(self.tagged_trait.tag, context['archived_other_tags'])

    def test_archives_tagged_trait_with_dccdecision_remove(self):
        """Creating a remove DCCDecision archives the tagged trait."""
        self.assertFalse(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': 'get rid of it'}
        response = self.client.post(self.get_url(), form_data)
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_tagged_trait_nonarchived_after_dccdecision_confirm(self):
        """Creating a confirm DCCDecision results in the tagged trait being non-archived."""
        self.assertFalse(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(), form_data)
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.tagged_trait.refresh_from_db()
        self.assertFalse(self.tagged_trait.archived)
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_deprecated_tagged_trait(self):
        """Shows warning message and does not save decision if TaggedTrait's study version is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'Looks good.'}
        response = self.client.post(self.get_url(), form_data)
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)

    def test_message_and_redirect_for_deprecated_tagged_trait_with_form_error(self):
        """Shows warning message and does not save decision if TaggedTrait's study version is deprecated, with form error.""" # noqa
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        # Now try to decide on it through the web interface.
        form_data = {forms.DCCDecisionByTagAndStudyForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        # Check session variables.
        self.assertIn('tagged_trait_decision_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_decision_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))
        self.assertRedirects(response, reverse('tags:tagged-traits:dcc-decision:next'), target_status_code=302)


class DCCDecisionByTagAndStudyDCCAnalystTest(DCCDecisionByTagAndStudyDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudyDCCTestsMixin, as a DCC analyst.
    pass


class DCCDecisionByTagAndStudyDCCDeveloperTest(DCCDecisionByTagAndStudyDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCDecisionByTagAndStudyDCCTestsMixin, as a DCC developer.
    pass


class DCCDecisionByTagAndStudyOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.study_response = factories.StudyResponseFactory.create(
            status=models.StudyResponse.STATUS_DISAGREE, dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        # Set expected session variables.
        session = self.client.session
        session['tagged_trait_decision_by_tag_and_study_info'] = {
            'study_pk': self.study.pk,
            'tag_pk': self.tag.pk,
            'tagged_trait_pks': [self.tagged_trait.pk],
            'pk': self.tagged_trait.pk,
        }
        session.save()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:dcc-decision:decide', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)


class DCCDecisionCreateDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        self.need_decision_url = reverse('tags:tag:study:need-decision',
                                         args=[self.tagged_trait.tag.pk,
                                               self.tagged_trait.trait.source_dataset.source_study_version.study.pk])

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-decision:new', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCDecisionForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_post_confirm_decision_creates_decision(self):
        """Posting valid data to the form correctly creates a DCCDecision."""
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        # Correctly creates a DCCDecision for this TaggedTrait.
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully made final decision for', str(messages[0]))

    def test_remove_decision_creates_decision(self):
        """Posting valid data to the form correctly creates a DCCDecision."""
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': 'foo'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        # Correctly creates a DCCDecision for this TaggedTrait.
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully made final decision for', str(messages[0]))

    def test_form_error_missing_comment_for_remove(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'comment', 'Comment cannot be blank.')
        # Does not create a DCCDecision for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_form_error_missing_comment_for_confirm(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'comment', 'Comment cannot be blank.')
        # Does not create a DCCDecision for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_view_with_invalid_tagged_trait_pk(self):
        """Returns a 404 page with a get request if the tagged trai doesn't exist."""
        url = self.get_url(self.tagged_trait.pk + 1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_view_with_invalid_tagged_trait_pk(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        url = self.get_url(self.tagged_trait.pk + 1)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_message_and_redirect_archived_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_post_message_and_redirect_archived_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait is archived."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_post_message_and_redirect_archived_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if the tagged trait is archived, even with bad data."""
        self.tagged_trait.archive()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('been archived', str(messages[0]))

    def test_get_message_and_redirect_missing_review_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has no dcc review."""
        self.tagged_trait.dcc_review.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_missing_review_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has no dcc review."""
        self.tagged_trait.dcc_review.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_missing_review_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if no dcc review, even with bad data."""
        self.tagged_trait.dcc_review.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_get_message_and_redirect_review_confirmed_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has dcc review status confirmed."""
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_review_confirmed_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has dcc review status confirmed."""
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_review_confirmed_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if dcc review status confirmed, even with bad data."""
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_get_message_and_redirect_missing_response_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has no study response."""
        self.tagged_trait.dcc_review.study_response.delete()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_missing_response_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has no study response."""
        self.tagged_trait.dcc_review.study_response.delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_missing_response_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if no study response, even with bad data."""
        self.tagged_trait.dcc_review.study_response.delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_get_message_and_redirect_response_agree_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has study response status agree."""
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_response_agree_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has study response status agree."""
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_post_message_and_redirect_response_agree_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if study response status agree, even with bad data."""
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot create', str(messages[0]))

    def test_get_message_and_redirect_to_update_for_previous_decision(self):
        """Shows warning message and redirects to update page if TaggedTrait is already decided."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE
        )
        # Now try to review it through the web interface.
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to updating decision', str(messages[0]))
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)

    def test_post_message_and_redirect_to_update_for_previous_decision(self):
        """Shows warning message and does not save decision if TaggedTrait is already decided."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to updating', str(messages[0]))
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)

    def test_post_message_and_redirect_to_update_for_previous_decision_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is already decided, with a form error."""
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review,
            decision=models.DCCDecision.DECISION_REMOVE
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:update', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to updating', str(messages[0]))
        # The previous DCCDecision was not updated.
        self.assertEqual(self.tagged_trait.dcc_review.dcc_decision, dcc_decision)

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

    def test_archives_tagged_trait_with_dccdecision_remove(self):
        """Creating a remove DCCDecision archives the tagged trait."""
        self.assertFalse(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': 'get rid of it'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)

    def test_tagged_trait_nonarchived_after_dccdecision_confirm(self):
        """Creating a confirm DCCDecision results in the tagged trait being non-archived."""
        self.assertFalse(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        dcc_decision = models.DCCDecision.objects.latest('created')
        self.tagged_trait.refresh_from_db()
        self.assertFalse(self.tagged_trait.archived)

    def test_get_message_and_redirect_response_deprecated_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Oops!', str(messages[0]))
        self.assertIn('newer version', str(messages[0]))

    def test_post_message_and_redirect_response_deprecated_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait is deprecated."""
        study_version = self.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.tagged_trait.refresh_from_db()
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Oops!', str(messages[0]))
        self.assertIn('newer version', str(messages[0]))


class DCCDecisionCreateDCCAnalystTest(DCCDecisionCreateDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCDecisionCreateDCCTestsMixin, as a DCC analyst.
    pass


class DCCDecisionCreateDCCDeveloperTest(DCCDecisionCreateDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCDecisionCreateDCCTestsMixin, as a DCC developer.
    pass


class DCCDecisionCreateOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-decision:new', args=args)

    def test_forbidden_get_request(self):
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_forbidden_get_request_with_existing_decision(self):
        """Get returns forbidden status code for non-DCC users when decision exists."""
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request_with_existing_decision(self):
        """Post returns forbidden status code for non-DCC users when decision exists."""
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class DCCDecisionUpdateDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        self.dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        self.need_decision_url = reverse('tags:tag:study:need-decision',
                                         args=[self.tagged_trait.tag.pk,
                                               self.tagged_trait.trait.source_dataset.source_study_version.study.pk])

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-decision:update', args=args)

    def test_view_success_code(self):
        """Returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCDecisionForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_post_confirm_decision_updates_comment(self):
        """Posting valid data to the form correctly updates a DCCDecision by changing comment."""
        original_comment = self.dcc_decision.comment
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        self.dcc_decision.refresh_from_db()
        # Correctly updates a DCCDecision for this TaggedTrait.
        updated_dcc_decision = models.DCCDecision.objects.latest('modified')
        self.assertEqual(self.dcc_decision, updated_dcc_decision)
        self.assertNotEqual(self.dcc_decision.comment, original_comment)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_post_remove_decision_updates_decision_and_comment(self):
        """Posting valid data to the form correctly updates a DCCDecision decision and comment."""
        original_comment = self.dcc_decision.comment
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': 'foo'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        self.dcc_decision.refresh_from_db()
        # Correctly updates a DCCDecision for this TaggedTrait.
        updated_dcc_decision = models.DCCDecision.objects.latest('modified')
        self.assertEqual(self.dcc_decision, updated_dcc_decision)
        self.assertNotEqual(self.dcc_decision.comment, original_comment)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_change_confirm_to_remove(self):
        """Updating a dcc decision from confirm to remove is successful."""
        self.dcc_decision.delete()
        self.dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': 'remove it'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        self.dcc_decision.refresh_from_db()
        updated_dcc_decision = models.DCCDecision.objects.latest('modified')
        self.assertEqual(self.dcc_decision, updated_dcc_decision)
        self.assertEqual(self.dcc_decision.decision, models.DCCDecision.DECISION_REMOVE)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_change_remove_to_confirm(self):
        """Updating a dcc decision from remove to confirm is successful."""
        self.dcc_decision.delete()
        self.dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        self.tagged_trait.archive()
        self.tagged_trait.refresh_from_db()
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'keep it'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.need_decision_url)
        self.dcc_decision.refresh_from_db()
        updated_dcc_decision = models.DCCDecision.objects.latest('modified')
        self.assertEqual(self.dcc_decision, updated_dcc_decision)
        self.assertEqual(self.dcc_decision.decision, models.DCCDecision.DECISION_CONFIRM)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_form_error_missing_comment_for_remove(self):
        """Posting bad data to the form shows a form error and does not update decision."""
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.dcc_decision.refresh_from_db()
        self.assertFormError(response, 'form', 'comment', 'Comment cannot be blank.')
        # Does not modify a DCCDecision for this TaggedTrait.
        self.assertNotEqual(self.dcc_decision.comment, form_data['comment'])
        self.assertNotEqual(self.dcc_decision.decision, models.DCCDecision.DECISION_REMOVE)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_form_error_missing_comment_for_confirm(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        self.dcc_decision.refresh_from_db()
        self.assertFormError(response, 'form', 'comment', 'Comment cannot be blank.')
        # Does not modify a DCCDecision for this TaggedTrait.
        self.assertNotEqual(self.dcc_decision.comment, form_data['comment'])
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_view_with_invalid_tagged_trait_pk(self):
        """Returns a 404 page with a get request if the tagged trai doesn't exist."""
        url = self.get_url(self.tagged_trait.pk + 1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_view_with_invalid_tagged_trait_pk(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        url = self.get_url(self.tagged_trait.pk + 1)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_message_and_redirect_missing_review_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has no dcc review."""
        self.tagged_trait.dcc_review.hard_delete()  # Also deletes dcc_decision and study_response!
        # Reset the objects saved to this testcase.
        self.tagged_trait = models.TaggedTrait.objects.get(pk=self.tagged_trait.pk)
        self.study_response = None
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url, follow=True)
        create_decision_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk])
        # Redirects first to the create page, then to the need_decision page.
        self.assertEqual(response.redirect_chain, [(create_decision_url, 302, ), (self.need_decision_url, 302, )])
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Switched to creating', str(messages[0]))
        self.assertIn('Cannot create', str(messages[1]))
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))

    def test_post_message_and_redirect_missing_review_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has no dcc review."""
        self.tagged_trait.dcc_review.hard_delete()  # Also deletes dcc_decision and study_response!
        # Reset the objects saved to this testcase.
        self.tagged_trait = models.TaggedTrait.objects.get(pk=self.tagged_trait.pk)
        self.study_response = None
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data, follow=True)
        create_decision_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk])
        # Redirects first to the create page, then to the need_decision page.
        self.assertEqual(response.redirect_chain, [(create_decision_url, 302, ), (self.need_decision_url, 302, )])
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Switched to creating', str(messages[0]))
        self.assertIn('Cannot create', str(messages[1]))
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))

    def test_post_message_and_redirect_missing_review_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if no dcc review, even with bad data."""
        self.tagged_trait.dcc_review.hard_delete()  # Also deletes dcc_decision and study_response!
        # Reset the objects saved to this testcase.
        self.tagged_trait = models.TaggedTrait.objects.get(pk=self.tagged_trait.pk)
        self.study_response = None
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data, follow=True)
        create_decision_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk])
        # Redirects first to the create page, then to the need_decision page.
        self.assertEqual(response.redirect_chain, [(create_decision_url, 302, ), (self.need_decision_url, 302, )])
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Switched to creating', str(messages[0]))
        self.assertIn('Cannot create', str(messages[1]))
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))

    def test_get_message_and_redirect_review_confirmed_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has dcc review status confirmed."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_post_message_and_redirect_review_confirmed_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has dcc review status confirmed."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_post_message_and_redirect_review_confirmed_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if dcc review status confirmed, even with bad data."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.status = models.DCCReview.STATUS_CONFIRMED
        self.tagged_trait.dcc_review.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_get_success_missing_response_tagged_trait(self):
        """Get response is successful if the tagged trait has no study response."""
        self.tagged_trait.dcc_review.study_response.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_post_updates_decision_missing_response_tagged_trait(self):
        """Post request successfully updates decision when the tagged trait has no study response."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.study_response.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertNotEqual(original_comment, self.dcc_decision.comment)
        self.assertEqual(self.dcc_decision.comment, form_data['comment'])
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully updated', str(messages[0]))

    def test_post_does_not_redirect_with_missing_response_tagged_trait_with_form_error(self):
        """Post request does not give message and redirect, but doesn't update decision when study response is missing and data is bad."""  # noqa
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.study_response.hard_delete()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_message_and_redirect_response_agree_tagged_trait(self):
        """Get request gives a warning message and redirects if the tagged trait has study response status agree."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        response = self.client.get(url)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_post_message_and_redirect_response_agree_tagged_trait(self):
        """Post request gives a warning message and redirects if the tagged trait has study response status agree."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_post_message_and_redirect_response_agree_tagged_trait_with_form_error(self):
        """Post request gives a warning message and redirects if study response status agree, even with bad data."""
        original_comment = self.dcc_decision.comment
        self.tagged_trait.dcc_review.study_response.status = models.StudyResponse.STATUS_AGREE
        self.tagged_trait.dcc_review.study_response.save()
        url = self.get_url(self.tagged_trait.pk)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Cannot update', str(messages[0]))

    def test_get_message_and_redirect_to_create_for_missing_decision(self):
        """Shows warning message and redirects to create page if TaggedTrait has no decision."""
        # Delete the DCC Decision and reset the other objects saved to this testcase.
        self.dcc_decision.delete()
        self.study_response = models.StudyResponse.objects.get(pk=self.study_response.pk)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to creating', str(messages[0]))
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))

    def test_post_message_and_redirect_to_create_for_missing_decision(self):
        """Shows warning message, does not update, and redirects to create view if TaggedTrait has no decision."""
        # Delete the DCC Decision and reset the other objects saved to this testcase.
        self.dcc_decision.delete()
        self.study_response = models.StudyResponse.objects.get(pk=self.study_response.pk)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to creating', str(messages[0]))
        # The input DCCDecision was not saved.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))

    def test_post_message_and_redirect_to_create_for_missing_decision_with_form_error(self):
        """Shows warning message, does not update, and redirects to create if no decision exists and data is bad."""
        # Delete the DCC Decision and reset the other objects saved to this testcase.
        self.dcc_decision.delete()
        self.study_response = models.StudyResponse.objects.get(pk=self.study_response.pk)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait
        self.dcc_decision = None
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.tagged_trait.dcc_review.refresh_from_db()
        self.assertRedirects(
            response, reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk]))
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Switched to creating', str(messages[0]))
        # The input DCCDecision was not saved.
        self.assertFalse(hasattr(self.tagged_trait.dcc_review, 'dcc_decision'))

    def test_shows_other_tags(self):
        """Other tags linked to the same trait are shown on the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_archived_other_tags(self):
        """Other tags linked to the same trait are shown on the page."""
        another_tagged_trait = factories.TaggedTraitFactory.create(trait=self.tagged_trait.trait, archived=True)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertIn(another_tagged_trait.tag.title, content)
        self.assertIn(self.tagged_trait.tag.title, content)

    def test_shows_tag_only_once_when_it_is_archived(self):
        """The tag is only shown once, even when the tagged variable is archived."""
        self.tagged_trait.archive()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertTrue(context['show_other_tags'])
        content = str(response.content)
        self.assertNotIn(self.tagged_trait.tag, context['other_tags'])
        self.assertNotIn(self.tagged_trait.tag, context['archived_other_tags'])

    def test_archives_tagged_trait_changed_from_confirm_to_remove(self):
        """Updating a DCCDecision from confirm to remove archives the tagged trait."""
        self.dcc_decision.delete()
        self.dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        self.assertFalse(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionForm.SUBMIT_REMOVE: 'Remove', 'comment': 'get rid of it'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        dcc_decision = models.DCCDecision.objects.latest('modified')
        self.tagged_trait.refresh_from_db()
        self.assertEqual(form_data['comment'], dcc_decision.comment)
        self.assertTrue(self.tagged_trait.archived)

    def test_unarchives_tagged_trait_changed_from_remove_to_confirm(self):
        """Updating a DCCDecision from remove to confirm unarchives the tagged trait."""
        self.dcc_decision.delete()
        self.dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        self.tagged_trait.archive()
        self.tagged_trait.refresh_from_db()
        self.assertTrue(self.tagged_trait.archived)
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        dcc_decision = models.DCCDecision.objects.latest('modified')
        self.tagged_trait.refresh_from_db()
        self.assertEqual(form_data['comment'], dcc_decision.comment)
        self.assertFalse(self.tagged_trait.archived)

    def test_get_deprecated_tagged_trait(self):
        """A get request redirects with a warning for a deprecated trait."""
        study_version = self.dcc_decision.dcc_review.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))

    def test_post_deprecated_tagged_trait(self):
        """Posting valid data to the form does not update a DCCDecision for a deprecated trait."""
        study_version = self.dcc_decision.dcc_review.tagged_trait.trait.source_dataset.source_study_version
        study_version.i_is_deprecated = True
        study_version.save()
        original_comment = self.dcc_decision.comment
        form_data = {forms.DCCDecisionForm.SUBMIT_CONFIRM: 'Confirm', 'comment': 'looks good'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.dcc_decision.refresh_from_db()
        self.assertRedirects(response, self.need_decision_url)
        self.assertEqual(original_comment, self.dcc_decision.comment)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('newer version', str(messages[0]))


class DCCDecisionUpdateDCCAnalystTest(DCCDecisionUpdateDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in DCCDecisionUpdateDCCTestsMixin, as a DCC analyst.
    pass


class DCCDecisionUpdateDCCDeveloperTest(DCCDecisionUpdateDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in DCCDecisionUpdateDCCTestsMixin, as a DCC developer.
    pass


class DCCDecisionUpdateOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_trait = self.study_response.dcc_review.tagged_trait

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:dcc-decision:update', args=args)

    def test_forbidden_get_request(self):
        """Get returns forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Post returns forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_forbidden_get_request_with_existing_decision(self):
        """Get returns forbidden status code for non-DCC users when decision exists."""
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request_with_existing_decision(self):
        """Post returns forbidden status code for non-DCC users when decision exists."""
        factories.DCCDecisionFactory.create(
            dcc_review=self.tagged_trait.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class TagsLoginRequiredTest(LoginRequiredTestCase):

    def test_tags_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('tags')
