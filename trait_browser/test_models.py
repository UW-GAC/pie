"""Test functions and classes from models.py."""

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
