"""Test functions and classes from models.py."""

from datetime import datetime

from django.test import TestCase
from django.core.validators import URLValidator

from .factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceDatasetSubcohortsFactory, SourceDatasetUniqueKeysFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory
from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceDatasetSubcohorts, SourceDatasetUniqueKeys, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class GlobalStudyTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a GlobalStudy object."""
        global_study = GlobalStudyFactory.create()
        self.assertIsInstance(GlobalStudy.objects.get(pk=global_study.pk), GlobalStudy)

    def test_printing(self):
        """Test the custom __str__ method."""
        global_study = GlobalStudyFactory.build()
        self.assertIsInstance(global_study.__str__(), str)
    
    def test_timestamps_added(self):
        """Test that timestamps are added."""
        global_study = GlobalStudyFactory.create()
        self.assertIsInstance(global_study.created, datetime)
        self.assertIsInstance(global_study.modified, datetime)


class StudyTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a Study object."""
        study = StudyFactory.create()
        self.assertIsInstance(Study.objects.get(pk=study.pk), Study)

    def test_printing(self):
        """Test the custom __str__ method."""
        study = StudyFactory.build()
        self.assertIsInstance(study.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        study = StudyFactory.create()
        self.assertIsInstance(study.created, datetime)
        self.assertIsInstance(study.modified, datetime)

    def test_custom_save(self):
        """Test that the custom save method works."""
        study = StudyFactory.create()
        self.assertRegex(study.phs, 'phs\d{6}')
        self.assertEqual(study.dbgap_latest_version_link[:68], Study.STUDY_URL[:68])


class SourceStudyVersionTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a SourceStudyVersion object."""
        source_study_version = SourceStudyVersionFactory.create()
        self.assertIsInstance(SourceStudyVersion.objects.get(pk=source_study_version.pk), SourceStudyVersion)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_study_version = SourceStudyVersionFactory.build()
        self.assertIsInstance(source_study_version.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_study_version = SourceStudyVersionFactory.create()
        self.assertIsInstance(source_study_version.created, datetime)
        self.assertIsInstance(source_study_version.modified, datetime)
    
    def test_custom_save(self):
        """Test that the custom save method works."""
        source_study_version = SourceStudyVersionFactory.create()
        self.assertRegex(source_study_version.phs_version_string, 'phs\d{6}\.v\d{1,3}\.p\d{1,3}')


class SourceDatasetTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a SourceDataset object."""
        source_dataset = SourceDatasetFactory.create()
        self.assertIsInstance(SourceDataset.objects.get(pk=source_dataset.pk), SourceDataset)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_dataset = SourceDatasetFactory.build()
        self.assertIsInstance(source_dataset.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_dataset = SourceDatasetFactory.create()
        self.assertIsInstance(source_dataset.created, datetime)
        self.assertIsInstance(source_dataset.modified, datetime)


class SourceDatasetSubcohortsTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a SourceDatasetSubcohorts object."""
        source_dataset_subcohorts = SourceDatasetSubcohortsFactory.create()
        self.assertIsInstance(SourceDatasetSubcohorts.objects.get(pk=source_dataset_subcohorts.pk), SourceDatasetSubcohorts)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_dataset_subcohorts = SourceDatasetSubcohortsFactory.build()
        self.assertIsInstance(source_dataset_subcohorts.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_dataset_subcohorts = SourceDatasetSubcohortsFactory.create()
        self.assertIsInstance(source_dataset_subcohorts.created, datetime)
        self.assertIsInstance(source_study_version.modified, datetime)





class SourceTraitTestCase(TestCase):
    
    def test_is_latest_version(self):
        pass
    
    def test_printing(self):
        """Ensure that the __str__ function works for printing the object."""
        trait = SourceTraitFactory.build()
        self.assertIsInstance(trait.__str__(), str)
        

class SourceTraitEncodedValueTestCase(TestCase):
    
    def test_printing(self):
        """Ensure that the custom printing method works."""
        enc_value = SourceEncodedValueFactory.build()
        self.assertIsInstance(enc_value.__str__(), str)
        
    def test_get_source_trait_name(self):
        """Ensure that get_source_trait_name() works."""
        enc_value = SourceEncodedValueFactory.build()
        enc_value.get_source_trait_name()
        
    def test_get_source_trait_enc_value(self):
        """Ensure that SourceEncodedValue.get_source_trait_enc_value() works."""
        enc_value = SourceEncodedValueFactory.build()
        enc_value.get_source_trait_study()
