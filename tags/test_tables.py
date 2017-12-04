"""Tests of tables from the tags app."""

from django.test import TestCase

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
        """Number of rows in table matches number of data dictionaries."""
        table = self.table_class(self.tags)
        self.assertEqual(self.model_class.objects.count(), len(table.rows))
