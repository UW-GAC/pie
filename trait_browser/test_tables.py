"""Tests of tables from the visit_tracker app."""

from django.test import TestCase

from . import tables
from . import factories
from . import models


class SourceTraitTableTest(TestCase):

    model = models.SourceTrait
    model_factory = factories.SourceTraitFactory
    table_class = tables.SourceTraitTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))


class HarmonizedTraitTableTest(TestCase):

    model = models.HarmonizedTrait
    model_factory = factories.HarmonizedTraitFactory
    table_class = tables.HarmonizedTraitTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))


class StudyTableTest(TestCase):

    model = models.Study
    model_factory = factories.StudyFactory
    table_class = tables.StudyTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))
