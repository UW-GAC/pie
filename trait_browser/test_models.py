from django.test import TestCase
from django.core.validators import URLValidator

from .factories import StudyFactory, SourceTraitFactory, SourceEncodedValueFactory
from .models import SourceEncodedValue, SourceTrait, Study

class StudyTestCase(TestCase):
    
    def test_printing(self):
        """Ensure that the custom printing method works."""
        study = StudyFactory.build()
        self.assertIsInstance(study.__str__(), str)


class SourceTraitTestCase(TestCase):
    
    def test_is_latest_version(self):
        pass
    
    def test_get_phv_number_gets_int(self):
        """Ensure that SourceTrait.get_phv_number returns an int"""
        trait = SourceTraitFactory.build()
        phv_number = trait.get_phv_number()
        self.assertIsInstance(phv_number, int)
        
    def test_get_phv_number_phv00000001(self):
        """Ensure that SourceTrait.get_phv_number returns the correct number"""
        trait = SourceTraitFactory.build(phv_string='phv00000001')
        phv_number = trait.get_phv_number()
        self.assertEqual(phv_number, 1)

    def test_get_phv_number_many_digits(self):
        """Ensure that SourceTrait.get_phv_number returns a correct number for
        several different numbers of significant digits."""
        # Make test strings with 1 - 8 significant digits
        # Make them into tuples along with the int that they should match
        test_strings = [(10 ** x, 'phv' + '%08d'%(10 ** x)) for x in range(8)]
        for (n, phv) in test_strings:
            trait = SourceTraitFactory.build(phv_string=phv)
            phv_number = trait.get_phv_number()
            self.assertEqual(phv_number, n)

    def test_field_iter_runs(self):
        """Ensure that the field_iter generator runs"""
        trait = SourceTraitFactory.build()
        for item in trait.field_iter():
            self.assertIsNotNone(item)
            
    def test_get_dbgap_link_runs(self):
        """Ensure that get_dbgap_link builds a validly constructed URL (though
        this URL may be a broken link)."""
        # this will use regex to test that the link is a good URL
        # this will find poorly formed URLs, but not broken links
        validate = URLValidator 
        trait = SourceTraitFactory.build()
        # There is not assertNotRaises, so this one will just fail with an error
        
    def test_detail_iter_runs(self):
        """Ensure that the SourceTrait.detail_iter function will run."""
        trait = SourceTraitFactory.build()
        for item in trait.detail_iter():
            self.assertIsNotNone(item)
        
    def test_printing(self):
        """Ensure that the __str__ function works for printing the object."""
        trait = SourceTraitFactory.build()
        self.assertIsInstance(trait.__str__(), str)
        


class SourceTraitEncodedValueTestCase(TestCase):
    
    def test_printing(self):
        """Ensure that the custom printing method works."""
        enc_value = SourceEncodedValueFactory.build()
        self.assertIsInstance(enc_value.__str__(), str)

