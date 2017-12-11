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


class ProfileTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a UnitRecipe object."""
        profile = factories.ProfileFactory.create()
        self.assertIsInstance(models.Profile.objects.get(pk=profile.pk), models.Profile)

    def test_printing(self):
        """Test the custom __str__ method."""
        profile = factories.ProfileFactory.build()
        self.assertIsInstance(profile.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        profile = factories.ProfileFactory.create()
        self.assertIsInstance(profile.created, datetime)
        self.assertIsInstance(profile.modified, datetime)

    def test_adding_taggable_studies(self):
        """Studies can be added properly to the user's taggable_studies."""
        profile = factories.ProfileFactory.create()
        studies = StudyFactory.create_batch(2)
        profile.taggable_studies.add(*studies)
        for st in studies:
            self.assertIn(st, profile.taggable_studies.all())


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
