"""Test functions and classes from models.py."""

from datetime import datetime

from django.test import TestCase
from django.core.validators import URLValidator
from django.core.urlresolvers import reverse

from .factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory
from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


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

    def test_get_search_url_creation(self):
        study = StudyFactory.create()
        url = ''.join([reverse('trait_browser:source:search'), '\?study=\d+'])
        self.assertRegex(study.get_search_url(),  url)

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
    
    def test_adding_subcohorts(self):
        """Test that adding associated subcohorts works."""
        study = StudyFactory.create()
        subcohorts = SubcohortFactory.create_batch(5, study=study)
        source_dataset = SourceDatasetFactory.create(source_study_version__study=study, subcohorts=subcohorts)
        self.assertEqual(len(source_dataset.subcohorts.all()), 5)

    def test_custom_save(self):
        """Test that the custom save method works."""
        source_dataset = SourceDatasetFactory.create()
        self.assertRegex(source_dataset.pht_version_string, 'pht\d{6}\.v\d{1,5}.p\d{1,5}')
       

class HarmonizedTraitSetTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a HarmonizedTraitSet object."""
        harmonized_trait_set = HarmonizedTraitSetFactory.create()
        self.assertIsInstance(HarmonizedTraitSet.objects.get(pk=harmonized_trait_set.pk), HarmonizedTraitSet)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait_set = HarmonizedTraitSetFactory.build()
        self.assertIsInstance(harmonized_trait_set.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait_set = HarmonizedTraitSetFactory.create()
        self.assertIsInstance(harmonized_trait_set.created, datetime)
        self.assertIsInstance(harmonized_trait_set.modified, datetime)
    
 
class SourceTraitTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a SourceTrait object."""
        source_trait = SourceTraitFactory.create()
        self.assertIsInstance(SourceTrait.objects.get(pk=source_trait.pk), SourceTrait)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_trait = SourceTraitFactory.build()
        self.assertIsInstance(source_trait.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_trait = SourceTraitFactory.create()
        self.assertIsInstance(source_trait.created, datetime)
        self.assertIsInstance(source_trait.modified, datetime)

    def test_is_latest_version(self):
        pass

    def test_custom_save(self):
        """Test that the custom save method works."""
        source_trait = SourceTraitFactory.create()
        self.assertEqual(source_trait.study_accession, source_trait.source_dataset.source_study_version.phs_version_string)
        self.assertEqual(source_trait.dataset_accession, source_trait.source_dataset.pht_version_string)
        self.assertRegex(source_trait.variable_accession, 'phv\d{8}.v\d{1,3}.p\d{1,3}')
        self.assertEqual(source_trait.dbgap_study_link[:68], SourceTrait.STUDY_URL[:68])
        self.assertEqual(source_trait.dbgap_variable_link[:71], SourceTrait.VARIABLE_URL[:71])
        self.assertEqual(source_trait.dbgap_dataset_link[:70], SourceTrait.DATASET_URL[:70])


class HarmonizedTraitTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a HarmonizedTrait object."""
        harmonized_trait = HarmonizedTraitFactory.create()
        self.assertIsInstance(HarmonizedTrait.objects.get(pk=harmonized_trait.pk), HarmonizedTrait)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait = HarmonizedTraitFactory.build()
        self.assertIsInstance(harmonized_trait.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait = HarmonizedTraitFactory.create()
        self.assertIsInstance(harmonized_trait.created, datetime)
        self.assertIsInstance(harmonized_trait.modified, datetime)
        
    def test_custom_save(self):
        """Test that the custom save method works."""
        harmonized_trait = HarmonizedTraitFactory.create()
        self.assertEqual(harmonized_trait.trait_flavor_name, '{}_{}'.format(harmonized_trait.i_trait_name, harmonized_trait.harmonized_trait_set.i_flavor))


class SourceTraitEncodedValueTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a SourceTraitEncodedValue object."""
        source_trait_encoded_value = SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(SourceTraitEncodedValue.objects.get(pk=source_trait_encoded_value.pk), SourceTraitEncodedValue)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_trait_encoded_value = SourceTraitEncodedValueFactory.build()
        self.assertIsInstance(source_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_trait_encoded_value = SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(source_trait_encoded_value.created, datetime)
        self.assertIsInstance(source_trait_encoded_value.modified, datetime)


class HarmonizedTraitEncodedValueTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a HarmonizedTraitEncodedValue object."""
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(HarmonizedTraitEncodedValue.objects.get(pk=harmonized_trait_encoded_value.pk), HarmonizedTraitEncodedValue)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValueFactory.build()
        self.assertIsInstance(harmonized_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(harmonized_trait_encoded_value.created, datetime)
        self.assertIsInstance(harmonized_trait_encoded_value.modified, datetime)