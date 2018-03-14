"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from . import factories
from . import models

# Note that running the create_batch commands with n=5000 is likely to catch unique constraint errors that are
# caused because Faker doesn't have enough unique fake values.


class GlobalStudyFactoryTest(TestCase):

    def test_global_study_factory_build(self):
        """A GlobalStudy instance is returned by GlobalStudyFactory.build()."""
        global_study = factories.GlobalStudyFactory.build()
        self.assertIsInstance(global_study, models.GlobalStudy)

    def test_global_study_factory_create(self):
        """A GlobalStudy instance is returned by GlobalStudyFactory.create()."""
        global_study = factories.GlobalStudyFactory.create()
        self.assertIsInstance(global_study, models.GlobalStudy)

    def test_global_study_factory_build_batch(self):
        """A GlobalStudy instance is returned by GlobalStudyFactory.build_batch."""
        global_studies = factories.GlobalStudyFactory.build_batch(10)
        for one in global_studies:
            self.assertIsInstance(one, models.GlobalStudy)

    def test_global_study_factory_create_batch(self):
        """A GlobalStudy instance is returned by GlobalStudyFactory.create_batch."""
        global_studies = factories.GlobalStudyFactory.create_batch(1000)
        for one in global_studies:
            self.assertIsInstance(one, models.GlobalStudy)


class StudyFactoryTest(TestCase):

    def test_study_factory_build(self):
        """A Study instance is returned by StudyFactory.build()."""
        study = factories.StudyFactory.build()
        self.assertIsInstance(study, models.Study)

    def test_study_factory_create(self):
        """A Study instance is returned by StudyFactory.create()."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(study, models.Study)

    def test_study_factory_build_batch(self):
        """A Study instance is returned by StudyFactory.build_batch."""
        studies = factories.StudyFactory.build_batch(10)
        for one in studies:
            self.assertIsInstance(one, models.Study)

    def test_study_factory_create_batch(self):
        """A Study instance is returned by StudyFactory.create_batch."""
        studies = factories.StudyFactory.create_batch(1000)
        for one in studies:
            self.assertIsInstance(one, models.Study)


class SourceStudyVersionFactoryTest(TestCase):

    def test_source_study_version_factory_build(self):
        """A SourceStudyVersion instance is returned by SourceStudyVersionFactory.build()."""
        source_study_version = factories.SourceStudyVersionFactory.build()
        self.assertIsInstance(source_study_version, models.SourceStudyVersion)

    def test_source_study_version_factory_create(self):
        """A SourceStudyVersion instance is returned by SourceStudyVersionFactory.create()."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsInstance(source_study_version, models.SourceStudyVersion)

    def test_source_study_version_factory_build_batch(self):
        """A SourceStudyVersion instance is returned by SourceStudyVersionFactory.build_batch."""
        source_study_versions = factories.SourceStudyVersionFactory.build_batch(10)
        for one in source_study_versions:
            self.assertIsInstance(one, models.SourceStudyVersion)

    def test_source_study_version_factory_create_batch(self):
        """A SourceStudyVersion instance is returned by SourceStudyVersionFactory.create_batch."""
        source_study_versions = factories.SourceStudyVersionFactory.create_batch(1000)
        for one in source_study_versions:
            self.assertIsInstance(one, models.SourceStudyVersion)


class SubcohortFactoryTest(TestCase):

    def test_subcohort_factory_build(self):
        """A Subcohort instance is returned by SubcohortFactory.build()."""
        subcohort = factories.SubcohortFactory.build()
        self.assertIsInstance(subcohort, models.Subcohort)

    def test_subcohort_factory_create(self):
        """A Subcohort instance is returned by SubcohortFactory.create()."""
        subcohort = factories.SubcohortFactory.create()
        self.assertIsInstance(subcohort, models.Subcohort)

    def test_subcohort_factory_build_batch(self):
        """A Subcohort instance is returned by SubcohortFactory.build_batch."""
        subcohorts = factories.SubcohortFactory.build_batch(10)
        for one in subcohorts:
            self.assertIsInstance(one, models.Subcohort)

    def test_subcohort_factory_create_batch(self):
        """A Subcohort instance is returned by SubcohortFactory.create_batch."""
        subcohorts = factories.SubcohortFactory.create_batch(1000)
        for one in subcohorts:
            self.assertIsInstance(one, models.Subcohort)


class SourceDatasetFactoryTest(TestCase):

    def test_source_dataset_factory_build(self):
        """A SourceDataset instance is returned by SourceDatasetFactory.build()."""
        source_dataset = factories.SourceDatasetFactory.build()
        self.assertIsInstance(source_dataset, models.SourceDataset)

    def test_source_dataset_factory_create(self):
        """A SourceDataset instance is returned by SourceDatasetFactory.create()."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(source_dataset, models.SourceDataset)

    def test_source_dataset_factory_build_batch(self):
        """A SourceDataset instance is returned by SourceDatasetFactory.build_batch."""
        source_datasets = factories.SourceDatasetFactory.build_batch(10)
        for one in source_datasets:
            self.assertIsInstance(one, models.SourceDataset)

    def test_source_dataset_factory_create_batch(self):
        """A SourceDataset instance is returned by SourceDatasetFactory.create_batch."""
        source_datasets = factories.SourceDatasetFactory.create_batch(1000)
        for one in source_datasets:
            self.assertIsInstance(one, models.SourceDataset)

    # def test_source_dataset_factory_create_with_subcohorts(self):
    #     """Passing subcohorts to factories.SourceDatasetFactory creates a SourceDataset with non-empty subcohorts."""
    #     subcohorts = factories.SubcohortFactory.create_batch(5, global_study__i_id=5)
    #     source_dataset = factories.SourceDatasetFactory.create(subcohorts=subcohorts)
    #     self.assertEqual(subcohorts, list(source_dataset.subcohorts.all()))


class HarmonizedTraitSetFactoryTest(TestCase):

    def test_harmonized_trait_set_factory_build(self):
        """A HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.build()."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.build()
        self.assertIsInstance(harmonized_trait_set, models.HarmonizedTraitSet)

    def test_harmonized_trait_set_factory_create(self):
        """A HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.create()."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create()
        self.assertIsInstance(harmonized_trait_set, models.HarmonizedTraitSet)

    def test_harmonized_trait_set_factory_build_batch(self):
        """A HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.build_batch."""
        harmonized_trait_sets = factories.HarmonizedTraitSetFactory.build_batch(10)
        for one in harmonized_trait_sets:
            self.assertIsInstance(one, models.HarmonizedTraitSet)

    def test_harmonized_trait_set_factory_create_batch(self):
        """A HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.create_batch."""
        harmonized_trait_sets = factories.HarmonizedTraitSetFactory.create_batch(1000)
        for one in harmonized_trait_sets:
            self.assertIsInstance(one, models.HarmonizedTraitSet)


class AllowedUpdateReasonFactoryTest(TestCase):

    def test_allowed_update_reason_factory_build(self):
        """An AllowedUpdateReason instance is returned by AllowedUpdateReasonFactory.build()."""
        allowed_update_reason = factories.AllowedUpdateReasonFactory.build()
        self.assertIsInstance(allowed_update_reason, models.AllowedUpdateReason)

    def test_allowed_update_reason_factory_create(self):
        """An AllowedUpdateReason instance is returned by AllowedUpdateReasonFactory.create()."""
        allowed_update_reason = factories.AllowedUpdateReasonFactory.create()
        self.assertIsInstance(allowed_update_reason, models.AllowedUpdateReason)

    def test_allowed_update_reason_factory_build_batch(self):
        """An AllowedUpdateReason instance is returned by AllowedUpdateReasonFactory.build_batch."""
        allowed_update_reasons = factories.AllowedUpdateReasonFactory.build_batch(10)
        for one in allowed_update_reasons:
            self.assertIsInstance(one, models.AllowedUpdateReason)

    def test_allowed_update_reason_factory_create_batch(self):
        """An AllowedUpdateReason instance is returned by AllowedUpdateReasonFactory.create_batch."""
        allowed_update_reasons = factories.AllowedUpdateReasonFactory.create_batch(1000)
        for one in allowed_update_reasons:
            self.assertIsInstance(one, models.AllowedUpdateReason)


class HarmonizedTraitSetVersionFactoryTest(TestCase):

    def test_harmonized_trait_set_version_factory_build(self):
        """A HarmonizedTraitSetVersion instance is returned by HarmonizedTraitSetVersionFactory.build()."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.build()
        self.assertIsInstance(harmonized_trait_set_version, models.HarmonizedTraitSetVersion)

    def test_harmonized_trait_set_version_factory_create(self):
        """A HarmonizedTraitSetVersion instance is returned by HarmonizedTraitSetVersionFactory.create()."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(harmonized_trait_set_version, models.HarmonizedTraitSetVersion)

    def test_harmonized_trait_set_version_factory_build_batch(self):
        """A HarmonizedTraitSetVersion instance is returned by HarmonizedTraitSetVersionFactory.build_batch."""
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.build_batch(10)
        for one in harmonized_trait_set_versions:
            self.assertIsInstance(one, models.HarmonizedTraitSetVersion)

    def test_harmonized_trait_set_version_factory_create_batch(self):
        """A HarmonizedTraitSetVersion instance is returned by HarmonizedTraitSetVersionFactory.create_batch."""
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(1000)
        for one in harmonized_trait_set_versions:
            self.assertIsInstance(one, models.HarmonizedTraitSetVersion)


class HarmonizationUnitFactoryTest(TestCase):

    def test_build(self):
        """A HarmonizationUnit instance is returned by HarmonizationUnitFactory.build()."""
        harmonization_unit = factories.HarmonizationUnitFactory.build()
        self.assertIsInstance(harmonization_unit, models.HarmonizationUnit)

    def test_create(self):
        """A HarmonizationUnit instance is returned by HarmonizationUnitFactory.create()."""
        harmonization_unit = factories.HarmonizationUnitFactory.create()
        self.assertIsInstance(harmonization_unit, models.HarmonizationUnit)

    def test_build_batch(self):
        """A HarmonizationUnit instance is returned by HarmonizationUnitFactory.build_batch."""
        harmonization_units = factories.HarmonizationUnitFactory.build_batch(10)
        for one in harmonization_units:
            self.assertIsInstance(one, models.HarmonizationUnit)

    def test_create_batch(self):
        """A HarmonizationUnit instance is returned by HarmonizationUnitFactory.create_batch."""
        harmonization_units = factories.HarmonizationUnitFactory.create_batch(1000)
        for one in harmonization_units:
            self.assertIsInstance(one, models.HarmonizationUnit)

    def test_create_with_component_source_traits(self):
        """Passing component_source_traits to creates a HarmonizationUnitSet with non-empty component_source_traits."""
        source_traits = factories.SourceTraitFactory.create_batch(10)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_source_traits=source_traits)
        self.assertEqual(source_traits, list(harmonization_unit.component_source_traits.all()))

    def test_create_with_component_harmonized_trait_set_versions(self):
        """Passing component_harmonized_trait_sets creates with non-empty component_harmonized_trait_sets."""
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(10)
        harmonization_unit = factories.HarmonizationUnitFactory.create(
            component_harmonized_trait_set_versions=harmonized_trait_set_versions)
        self.assertEqual(harmonized_trait_set_versions,
                         list(harmonization_unit.component_harmonized_trait_set_versions.all()))

    def test_create_with_component_batch_traits(self):
        """Passing component_batch_traits creates a HarmonizationUnitSet with non-empty component_batch_traits."""
        source_traits = factories.SourceTraitFactory.create_batch(10)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_batch_traits=source_traits)
        self.assertEqual(source_traits, list(harmonization_unit.component_batch_traits.all()))

    def test_create_with_component_source_and_harmonized_and_batch_traits(self):
        """Passing component_source_traits and component_harmonized_trait_sets to factory creation works."""
        source_traits = factories.SourceTraitFactory.create_batch(1000)
        batch_traits = factories.SourceTraitFactory.create_batch(1000)
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(10)
        harmonization_unit = factories.HarmonizationUnitFactory.create(
            component_source_traits=source_traits, component_batch_traits=batch_traits,
            component_harmonized_trait_set_versions=harmonized_trait_set_versions)
        self.assertEqual(source_traits, list(harmonization_unit.component_source_traits.all()))
        self.assertEqual(harmonized_trait_set_versions,
                         list(harmonization_unit.component_harmonized_trait_set_versions.all()))
        self.assertEqual(batch_traits, list(harmonization_unit.component_batch_traits.all()))


class SourceTraitFactoryTest(TestCase):

    def test_source_trait_factory_build(self):
        """A SourceTrait instance is returned by SourceTraitFactory.build()."""
        source_trait = factories.SourceTraitFactory.build()
        self.assertIsInstance(source_trait, models.SourceTrait)

    def test_source_trait_factory_create(self):
        """A SourceTrait instance is returned by SourceTraitFactory.create()."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(source_trait, models.SourceTrait)

    def test_source_trait_factory_build_batch(self):
        """A SourceTrait instance is returned by SourceTraitFactory.build_batch."""
        source_traits = factories.SourceTraitFactory.build_batch(10)
        for one in source_traits:
            self.assertIsInstance(one, models.SourceTrait)

    def test_source_trait_factory_create_batch(self):
        """A SourceTrait instance is returned by SourceTraitFactory.create_batch."""
        source_traits = factories.SourceTraitFactory.create_batch(1000)
        for one in source_traits:
            self.assertIsInstance(one, models.SourceTrait)


class HarmonizedTraitFactoryTest(TestCase):

    def test_build(self):
        """A HarmonizedTrait instance is returned by HarmonizedTraitFactory.build()."""
        harmonized_trait = factories.HarmonizedTraitFactory.build()
        self.assertIsInstance(harmonized_trait, models.HarmonizedTrait)

    def test_create(self):
        """A HarmonizedTrait instance is returned by HarmonizedTraitFactory.create()."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(harmonized_trait, models.HarmonizedTrait)

    def test_build_batch(self):
        """A HarmonizedTrait instance is returned by HarmonizedTraitFactory.build_batch."""
        harmonized_traits = factories.HarmonizedTraitFactory.build_batch(10)
        for one in harmonized_traits:
            self.assertIsInstance(one, models.HarmonizedTrait)

    def test_create_batch(self):
        """A HarmonizedTrait instance is returned by HarmonizedTraitFactory.create_batch."""
        harmonized_traits = factories.HarmonizedTraitFactory.create_batch(1000)
        for one in harmonized_traits:
            self.assertIsInstance(one, models.HarmonizedTrait)

    def test_create_with_harmonization_units(self):
        """Passing harmonization_units creates a HarmonizedTraitSet with non-empty harmonization_units."""
        harmonization_units = factories.HarmonizationUnitFactory.create_batch(10)
        harmonized_trait = factories.HarmonizedTraitFactory.create(harmonization_units=harmonization_units)
        self.assertEqual(harmonization_units, list(harmonized_trait.harmonization_units.all()))

    def test_create_with_component_source_traits(self):
        """Passing component_source_traits creates a HarmonizedTraitSet with non-empty component_source_traits."""
        source_traits = factories.SourceTraitFactory.create_batch(10)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_source_traits=source_traits)
        self.assertEqual(source_traits, list(harmonized_trait.component_source_traits.all()))

    def test_create_with_component_harmonized_trait_set_versions(self):
        """Passing component_harmonized_trait_sets to factory creation works."""
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(10)
        harmonized_trait = factories.HarmonizedTraitFactory.create(
            component_harmonized_trait_set_versions=harmonized_trait_set_versions)
        self.assertEqual(harmonized_trait_set_versions,
                         list(harmonized_trait.component_harmonized_trait_set_versions.all()))

    def test_create_with_component_batch_traits(self):
        """Passing component_batch_traits to factory creation works."""
        source_traits = factories.SourceTraitFactory.create_batch(10)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_batch_traits=source_traits)
        self.assertEqual(source_traits, list(harmonized_trait.component_batch_traits.all()))

    def test_create_with_component_source_and_harmonized_and_batch_traits(self):
        """Passing component_batch_traits and component_source_traits to factory creation works."""
        source_traits = factories.SourceTraitFactory.create_batch(1000)
        batch_traits = factories.SourceTraitFactory.create_batch(1000)
        harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(10)
        harmonized_trait = factories.HarmonizedTraitFactory.create(
            component_source_traits=source_traits, component_batch_traits=batch_traits,
            component_harmonized_trait_set_versions=harmonized_trait_set_versions)
        self.assertEqual(source_traits, list(harmonized_trait.component_source_traits.all()))
        self.assertEqual(harmonized_trait_set_versions,
                         list(harmonized_trait.component_harmonized_trait_set_versions.all()))
        self.assertEqual(batch_traits, list(harmonized_trait.component_batch_traits.all()))


class SourceTraitEncodedValueFactoryTest(TestCase):

    def test_source_trait_encoded_value_factory_build(self):
        """A SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.build()."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.build()
        self.assertIsInstance(source_trait_encoded_value, models.SourceTraitEncodedValue)

    def test_source_trait_encoded_value_factory_create(self):
        """A SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.create()."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(source_trait_encoded_value, models.SourceTraitEncodedValue)

    def test_source_trait_encoded_value_factory_build_batch(self):
        """A SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.build_batch."""
        source_trait_encoded_values = factories.SourceTraitEncodedValueFactory.build_batch(10)
        for one in source_trait_encoded_values:
            self.assertIsInstance(one, models.SourceTraitEncodedValue)

    def test_source_trait_encoded_value_factory_create_batch(self):
        """A SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.create_batch."""
        source_trait_encoded_values = factories.SourceTraitEncodedValueFactory.create_batch(1000)
        for one in source_trait_encoded_values:
            self.assertIsInstance(one, models.SourceTraitEncodedValue)


class HarmonizedTraitEncodedValueFactoryTest(TestCase):

    def test_harmonized_trait_encoded_value_factory_build(self):
        """A HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.build()."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.build()
        self.assertIsInstance(harmonized_trait_encoded_value, models.HarmonizedTraitEncodedValue)

    def test_harmonized_trait_encoded_value_factory_create(self):
        """A HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.create()."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(harmonized_trait_encoded_value, models.HarmonizedTraitEncodedValue)

    def test_harmonized_trait_encoded_value_factory_build_batch(self):
        """A HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.build_batch."""
        harmonized_trait_encoded_values = factories.HarmonizedTraitEncodedValueFactory.build_batch(10)
        for one in harmonized_trait_encoded_values:
            self.assertIsInstance(one, models.HarmonizedTraitEncodedValue)

    def test_harmonized_trait_encoded_value_factory_create_batch(self):
        """A HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.create_batch."""
        harmonized_trait_encoded_values = factories.HarmonizedTraitEncodedValueFactory.create_batch(1000)
        for one in harmonized_trait_encoded_values:
            self.assertIsInstance(one, models.HarmonizedTraitEncodedValue)
