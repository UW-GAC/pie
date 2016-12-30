"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from .factories import build_test_db
from trait_browser.models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class BuildTestDbTestCase(TestCase):
    
    def test_build_db_global_studies_error(self):
        """Test that calling build_test_db() with too small a value for n_global_studies raises ValueError."""
        with self.assertRaises(ValueError):
            build_test_db(n_global_studies=1,
                          n_subcohort_range=(2,3),
                          n_dataset_range=(3,9),
                          n_trait_range=(2,16),
                          n_enc_value_range=(2,9))    
    
    def test_build_db_trait_range_error(self):
        """Test that calling build_test_db() with too small a value for n_global_studies raises ValueError."""
        with self.assertRaises(ValueError):
            build_test_db(n_global_studies=3,
                          n_subcohort_range=(2,3),
                          n_dataset_range=(3,9),
                          n_trait_range=(22,16),
                          n_enc_value_range=(2,9))    

    def test_build_db1(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(n_global_studies=3,
                      n_subcohort_range=(2,3),
                      n_dataset_range=(3,9),
                      n_trait_range=(2,16),
                      n_enc_value_range=(2,9))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(GlobalStudy.objects.count() > 0)
        self.assertTrue(Study.objects.count() > 0)
        self.assertTrue(Subcohort.objects.count() > 0)
        self.assertTrue(SourceStudyVersion.objects.count() > 0)
        self.assertTrue(SourceDataset.objects.count() > 0)
        self.assertTrue(SourceTrait.objects.count() > 0)
        self.assertTrue(SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(HarmonizedTrait.objects.count() > 0)
        self.assertTrue(HarmonizedTraitEncodedValue.objects.count() > 0)

    def test_build_db2(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(n_global_studies=10,
                      n_subcohort_range=(2,3),
                      n_dataset_range=(3,9),
                      n_trait_range=(2,16),
                      n_enc_value_range=(2,9))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(GlobalStudy.objects.count() > 0)
        self.assertTrue(Study.objects.count() > 0)
        self.assertTrue(Subcohort.objects.count() > 0)
        self.assertTrue(SourceStudyVersion.objects.count() > 0)
        self.assertTrue(SourceDataset.objects.count() > 0)
        self.assertTrue(SourceTrait.objects.count() > 0)
        self.assertTrue(SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(HarmonizedTrait.objects.count() > 0)
        self.assertTrue(HarmonizedTraitEncodedValue.objects.count() > 0)

    def test_build_db3(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(n_global_studies=3,
                      n_subcohort_range=(1,2),
                      n_dataset_range=(1,2),
                      n_trait_range=(2,3),
                      n_enc_value_range=(1,2))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(GlobalStudy.objects.count() > 0)
        self.assertTrue(Study.objects.count() > 0)
        self.assertTrue(Subcohort.objects.count() > 0)
        self.assertTrue(SourceStudyVersion.objects.count() > 0)
        self.assertTrue(SourceDataset.objects.count() > 0)
        self.assertTrue(SourceTrait.objects.count() > 0)
        self.assertTrue(SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(HarmonizedTrait.objects.count() > 0)
        self.assertTrue(HarmonizedTraitEncodedValue.objects.count() > 0)
