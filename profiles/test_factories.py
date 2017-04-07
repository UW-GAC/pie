"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from .factories import *
from trait_browser.factories import StudyFactory

from .models import *
from trait_browser.models import Study


class SearchModelTestCase(TestCase):
    
    def test_user_data_factory_build(self):
        """Test that a Search instance is returned by SearchFactory.build()"""
        search = SearchFactory.build()
        self.assertIsInstance(search, Search)
        
    def test_user_data_factory_create(self):
        """Test that a Search instance is returned by SearchFactory.create()"""
        search = SearchFactory.create()
        self.assertIsInstance(search, Search)

    def test_user_data_factory_build_batch(self):
        """Test that a Search instance is returned by SearchFactory.build_batch()"""
        searches = SearchFactory.build_batch(5)
        for rec in searches:
            self.assertIsInstance(rec, Search)
        
    def test_user_data_factory_create_batch(self):
        """Test that a Search instance is returned by SearchFactory.create_batch()"""
        searches = SearchFactory.create_batch(5)
        for rec in searches:
            self.assertIsInstance(rec, Search)

    def test_user_data_factory_create_with_studies(self):
        """Test that a Search instance is returned by SearchFactory.create() with checked studies"""
        for i in range(3):
            StudyFactory.create()
        studies = Study.objects.all()
        search = SearchFactory.create(param_studies=studies)
        self.assertIsInstance(search, Search)

class UserDataModelTestCase(TestCase):
    
    def test_user_data_factory_build(self):
        """Test that a UserData instance is returned by UserDataFactory.build()"""
        user_data = UserDataFactory.build()
        self.assertIsInstance(user_data, UserData)
        
    def test_user_data_factory_create(self):
        """Test that a UserData instance is returned by UserDataFactory.create()"""
        user_data = UserDataFactory.create()
        self.assertIsInstance(user_data, UserData)

    def test_user_data_factory_build_batch(self):
        """Test that a UserData instance is returned by UserDataFactory.build_batch()"""
        user_data = UserDataFactory.build_batch(5)
        for rec in user_data:
            self.assertIsInstance(rec, UserData)
        
    def test_user_data_factory_create_batch(self):
        """Test that a UserData instance is returned by UserDataFactory.create_batch()"""
        user_data = UserDataFactory.create_batch(5)
        for rec in user_data:
            self.assertIsInstance(rec, UserData)

class SavedSearchMetaModelTestCase(TestCase):

    def test_saved_search_meta_build(self):
        """Test that a UserData instance is returned by UserDataFactory.build()"""
        saved_search_meta = SavedSearchMetaFactory.build()
        self.assertIsInstance(saved_search_meta, SavedSearchMeta)
        
    def test_saved_search_meta_create(self):
        """Test that a UserData instance is returned by UserDataFactory.create()"""
        saved_search_meta = SavedSearchMetaFactory.create()
        self.assertIsInstance(saved_search_meta, SavedSearchMeta)

    def test_saved_search_meta_build_batch(self):
        """Test that a UserData instance is returned by UserDataFactory.build_batch()"""
        saved_search_meta = SavedSearchMetaFactory.build_batch(5)
        for rec in saved_search_meta:
            self.assertIsInstance(rec, SavedSearchMeta)
        
    def test_saved_search_meta_create_batch(self):
        """Test that a UserData instance is returned by UserDataFactory.create_batch()"""
        saved_search_meta = SavedSearchMetaFactory.create_batch(5)
        for rec in saved_search_meta:
            self.assertIsInstance(rec, SavedSearchMeta)
