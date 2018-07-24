"""Tests of tables from the tags app."""

from django.test import TestCase
from django.urls import reverse

from trait_browser.models import Study

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
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, comment='foo',
                                          status=models.DCCReview.STATUS_FOLLOWUP)
        table = self.table_class(models.TaggedTrait.objects.all())
        self.assertIn('disabled', table.render_delete_button(tagged_trait))


class TaggedTraitTableWithDCCReviewButtonMixinTest(TestCase):

    table_class = tables.TaggedTraitTableDCCReviewButtonMixin

    def test_proper_link_with_reviewed_tagged_trait(self):
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait)
        table = self.table_class(models.TaggedTrait.objects.all())
        expected_url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[tagged_trait.pk])
        self.assertIn(expected_url, table.render_review_button(tagged_trait))

    def test_proper_link_with_unreviewed_tagged_trait(self):
        tagged_trait = factories.TaggedTraitFactory.create()
        table = self.table_class(models.TaggedTrait.objects.all())
        expected_url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[tagged_trait.pk])
        self.assertIn(expected_url, table.render_review_button(tagged_trait))


class TaggedTraitTableWithDCCReviewStatusTest(TestCase):
    table_class = tables.TaggedTraitTableWithDCCReviewStatus
    model_class = models.TaggedTrait

    def setUp(self):
        super().setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of tagged traits."""
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
