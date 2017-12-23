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

    def test_trait_name(self):
        """Trait name column value is as expected."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        self.assertIn(
            row.record.i_trait_name,
            row.get_cell_value('i_trait_name')
        )


class HarmonizedTraitTableTest(TestCase):

    model = models.HarmonizedTrait
    model_factory = factories.HarmonizedTraitFactory
    table_class = tables.HarmonizedTraitTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))

    def test_trait_flavor_name(self):
        """Trait name column value is as expected."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        self.assertIn(
            row.record.trait_flavor_name,
            row.get_cell_value('trait_flavor_name')
        )


class StudyTableTest(TestCase):

    model = models.Study
    model_factory = factories.StudyFactory
    table_class = tables.StudyTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))

    def test_trait_count_zero(self):
        """."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 0
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))

    def test_trait_count_all_not_deprecated(self):
        """."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 12
        factories.SourceTraitFactory.create_batch(
            n_traits, source_dataset__source_study_version__study=row.record,
            source_dataset__source_study_version__i_is_deprecated=False)
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))

    def test_trait_count_some_deprecated(self):
        """."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 12
        factories.SourceTraitFactory.create_batch(
            n_traits, source_dataset__source_study_version__study=row.record,
            source_dataset__source_study_version__i_is_deprecated=False)
        n_deprecated = 5
        factories.SourceTraitFactory.create_batch(
            n_deprecated, source_dataset__source_study_version__study=row.record,
            source_dataset__source_study_version__i_is_deprecated=True)
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))
