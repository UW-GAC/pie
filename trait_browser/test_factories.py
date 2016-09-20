"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from .factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory
from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class GlobalStudyFactoryTestCase(TestCase):
    
    def test_global_study_factory_build(self):
        """Test that a GlobalStudy instance is returned by GlobalStudyFactory.build()"""
        global_study = GlobalStudyFactory.build()
        self.assertIsInstance(global_study, GlobalStudy)
        
    def test_global_study_factory_create(self):
        """Test that a GlobalStudy instance is returned by GlobalStudyFactory.create()"""
        global_study = GlobalStudyFactory.create()
        self.assertIsInstance(global_study, GlobalStudy)

    def test_global_study_factory_build_batch(self):
        """Test that a GlobalStudy instance is returned by GlobalStudyFactory.build_batch(5)"""
        global_studies = GlobalStudyFactory.build_batch(5)
        for one in global_studies:
            self.assertIsInstance(one, GlobalStudy)
        
    def test_global_study_factory_create_batch(self):
        """Test that a GlobalStudy instance is returned by GlobalStudyFactory.create_batch(5)"""
        global_studies = GlobalStudyFactory.create_batch(5)
        for one in global_studies:
            self.assertIsInstance(one, GlobalStudy)


class StudyFactoryTestCase(TestCase):
    
    def test_study_factory_build(self):
        """Test that a Study instance is returned by StudyFactory.build()"""
        study = StudyFactory.build()
        self.assertIsInstance(study, Study)
        
    def test_study_factory_create(self):
        """Test that a Study instance is returned by StudyFactory.create()"""
        study = StudyFactory.create()
        self.assertIsInstance(study, Study)

    def test_study_factory_build_batch(self):
        """Test that a Study instance is returned by StudyFactory.build_batch(5)"""
        studies = StudyFactory.build_batch(5)
        for one in studies:
            self.assertIsInstance(one, Study)
        
    def test_study_factory_create_batch(self):
        """Test that a Study instance is returned by StudyFactory.create_batch(5)"""
        studies = StudyFactory.create_batch(5)
        for one in studies:
            self.assertIsInstance(one, Study)


class SourceStudyVersionFactoryTestCase(TestCase):

    def test_source_study_version_factory_build(self):
        """Test that a SourceStudyVersion instance is returned by SourceStudyVersionFactory.build()"""
        source_study_version = SourceStudyVersionFactory.build()
        self.assertIsInstance(source_study_version, SourceStudyVersion)
        
    def test_source_study_version_factory_create(self):
        """Test that a SourceStudyVersion instance is returned by SourceStudyVersionFactory.create()"""
        source_study_version = SourceStudyVersionFactory.create()
        self.assertIsInstance(source_study_version, SourceStudyVersion)

    def test_source_study_version_factory_build_batch(self):
        """Test that a SourceStudyVersion instance is returned by SourceStudyVersionFactory.build_batch(5)"""
        source_study_versions = SourceStudyVersionFactory.build_batch(5)
        for one in source_study_versions:
            self.assertIsInstance(one, SourceStudyVersion)
        
    def test_source_study_version_factory_create_batch(self):
        """Test that a SourceStudyVersion instance is returned by SourceStudyVersionFactory.create_batch(5)"""
        source_study_versions = SourceStudyVersionFactory.create_batch(5)
        for one in source_study_versions:
            self.assertIsInstance(one, SourceStudyVersion)
    

class SubcohortFactoryTestCase(TestCase):
    
    def test_source_trait_factory_build(self):
        """Test that a Subcohort instance is returned by SubcohortFactory.build()"""
        source_trait = SubcohortFactory.build()
        self.assertIsInstance(source_trait, Subcohort)
        
    def test_source_trait_factory_create(self):
        """Test that a Subcohort instance is returned by SubcohortFactory.create()"""
        source_trait = SubcohortFactory.create()
        self.assertIsInstance(source_trait, Subcohort)

    def test_source_trait_factory_build_batch(self):
        """Test that a Subcohort instance is returned by SubcohortFactory.build_batch(5)"""
        source_traits = SubcohortFactory.build_batch(5)
        for one in source_traits:
            self.assertIsInstance(one, Subcohort)
        
    def test_source_trait_factory_create_batch(self):
        """Test that a Subcohort instance is returned by SubcohortFactory.create_batch(5)"""
        source_traits = SubcohortFactory.create_batch(5)
        for one in source_traits:
            self.assertIsInstance(one, Subcohort)


class SourceDatasetFactoryTestCase(TestCase):
    
    def test_source_dataset_factory_build(self):
        """Test that a SourceDataset instance is returned by SourceDatasetFactory.build()"""
        source_dataset = SourceDatasetFactory.build()
        self.assertIsInstance(source_dataset, SourceDataset)
        
    def test_source_dataset_factory_create(self):
        """Test that a SourceDataset instance is returned by SourceDatasetFactory.create()"""
        source_dataset = SourceDatasetFactory.create()
        self.assertIsInstance(source_dataset, SourceDataset)

    def test_source_dataset_factory_build_batch(self):
        """Test that a SourceDataset instance is returned by SourceDatasetFactory.build_batch(5)"""
        source_datasets = SourceDatasetFactory.build_batch(5)
        for one in source_datasets:
            self.assertIsInstance(one, SourceDataset)
        
    def test_source_dataset_factory_create_batch(self):
        """Test that a SourceDataset instance is returned by SourceDatasetFactory.create_batch(5)"""
        source_datasets = SourceDatasetFactory.create_batch(5)
        for one in source_datasets:
            self.assertIsInstance(one, SourceDataset)


class HarmonizedTraitSetFactoryTestCase(TestCase):
    
    def test_harmonized_trait_set_factory_build(self):
        """Test that a HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.build()"""
        harmonized_trait_set = HarmonizedTraitSetFactory.build()
        self.assertIsInstance(harmonized_trait_set, HarmonizedTraitSet)
        
    def test_harmonized_trait_set_factory_create(self):
        """Test that a HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.create()"""
        harmonized_trait_set = HarmonizedTraitSetFactory.create()
        self.assertIsInstance(harmonized_trait_set, HarmonizedTraitSet)

    def test_harmonized_trait_set_factory_build_batch(self):
        """Test that a HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.build_batch(5)"""
        harmonized_trait_sets = HarmonizedTraitSetFactory.build_batch(5)
        for one in harmonized_trait_sets:
            self.assertIsInstance(one, HarmonizedTraitSet)
        
    def test_harmonized_trait_set_factory_create_batch(self):
        """Test that a HarmonizedTraitSet instance is returned by HarmonizedTraitSetFactory.create_batch(5)"""
        harmonized_trait_sets = HarmonizedTraitSetFactory.create_batch(5)
        for one in harmonized_trait_sets:
            self.assertIsInstance(one, HarmonizedTraitSet)


class SourceTraitFactoryTestCase(TestCase):

    def test_source_trait_factory_build(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.build()"""
        source_trait = SourceTraitFactory.build()
        self.assertIsInstance(source_trait, SourceTrait)
        
    def test_source_trait_factory_create(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.create()"""
        source_trait = SourceTraitFactory.create()
        self.assertIsInstance(source_trait, SourceTrait)

    def test_source_trait_factory_build_batch(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.build_batch(5)"""
        source_traits = SourceTraitFactory.build_batch(5)
        for one in source_traits:
            self.assertIsInstance(one, SourceTrait)
        
    def test_source_trait_factory_create_batch(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.create_batch(5)"""
        source_traits = SourceTraitFactory.create_batch(5)
        for one in source_traits:
            self.assertIsInstance(one, SourceTrait)


class HarmonizedTraitFactoryTestCase(TestCase):

    def test_harmonized_trait_factory_build(self):
        """Test that a HarmonizedTrait instance is returned by HarmonizedTraitFactory.build()"""
        harmonized_trait = HarmonizedTraitFactory.build()
        self.assertIsInstance(harmonized_trait, HarmonizedTrait)
        
    def test_harmonized_trait_factory_create(self):
        """Test that a HarmonizedTrait instance is returned by HarmonizedTraitFactory.create()"""
        harmonized_trait = HarmonizedTraitFactory.create()
        self.assertIsInstance(harmonized_trait, HarmonizedTrait)

    def test_harmonized_trait_factory_build_batch(self):
        """Test that a HarmonizedTrait instance is returned by HarmonizedTraitFactory.build_batch(5)"""
        harmonized_traits = HarmonizedTraitFactory.build_batch(5)
        for one in harmonized_traits:
            self.assertIsInstance(one, HarmonizedTrait)
        
    def test_harmonized_trait_factory_create_batch(self):
        """Test that a HarmonizedTrait instance is returned by HarmonizedTraitFactory.create_batch(5)"""
        harmonized_traits = HarmonizedTraitFactory.create_batch(5)
        for one in harmonized_traits:
            self.assertIsInstance(one, HarmonizedTrait)


class SourceTraitEncodedValueFactoryTestCase(TestCase):

    def test_source_trait_encoded_value_factory_build(self):
        """Test that a SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.build()"""
        source_trait_encoded_value = SourceTraitEncodedValueFactory.build()
        self.assertIsInstance(source_trait_encoded_value, SourceTraitEncodedValue)
        
    def test_source_trait_encoded_value_factory_create(self):
        """Test that a SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.create()"""
        source_trait_encoded_value = SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(source_trait_encoded_value, SourceTraitEncodedValue)

    def test_source_trait_encoded_value_factory_build_batch(self):
        """Test that a SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.build_batch(5)"""
        source_trait_encoded_values = SourceTraitEncodedValueFactory.build_batch(5)
        for one in source_trait_encoded_values:
            self.assertIsInstance(one, SourceTraitEncodedValue)
        
    def test_source_trait_encoded_value_factory_create_batch(self):
        """Test that a SourceTraitEncodedValue instance is returned by SourceTraitEncodedValueFactory.create_batch(5)"""
        source_trait_encoded_values = SourceTraitEncodedValueFactory.create_batch(5)
        for one in source_trait_encoded_values:
            self.assertIsInstance(one, SourceTraitEncodedValue)


class HarmonizedTraitEncodedValueFactoryTestCase(TestCase):

    def test_harmonized_trait_encoded_value_factory_build(self):
        """Test that a HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.build()"""
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValueFactory.build()
        self.assertIsInstance(harmonized_trait_encoded_value, HarmonizedTraitEncodedValue)
        
    def test_harmonized_trait_encoded_value_factory_create(self):
        """Test that a HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.create()"""
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(harmonized_trait_encoded_value, HarmonizedTraitEncodedValue)

    def test_harmonized_trait_encoded_value_factory_build_batch(self):
        """Test that a HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.build_batch(5)"""
        harmonized_trait_encoded_values = HarmonizedTraitEncodedValueFactory.build_batch(5)
        for one in harmonized_trait_encoded_values:
            self.assertIsInstance(one, HarmonizedTraitEncodedValue)
        
    def test_harmonized_trait_encoded_value_factory_create_batch(self):
        """Test that a HarmonizedTraitEncodedValue instance is returned by HarmonizedTraitEncodedValueFactory.create_batch(5)"""
        harmonized_trait_encoded_values = HarmonizedTraitEncodedValueFactory.create_batch(5)
        for one in harmonized_trait_encoded_values:
            self.assertIsInstance(one, HarmonizedTraitEncodedValue)
