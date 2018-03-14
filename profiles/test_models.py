from datetime import datetime

from django.test import TestCase

from core.factories import UserFactory
from trait_browser.factories import StudyFactory
from . import factories
from . import models


class SearchTest(TestCase):

    def test_model_saving(self):
        """Test that you can save a Search object."""
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


class ProfileTest(TestCase):

    def test_model_saving(self):
        """Test that you can save a Profile object."""
        user = UserFactory.create()
        self.assertIsInstance(user.profile, models.Profile)

    def test_printing(self):
        """Test the custom __str__ method."""
        user = UserFactory.create()
        self.assertIsInstance(user.profile.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        user = UserFactory.create()
        self.assertIsInstance(user.profile.created, datetime)
        self.assertIsInstance(user.profile.modified, datetime)

    def test_adding_taggable_studies(self):
        """Studies can be added properly to the user's taggable_studies."""
        user = UserFactory.create()
        studies = StudyFactory.create_batch(2)
        user.profile.taggable_studies.add(*studies)
        for st in studies:
            self.assertIn(st, user.profile.taggable_studies.all())


class SavedSearchMetaTest(TestCase):

    def test_model_saving(self):
        """Test that you can save a SavedSearchMeta object."""
        user = UserFactory.create()
        search = factories.SearchFactory.create()
        saved_search = models.SavedSearchMeta.objects.create(profile=user.profile, search=search)
        self.assertIsInstance(models.SavedSearchMeta.objects.get(pk=saved_search.pk), models.SavedSearchMeta)

    def test_printing(self):
        """Test the custom __str__ method."""
        user = UserFactory.create()
        search = factories.SearchFactory.create()
        saved_search = models.SavedSearchMeta.objects.create(profile=user.profile, search=search)
        self.assertIsInstance(saved_search.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        user = UserFactory.create()
        search = factories.SearchFactory.create()
        saved_search = models.SavedSearchMeta.objects.create(profile=user.profile, search=search)
        self.assertIsInstance(saved_search.created, datetime)
        self.assertIsInstance(saved_search.modified, datetime)
