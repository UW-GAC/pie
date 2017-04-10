"""Test functions and classes from models.py."""

from datetime import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse

from .factories import *
from .models import *


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
        """Tests that the get_search_url method returns an appropriately constructed url"""
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
        global_study = GlobalStudyFactory.create()
        subcohorts = SubcohortFactory.create_batch(5, global_study=global_study)
        source_dataset = SourceDatasetFactory.create(source_study_version__study__global_study=global_study, subcohorts=subcohorts)
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
    
    def test_get_trait_names(self):
        """List of trait names is correct."""
        hts = HarmonizedTraitSetFactory.create()
        htraits = HarmonizedTraitFactory.create_batch(5, harmonized_trait_set=hts)
        hts.refresh_from_db()
        self.assertEqual(sorted(hts.get_trait_names()), sorted([tr.trait_flavor_name for tr in htraits]))


class HarmonizationUnitTestCase(TestCase):
    
    def test_model_saving(self):
        """Test that you can save a HarmonizationUnit object."""
        harmonization_unit = HarmonizationUnitFactory.create()
        self.assertIsInstance(HarmonizationUnit.objects.get(pk=harmonization_unit.pk), HarmonizationUnit)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonization_unit = HarmonizationUnitFactory.build()
        self.assertIsInstance(harmonization_unit.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonization_unit = HarmonizationUnitFactory.create()
        self.assertIsInstance(harmonization_unit.created, datetime)
        self.assertIsInstance(harmonization_unit.modified, datetime)

    def test_adding_component_source_traits(self):
        """Test that adding associated component_source_traits works."""
        global_study = GlobalStudyFactory.create()
        component_source_traits = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = HarmonizationUnitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonization_unit.component_source_traits.all()), 5)

    def test_adding_component_harmonized_traits(self):
        """Test that adding associated component_harmonized_traits works."""
        htrait_set = HarmonizedTraitSetFactory.create()
        component_harmonized_traits = HarmonizedTraitFactory.create_batch(5, harmonized_trait_set=htrait_set)
        harmonization_unit = HarmonizationUnitFactory.create(component_harmonized_traits=component_harmonized_traits)
        self.assertEqual(len(harmonization_unit.component_harmonized_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Test that adding associated component_batch_traits works."""
        global_study = GlobalStudyFactory.create()
        component_batch_traits = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = HarmonizationUnitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonization_unit.component_batch_traits.all()), 5)

    def test_adding_component_age_traits(self):
        """Test that adding associated component_age_traits works."""
        global_study = GlobalStudyFactory.create()
        component_age_traits = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = HarmonizationUnitFactory.create(component_age_traits=component_age_traits)
        self.assertEqual(len(harmonization_unit.component_age_traits.all()), 5)
    
    def test_get_all_source_traits(self):
        """Returned queryset of source traits is correct."""
        source_traits = SourceTraitFactory.create_batch(6)
        hu = HarmonizationUnitFactory.create(component_age_traits=source_traits[0:2], component_batch_traits=source_traits[2:4], component_source_traits=source_traits[4:])
        self.assertEqual(list(hu.get_all_source_traits().order_by('pk')), list(SourceTrait.objects.all().order_by('pk')))
    
    def test_get_source_studies(self):
        """Returned list of linked studies is correct."""
        global_study = GlobalStudyFactory.create()
        studies = StudyFactory.create_batch(2, global_study=global_study)
        traits1 = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study=studies[0])
        traits2 = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study=studies[1])
        hu = HarmonizationUnitFactory.create(component_age_traits=[traits1[0], traits2[0]], component_batch_traits=[traits1[1], traits2[1]], component_source_traits=[traits1[2], traits2[2]])
        self.assertEqual(list(studies), list(hu.get_source_studies()))

 
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

    def test_adding_component_source_traits(self):
        """Test that adding associated component_source_traits works."""
        global_study = GlobalStudyFactory.create()
        component_source_traits = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = HarmonizedTraitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonized_trait.component_source_traits.all()), 5)

    def test_adding_component_harmonized_traits(self):
        """Test that adding associated component_harmonized_traits works."""
        htrait_set = HarmonizedTraitSetFactory.create()
        component_harmonized_traits = HarmonizedTraitFactory.create_batch(5, harmonized_trait_set=htrait_set)
        harmonized_trait = HarmonizedTraitFactory.create(component_harmonized_traits=component_harmonized_traits)
        self.assertEqual(len(harmonized_trait.component_harmonized_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Test that adding associated component_batch_traits works."""
        global_study = GlobalStudyFactory.create()
        component_batch_traits = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = HarmonizedTraitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonized_trait.component_batch_traits.all()), 5)

    def test_adding_harmonization_units(self):
        """Test that adding associated harmonization_units works."""
        htrait_set = HarmonizedTraitSetFactory.create()
        harmonization_units = HarmonizationUnitFactory.create_batch(5, harmonized_trait_set=htrait_set)
        harmonized_trait = HarmonizedTraitFactory.create(harmonization_units=harmonization_units)
        self.assertEqual(len(harmonized_trait.harmonization_units.all()), 5)


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