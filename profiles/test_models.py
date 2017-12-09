from datetime import datetime

from django.test import TestCase

from trait_browser.factories import StudyFactory
from . import factories
from . import models


class SearchTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        search = factories.SearchFactory.create()
        self.assertIsInstance(models.Search.objects.get(pk=search.pk), models.Search)

    def test_printing(self):
        """Test the custom __str__ method."""
        search = factories.SearchFactory.build()
        self.assertIsInstance(search.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        search = factories.SearchFactory.create()
        self.assertIsInstance(search.created, datetime)
        self.assertIsInstance(search.modified, datetime)


class UserDataTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        user_data = factories.UserDataFactory.create()
        self.assertIsInstance(models.UserData.objects.get(pk=user_data.pk), models.UserData)

    def test_printing(self):
        """Test the custom __str__ method."""
        user_data = factories.UserDataFactory.build()
        self.assertIsInstance(user_data.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        user_data = factories.UserDataFactory.create()
        self.assertIsInstance(user_data.created, datetime)
        self.assertIsInstance(user_data.modified, datetime)

    def test_adding_taggable_studies(self):
        """Studies can be added properly to the user's taggable_studies."""
        user_data = factories.UserDataFactory.create()
        studies = StudyFactory.create_batch(2)
        user_data.taggable_studies.add(*studies)
        for st in studies:
            self.assertIn(st, user_data.taggable_studies.all())


class SavedSearchMetaTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        saved_search = factories.SavedSearchMetaFactory.create()
        self.assertIsInstance(models.SavedSearchMeta.objects.get(pk=saved_search.pk), models.SavedSearchMeta)

    def test_printing(self):
        """Test the custom __str__ method."""
        saved_search = factories.SavedSearchMetaFactory.build()
        self.assertIsInstance(saved_search.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        saved_search = factories.SavedSearchMetaFactory.create()
        self.assertIsInstance(saved_search.created, datetime)
        self.assertIsInstance(saved_search.modified, datetime)
