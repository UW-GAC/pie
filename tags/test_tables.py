"""Tests of tables from the tags app."""

from django.test import TestCase
from django.urls import reverse

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


class TaggedTraitDeleteButtonMixinTest(TestCase):

    table_class = tables.TaggedTraitDeleteButtonMixin

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


class TaggedTraitTableWithDCCReviewButtonMixinTest(TestCase):

    table_class = tables.TaggedTraitTableDCCReviewButtonMixin

    def test_proper_link_with_reviewed_tagged_trait(self):
        """Reviewed tagged traits have a link to the DCC Review update view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait)
        table = self.table_class(models.TaggedTrait.objects.all())
        expected_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertIn(expected_url, table.render_review_button(tagged_trait))

    def test_proper_link_with_unreviewed_tagged_trait(self):
        """Reviewed tagged traits have a link to the DCC Review create view."""
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        expected_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        self.assertIn(expected_url, table.render_review_button(tagged_trait))

    def test_no_update_button_if_study_response_exists(self):
        """No update button is shown if a StudyResponse exists."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        table = self.table_class(models.TaggedTrait.objects.all())
        self.assertNotIn(reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk]),
                         table.render_review_button(tagged_trait))
        self.assertNotIn(reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk]),
                         table.render_review_button(tagged_trait))


class TaggedTraitTableWithReviewStatusTest(TestCase):
    table_class = tables.TaggedTraitTableWithReviewStatus
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_with_reviewed_tagged_traits_confirmed(self):
        """Table works with TaggedTraits that need followup."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_traits[0], status=models.DCCReview.STATUS_CONFIRMED)
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_with_reviewed_tagged_traits_followup(self):
        """Table works with confirmed TaggedTraits."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_traits[0], status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class TaggedTraitTableWithDCCReviewButtonTest(TestCase):
    table_class = tables.TaggedTraitTableWithDCCReviewButton
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class DCCReviewTableTest(TestCase):
    table_class = tables.DCCReviewTable
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))

    def test_render_status_for_tagged_trait_with_no_study_response_non_archived(self):
        """Missing status for non_archived need_followup taggedtraits without studyresponse."""
        table = self.table_class(self.tagged_traits)
        tagged_trait = self.tagged_traits[0]
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        self.assertEqual(len(table.render_study_response(tagged_trait)), 0)

    def test_render_status_for_need_followup_tagged_trait_with_agree_response(self):
        """Correct status for non_archived need_followup taggedtraits with agree response."""
        table = self.table_class(self.tagged_traits)
        tagged_trait = self.tagged_traits[0]
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review,
                                              status=models.StudyResponse.STATUS_AGREE)
        self.assertIn(self.table_class.AGREE_STATUS, table.render_study_response(tagged_trait))

    def test_render_status_for_need_followup_tagged_trait_with_agree_response_and_archived(self):
        """Correct status for archived need_followup taggedtraits with agree response."""
        table = self.table_class(self.tagged_traits)
        tagged_trait = self.tagged_traits[0]
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review,
                                              status=models.StudyResponse.STATUS_AGREE)
        tagged_trait.archive()
        tagged_trait.refresh_from_db()
        self.assertIn(self.table_class.AGREE_STATUS, table.render_study_response(tagged_trait))
        self.assertIn(self.table_class.ARCHIVED_STATUS, table.render_study_response(tagged_trait))

    def test_render_status_for_need_followup_tagged_trait_with_disagree_response(self):
        """Correct status for non_archived need_followup taggedtraits with disagree response."""
        table = self.table_class(self.tagged_traits)
        tagged_trait = self.tagged_traits[0]
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review,
                                              status=models.StudyResponse.STATUS_DISAGREE)
        self.assertIn(self.table_class.DISAGREE_STATUS, table.render_study_response(tagged_trait))

    def test_render_status_for_need_followup_tagged_trait_with_disagree_response_and_archived(self):
        """Correct status for archived need_followup taggedtraits with disagree response."""
        table = self.table_class(self.tagged_traits)
        tagged_trait = self.tagged_traits[0]
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review,
                                              status=models.StudyResponse.STATUS_DISAGREE)
        tagged_trait.archive()
        tagged_trait.refresh_from_db()
        self.assertIn(self.table_class.DISAGREE_STATUS, table.render_study_response(tagged_trait))
        self.assertIn(self.table_class.ARCHIVED_STATUS, table.render_study_response(tagged_trait))


class DCCReviewTableWithStudyResponseButtonsTest(TestCase):
    table_class = tables.DCCReviewTableWithStudyResponseButtons

    def setUp(self):
        super().setUp()
        self.dcc_reviews = factories.DCCReviewFactory.create_batch(10, status=models.DCCReview.STATUS_FOLLOWUP)
        self.tagged_traits = models.TaggedTrait.objects.all()

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(models.DCCReview.objects.count(), len(table.rows))

    # I could not find a way to test the conditional rendering of buttons in the
    # table, since a request is needed to render the template properly. They are
    # tested in the views that use this table.
