from datetime import datetime

from django.test import TestCase

from .factories import SearchFactory, UserDataFactory, SavedSearchMetaFactory
from .models import Search, UserData, SavedSearchMeta


class SearchTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = SearchFactory.create()
        self.assertIsInstance(Search.objects.get(pk=rec.pk), Search)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = SearchFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = SearchFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)


class UserDataTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = UserDataFactory.create()
        self.assertIsInstance(UserData.objects.get(pk=rec.pk), UserData)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = UserDataFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = UserDataFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)


class SavedSearchMetaTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = SavedSearchMetaFactory.create()
        self.assertIsInstance(SavedSearchMeta.objects.get(pk=rec.pk), SavedSearchMeta)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = SavedSearchMetaFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = SavedSearchMetaFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)
