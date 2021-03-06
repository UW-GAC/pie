"""Tests of tables from the tags app."""

from django.test import TestCase
from django.urls import reverse

from trait_browser.factories import StudyFactory, SourceStudyVersionFactory, SourceTraitFactory

from . import factories
from . import models
from . import tables


class TagTableTest(TestCase):
    table_class = tables.TagTable
    model_class = models.Tag

    def setUp(self):
        super(TagTableTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tags."""
        table = self.table_class(self.tags)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_tagged_count_excludes_archived_tagged_trait(self):
        """Number in column for tagged trait count does not include archived tagged trait."""
        tag = self.tags[0]
        archived_tagged_trait = factories.TaggedTraitFactory.create(tag=tag, archived=True)
        non_archived_tagged_trait = factories.TaggedTraitFactory.create(tag=tag, archived=False)
        table = self.table_class(self.tags)
        row = table.rows[0]
        self.assertEqual(row.get_cell('number_tagged_traits'), 1)

    def test_tagged_count_excludes_deprecated_tagged_trait(self):
        """Number in column for tagged trait count does not include deprecated tagged trait."""
        tag = self.tags[0]
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=4, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        table = self.table_class(self.tags)
        row = table.rows[0]
        self.assertEqual(row.get_cell('number_tagged_traits'), 1)

    def test_tagged_count_excludes_deprecated_tagged_trait_with_same_version_number(self):
        """Tagged trait count excludes tagged traits from deprecated study version, even with same version number."""
        tag = self.tags[0]
        study = StudyFactory.create()
        current_study_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_study_version = SourceStudyVersionFactory.create(study=study, i_version=5, i_is_deprecated=True)
        current_trait = SourceTraitFactory.create(source_dataset__source_study_version=current_study_version)
        old_trait = SourceTraitFactory.create(source_dataset__source_study_version=old_study_version)
        current_tagged_trait = factories.TaggedTraitFactory.create(trait=current_trait, tag=tag)
        old_tagged_trait = factories.TaggedTraitFactory.create(trait=old_trait, tag=tag)
        table = self.table_class(self.tags)
        row = table.rows[0]
        self.assertEqual(row.get_cell('number_tagged_traits'), 1)


class TaggedTraitTableTest(TestCase):
    table_class = tables.TaggedTraitTable
    model_class = models.TaggedTrait

    def setUp(self):
        super(TaggedTraitTableTest, self).setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class TaggedTraitDeleteButtonColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitDeleteButtonColumnMixin

    def test_delete_button_unreviewed(self):
        """The delete button is not disabled for unreviewed tagged traits."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        self.assertNotIn('disabled', table.render_delete_button(tagged_trait))

    def test_delete_button_confirmed(self):
        """The delete button is disabled for confirmed tagged traits."""
        tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        self.assertIn('disabled', table.render_delete_button(tagged_trait))

    def test_delete_button_needs_followup(self):
        """The delete button is disabled for reviewed tagged traits that need followup."""
        tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        self.assertIn('disabled', table.render_delete_button(tagged_trait))


class TaggedTraitQualityReviewColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitQualityReviewColumnMixin

    def test_unreviewed(self):
        """Quality review text is correct for an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertNotIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_no_studyresponse_no_dccdecision(self):
        """Quality review text is correct for a followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertNotIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_disagree_studyresponse_no_dccdecision(self):
        """Quality review text is correct for a followup, disagree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertIn(tables.DISAGREE_TEXT, quality_review)
        self.assertNotIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_confirmed_dccreview(self):
        """Quality review text is correct for a confirmed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertNotIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_no_studyresponse_remove_dccdecision_archived(self):
        """Quality review text is correct for a followup, no response, decision remove, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_no_studyresponse_confirm_dccdecision(self):
        """Quality review text is correct for a followup, no response, decision confirm tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertNotIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_agree_studyresponse_archived(self):
        """Quality review text is correct for a followup, agree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertIn(tables.AGREE_TEXT, quality_review)
        self.assertNotIn(tables.DISAGREE_TEXT, quality_review)
        self.assertIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_disagree_studyresponse_remove_dccdecision_archived(self):
        """Quality review text is correct for a followup, disagree, decision remove tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertIn(tables.DISAGREE_TEXT, quality_review)
        self.assertIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)

    def test_followup_dccreview_disagree_studyresponse_confirm_dccdecision(self):
        """Quality review text is correct for a followup, disagree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        quality_review = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, quality_review)
        self.assertNotIn(tables.FOLLOWUP_TEXT, quality_review)
        self.assertNotIn(tables.AGREE_TEXT, quality_review)
        self.assertIn(tables.DISAGREE_TEXT, quality_review)
        self.assertIn(tables.ARCHIVED_TEXT, quality_review)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, quality_review)
        self.assertIn(tables.DECISION_CONFIRM_STUDY_USER_TEXT, quality_review)
        self.assertNotIn(tables.DECISION_REMOVE_STUDY_USER_TEXT, quality_review)


class TaggedTraitDCCReviewStatusColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitDCCReviewStatusColumnMixin

    def test_unreviewed_tagged_trait(self):
        """DCC review status text is correct for an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_confirmed_tagged_trait(self):
        """DCC review status text is correct for a confirmed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_noresponse_nonarchived_tagged_trait(self):
        """DCC review status text is correct for a followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_noresponse_archived_tagged_trait(self):
        """DCC review status text is correct for an archived followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_agree_nonarchived_tagged_trait(self):
        """DCC review status text is correct for a followup, agree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_agree_archived_tagged_trait(self):
        """DCC review status text is correct for a followup, agree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_disagree_nonarchived_tagged_trait(self):
        """DCC review status text is correct for a followup, disagree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)

    def test_followup_disagree_archived_tagged_trait(self):
        """DCC review status text is correct for a followup, disagree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_review_status = table.render_dcc_review_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_review_status)
        self.assertIn(tables.FOLLOWUP_TEXT, dcc_review_status)
        self.assertNotIn(tables.AGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_review_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_review_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_review_status)


class TaggedTraitStudyResponseStatusColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitStudyResponseStatusColumnMixin

    def test_unreviewed_tagged_trait(self):
        """Study response status text is correct for an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_confirmed_tagged_trait(self):
        """Study response status text is correct for a confirmed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_noresponse_nonarchived_tagged_trait(self):
        """Study response status text is correct for a followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_noresponse_archived_tagged_trait(self):
        """Study response status text is correct for an archived followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_agree_nonarchived_tagged_trait(self):
        """Study response status text is correct for a followup, agree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_agree_archived_tagged_trait(self):
        """Study response status text is correct for a followup, agree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertIn(tables.AGREE_TEXT, study_response_status)
        self.assertNotIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_disagree_nonarchived_tagged_trait(self):
        """Study response status text is correct for a followup, disagree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)

    def test_followup_disagree_archived_tagged_trait(self):
        """Study response status text is correct for a followup, disagree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        study_response_status = table.render_study_response_status(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_TEXT, study_response_status)
        self.assertNotIn(tables.AGREE_TEXT, study_response_status)
        self.assertIn(tables.DISAGREE_TEXT, study_response_status)
        self.assertNotIn(tables.ARCHIVED_TEXT, study_response_status)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, study_response_status)


class TaggedTraitDCCDecisionColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitDCCDecisionColumnMixin

    def test_followup_disagree_nodecision_tagged_trait(self):
        """DCC decision text is correct for a disagree tagged trait without a DCC decision."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_value = table.render_dcc_decision(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_decision_value)
        self.assertNotIn(tables.AGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_CONFIRM_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_REMOVE_TEXT, dcc_decision_value)

    def test_followup_disagree_decisionconfirm_tagged_trait(self):
        """DCC decision text is correct for a disagree tagged trait with a decision to confirm."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_value = table.render_dcc_decision(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_decision_value)
        self.assertNotIn(tables.AGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_decision_value)
        self.assertIn(tables.DECISION_CONFIRM_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_REMOVE_TEXT, dcc_decision_value)

    def test_followup_disagree_decisionremove_tagged_trait(self):
        """DCC decision text is correct for a disagree tagged trait with a decision to remove."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_value = table.render_dcc_decision(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_decision_value)
        self.assertNotIn(tables.AGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_CONFIRM_TEXT, dcc_decision_value)
        self.assertIn(tables.DECISION_REMOVE_TEXT, dcc_decision_value)

    def test_followup_noresponse_decisionconfirm_tagged_trait(self):
        """DCC decision text is correct for a followup tagged trait with no study response and confirm decision."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_value = table.render_dcc_decision(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_decision_value)
        self.assertNotIn(tables.AGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_decision_value)
        self.assertIn(tables.DECISION_CONFIRM_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_REMOVE_TEXT, dcc_decision_value)

    def test_followup_noresponse_decisionremove_tagged_trait(self):
        """DCC decision text is correct for a followup tagged trait with no study response and remove decision."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_value = table.render_dcc_decision(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_TEXT, dcc_decision_value)
        self.assertNotIn(tables.AGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DISAGREE_TEXT, dcc_decision_value)
        self.assertNotIn(tables.ARCHIVED_TEXT, dcc_decision_value)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, dcc_decision_value)
        self.assertNotIn(tables.DECISION_CONFIRM_TEXT, dcc_decision_value)
        self.assertIn(tables.DECISION_REMOVE_TEXT, dcc_decision_value)


class TaggedTraitArchivedColumnMixinTest(TestCase):

    table_class = tables.TaggedTraitArchivedColumnMixin

    def test_unreviewed_tagged_trait(self):
        """Archived status text is correct for an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_confirmed_tagged_trait(self):
        """Archived status text is correct for a confirmed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_noresponse_nonarchived_tagged_trait(self):
        """Archived status text is correct for a followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_noresponse_archived_tagged_trait(self):
        """Archived status text is correct for an archived followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_agree_nonarchived_tagged_trait(self):
        """Archived status text is correct for a followup, agree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_agree_archived_tagged_trait(self):
        """Archived status text is correct for a followup, agree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_disagree_nonarchived_tagged_trait(self):
        """Archived status text is correct for a followup, disagree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)

    def test_followup_disagree_archived_tagged_trait(self):
        """Archived status text is correct for a followup, disagree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        archived_text = table.render_archived(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, archived_text)
        self.assertNotIn(tables.AGREE_TEXT, archived_text)
        self.assertNotIn(tables.DISAGREE_TEXT, archived_text)
        self.assertIn(tables.ARCHIVED_TEXT, archived_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, archived_text)


class TaggedTraitDCCActionButtonMixinTest(TestCase):

    table_class = tables.TaggedTraitDCCActionButtonMixin

    def test_unreviewed(self):
        """An unreviewed tagged trait has a link to the DCC review create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertNotIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_no_studyresponse_no_dccdecision(self):
        """A followup tagged trait with no response has a link to the DCC review update view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertNotIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_disagree_studyresponse_no_dccdecision(self):
        """A followup, disagree, nonarchived tagged trait has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertIn(dccdecision_create_url, dcc_action_button)
        self.assertNotIn(dccdecision_update_url, dcc_action_button)

    def test_confirmed_dccreview(self):
        """A confirmed tagged trait has a link to the DCC review update view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertNotIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_no_studyresponse_remove_dccdecision_archived(self):
        """An archived followup tagged trait with no response has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_no_studyresponse_confirm_dccdecision(self):
        """An archived followup tagged trait with no response has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_agree_studyresponse_archived(self):
        """A followup, agree, archived tagged trait has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertNotIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_disagree_studyresponse_remove_dccdecision_archived(self):
        """A followup, disagree, archived tagged trait has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertIn(dccdecision_update_url, dcc_action_button)

    def test_followup_dccreview_disagree_studyresponse_confirm_dccdecision(self):
        """A followup, disagree, archived tagged trait has no link to the DCC review update or create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_action_button = table.render_dcc_action_button(tagged_trait)
        dccreview_create_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        dccreview_update_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertNotIn(dccreview_create_url, dcc_action_button)
        self.assertNotIn(dccreview_update_url, dcc_action_button)
        dccdecision_create_url = reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk])
        dccdecision_update_url = reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk])
        self.assertNotIn(dccdecision_create_url, dcc_action_button)
        self.assertIn(dccdecision_update_url, dcc_action_button)


class TaggedTraitDCCDecisionButtonMixinTest(TestCase):

    table_class = tables.TaggedTraitDCCDecisionButtonMixin

    def test_nodecision_tagged_trait(self):
        """A tagged trait without a decision has the confirm and remove buttons."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)

    def test_decision_confirm_tagged_trait(self):
        """A tagged trait with decision confirm has the update button."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)

    def test_decision_remove_tagged_trait(self):
        """A tagged trait with decision remove has the update button."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)


class TaggedTraitTableForPhenotypeTaggersFromStudyTest(TestCase):

    table_class = tables.TaggedTraitTableForPhenotypeTaggersFromStudy
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_with_reviewed_tagged_traits_confirmed(self):
        """Row count is correct with TaggedTraits that need followup."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_traits[0], status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_with_reviewed_tagged_traits_followup(self):
        """Row count is correct with confirmed TaggedTraits."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_traits[0], status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class TaggedTraitTableForStaffByStudyTest(TestCase):

    table_class = tables.TaggedTraitTableForStaffByStudy
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class DCCReviewTableTest(TestCase):

    table_class = tables.TaggedTraitDCCReviewTable
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class TaggedTraitDCCReviewStudyResponseButtonTableTest(TestCase):

    table_class = tables.TaggedTraitDCCReviewStudyResponseButtonTable

    def setUp(self):
        super().setUp()
        self.dcc_reviews = factories.DCCReviewFactory.create_batch(10, status=models.DCCReview.STATUS_FOLLOWUP)
        self.tagged_traits = models.TaggedTrait.objects.all()

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(models.DCCReview.objects.count(), len(table.rows))

    def test_unreviewed_tagged_trait(self):
        """Status text is correct for an unreviewed tagged trait."""
        # Note this kind of tagged trait should not be in this table.
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_confirmed_tagged_trait(self):
        """Status text is correct for a confirmed tagged trait."""
        # Note this kind of tagged trait should not be in this table.
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertIn(tables.CONFIRMED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_noresponse_nonarchived_tagged_trait(self):
        """Status text is correct for a followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_noresponse_archived_tagged_trait(self):
        """Status text is correct for an archived followup tagged trait with no response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_agree_nonarchived_tagged_trait(self):
        """Status text is correct for a followup, agree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_agree_archived_tagged_trait(self):
        """Status text is correct for a followup, agree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertIn(tables.AGREE_TEXT, status_text)
        self.assertNotIn(tables.DISAGREE_TEXT, status_text)
        self.assertIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_disagree_nonarchived_tagged_trait(self):
        """Status text is correct for a followup, disagree, nonarchived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertIn(tables.DISAGREE_TEXT, status_text)
        self.assertNotIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    def test_followup_disagree_archived_tagged_trait(self):
        """Status text is correct for a followup, disagree, archived tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        table = self.table_class(models.TaggedTrait.objects.all())
        status_text = table.render_quality_review(tagged_trait)
        self.assertNotIn(tables.CONFIRMED_TEXT, status_text)
        self.assertIn(tables.FOLLOWUP_STUDY_USER_TEXT, status_text)
        self.assertNotIn(tables.AGREE_TEXT, status_text)
        self.assertIn(tables.DISAGREE_TEXT, status_text)
        self.assertIn(tables.ARCHIVED_TEXT, status_text)
        self.assertNotIn(tables.FOLLOWUP_TEXT, status_text)

    # I could not find a way to test the conditional rendering of buttons in the
    # table, since a request is needed to render the template properly. They are
    # tested in the views that use this table.


class TaggedTraitDCCDecisionTable(TestCase):

    table_class = tables.TaggedTraitDCCDecisionTable
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.study_responses = factories.StudyResponseFactory.create_batch(
            10, status=models.StudyResponse.STATUS_DISAGREE)
        self.tagged_traits = models.TaggedTrait.objects.all()

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_nodecision_tagged_trait(self):
        """A tagged trait without a decision has the confirm and remove buttons."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)

    def test_decision_confirm_tagged_trait(self):
        """A tagged trait with decision confirm has the update button."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)

    def test_decision_remove_tagged_trait(self):
        """A tagged trait with decision remove has the update button."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(
            dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        table = self.table_class(models.TaggedTrait.objects.all())
        dcc_decision_button_value = table.render_decision_buttons(tagged_trait)
        self.assertNotIn(
            reverse('tags:tagged-traits:pk:dcc-decision:new', args=[tagged_trait.pk]), dcc_decision_button_value)
        self.assertIn(
            reverse('tags:tagged-traits:pk:dcc-decision:update', args=[tagged_trait.pk]), dcc_decision_button_value)
