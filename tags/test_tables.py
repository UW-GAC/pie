"""Tests of tables from the tags app."""

from django.test import TestCase

from trait_browser.models import Study
from . import tables
from . import factories
from . import models


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


class StudyTaggedTraitTableTest(TestCase):
    table_class = tables.StudyTaggedTraitTable
    model_class = Study

    def setUp(self):
        super(StudyTaggedTraitTableTest, self).setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of studies."""
        table = self.table_class(Study.objects.all())
        self.assertEqual(self.model_class.objects.count(), len(table.rows))


class TaggedTraitTableTest(TestCase):
    table_class = tables.TaggedTraitTable
    model_class = models.TaggedTrait

    def setUp(self):
        super(TaggedTraitTableTest, self).setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(10)

    def test_row_count(self):
        """Number of rows in table matches number of data dictionaries."""
        table = self.table_class(self.tagged_traits)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))
