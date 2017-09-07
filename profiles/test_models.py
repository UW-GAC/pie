from datetime import datetime

from django.test import TestCase

from . import factories
from . import models


class SearchTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = factories.SearchFactory.create()
        self.assertIsInstance(models.Search.objects.get(pk=rec.pk), models.Search)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = factories.SearchFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = factories.SearchFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)


class UserDataTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = factories.UserDataFactory.create()
        self.assertIsInstance(models.UserData.objects.get(pk=rec.pk), models.UserData)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = factories.UserDataFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = factories.UserDataFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)


class SavedSearchMetaTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        rec = factories.SavedSearchMetaFactory.create()
        self.assertIsInstance(models.SavedSearchMeta.objects.get(pk=rec.pk), models.SavedSearchMeta)

    def test_printing(self):
        """Test the custom __str__ method."""
        rec = factories.SavedSearchMetaFactory.build()
        self.assertIsInstance(rec.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        rec = factories.SavedSearchMetaFactory.create()
        self.assertIsInstance(rec.created, datetime)
        self.assertIsInstance(rec.modified, datetime)
