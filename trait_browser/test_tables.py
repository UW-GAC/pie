"""Tests of tables from the visit_tracker app."""

from django.test import TestCase

from . import factories
from . import models
from . import tables


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
        """Trait count is correct when it's zero."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 0
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))

    def test_trait_count_all_not_deprecated(self):
        """Trait count is correct when all traits for the study are not deprecated."""
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
        """Trait count is correct when some of the SSVs for the study are deprecated."""
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


class SourceDatasetTableTest(TestCase):

    model = models.SourceDataset
    model_factory = factories.SourceDatasetFactory
    table_class = tables.SourceDatasetTable

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))

    def test_trait_count_zero(self):
        """Trait count is correct when there are zero traits for a dataset."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 0
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))

    def test_trait_count_12(self):
        """Trait count is correct when there are 12 traits in the dataset."""
        things = self.model_factory.create_batch(20, source_study_version__i_is_deprecated=False)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 12
        factories.SourceTraitFactory.create_batch(
            n_traits, source_dataset=row.record)
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))


class SourceDatasetTableFullTest(TestCase):

    model = models.SourceDataset
    model_factory = factories.SourceDatasetFactory
    table_class = tables.SourceDatasetTableFull

    def test_row_count(self):
        """Table has expected number of rows."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        self.assertEqual(self.model.objects.count(), len(table.rows))

    def test_trait_count_zero(self):
        """Trait count is correct when there are zero traits for a dataset."""
        things = self.model_factory.create_batch(20)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 0
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))

    def test_trait_count_12(self):
        """Trait count is correct when there are 12 traits in the dataset."""
        things = self.model_factory.create_batch(20, source_study_version__i_is_deprecated=False)
        table = self.table_class(things)
        row = table.rows[0]
        n_traits = 12
        factories.SourceTraitFactory.create_batch(
            n_traits, source_dataset=row.record)
        # Remake the table, to update trait counts.
        table = self.table_class(things)
        row = table.rows[0]
        self.assertEqual(row.get_cell('trait_count'), '{:,}'.format(n_traits))


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


class SourceTraitTableFullTest(TestCase):

    model = models.SourceTrait
    model_factory = factories.SourceTraitFactory
    table_class = tables.SourceTraitTableFull

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


class SourceTraitStudyTableTest(TestCase):

    model = models.SourceTrait
    model_factory = factories.SourceTraitFactory
    table_class = tables.SourceTraitStudyTable

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


class SourceTraitDatasetTableTest(TestCase):

    model = models.SourceTrait
    model_factory = factories.SourceTraitFactory
    table_class = tables.SourceTraitDatasetTable

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
