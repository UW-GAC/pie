"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from .factories import SourceEncodedValueFactory, SourceTraitFactory, StudyFactory
from .models import Study, SourceEncodedValue, SourceTrait


class TestFactories(TestCase):
    
    def test_study_factory_build(self):
        """Test that a Study instance is returned by StudyFactory.build()"""
        my_study = StudyFactory.build()
        self.assertIsInstance(my_study, Study)
        
    def test_study_factory_create(self):
        """Test that a Study instance is returned by StudyFactory.create()"""
        my_study = StudyFactory.create()
        self.assertIsInstance(my_study, Study)

    def test_source_trait_factory_build(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.build()"""
        my_source_trait = SourceTraitFactory.build()
        self.assertIsInstance(my_source_trait, SourceTrait)
        
    def test_source_trait_factory_create(self):
        """Test that a SourceTrait instance is returned by SourceTraitFactory.create()"""
        my_source_trait = SourceTraitFactory.create()
        self.assertIsInstance(my_source_trait, SourceTrait)

    def test_source_encoded_value_factory_build(self):
        """Test that a SourceEncodedValue instance is returned by SourceEncodedValueFactory.build()"""
        my_source_encoded_value = SourceEncodedValueFactory.build()
        self.assertIsInstance(my_source_encoded_value, SourceEncodedValue)
        
    def test_source_encoded_value_factory_create(self):
        """Test that a SourceEncodedValue instance is returned by SourceEncodedValueFactory.create()"""
        my_source_encoded_value = SourceEncodedValueFactory.create()
        self.assertIsInstance(my_source_encoded_value, SourceEncodedValue)