"""Test the factory functions, which are used for testing."""

from django.test import TestCase

from . import factories
from trait_browser.factories import StudyFactory

from . import models
from trait_browser.models import Study


class SearchTest(TestCase):

    def test_search_factory_build(self):
        """A Search instance is returned by factories.SearchFactory.build()."""
        search = factories.SearchFactory.build()
        self.assertIsInstance(search, models.Search)

    def test_search_factory_create(self):
        """A Search instance is returned by factories.SearchFactory.create()."""
        search = factories.SearchFactory.create()
        self.assertIsInstance(search, models.Search)

    def test_search_factory_build_batch(self):
        """A Search instance is returned by factories.SearchFactory.build_batch()."""
        searches = factories.SearchFactory.build_batch(5)
        for rec in searches:
            self.assertIsInstance(rec, models.Search)

    def test_search_factory_create_batch(self):
        """A Search instance is returned by factories.SearchFactory.create_batch()."""
        searches = factories.SearchFactory.create_batch(5)
        for rec in searches:
            self.assertIsInstance(rec, models.Search)

    def test_search_factory_create_with_studies(self):
        """A Search instance is returned by factories.SearchFactory.create() with checked studies."""
        for i in range(3):
            StudyFactory.create()
        studies = Study.objects.all()
        search = factories.SearchFactory.create(param_studies=studies)
        self.assertIsInstance(search, models.Search)


# class ProfileModelTestCase(TestCase):
#
#     def test_profile_factory_build(self):
#         """A Profile instance is returned by factories.ProfileFactory.build()."""
#         profile = factories.ProfileFactory.build()
#         self.assertIsInstance(profile, models.Profile)
#
#     def test_profile_factory_create(self):
#         """A Profile instance is returned by factories.ProfileFactory.create()."""
#         profile = factories.ProfileFactory.create()
#         self.assertIsInstance(profile, models.Profile)
#
#     def test_profile_factory_build_batch(self):
#         """A Profile instance is returned by factories.ProfileFactory.build_batch()."""
#         profile = factories.ProfileFactory.build_batch(5)
#         for rec in profile:
#             self.assertIsInstance(rec, models.Profile)
#
#     def test_profile_factory_create_batch(self):
#         """A Profile instance is returned by factories.ProfileFactory.create_batch()."""
#         profile = factories.ProfileFactory.create_batch(5)
#         for rec in profile:
#             self.assertIsInstance(rec, models.Profile)
#
#
# class SavedSearchMetaModelTestCase(TestCase):
#
#     def test_saved_search_meta_build(self):
#         """A SavedSearchMeta instance is returned by factories.SavedSearchMetaFactory.build()."""
#         saved_search_meta = factories.SavedSearchMetaFactory.build()
#         self.assertIsInstance(saved_search_meta, models.SavedSearchMeta)
#
#     def test_saved_search_meta_create(self):
#         """A SavedSearchMeta instance is returned by factories.SavedSearchMetaFactory.create()."""
#         saved_search_meta = factories.SavedSearchMetaFactory.create()
#         self.assertIsInstance(saved_search_meta, models.SavedSearchMeta)
#
#     def test_saved_search_meta_build_batch(self):
#         """A SavedSearchMeta instance is returned by factories.SavedSearchMetaFactory.build_batch()."""
#         saved_search_meta = factories.SavedSearchMetaFactory.build_batch(5)
#         for rec in saved_search_meta:
#             self.assertIsInstance(rec, models.SavedSearchMeta)
#
#     def test_saved_search_meta_create_batch(self):
#         """A SavedSearchMeta instance is returned by factories.SavedSearchMetaFactory.create_batch()."""
#         saved_search_meta = factories.SavedSearchMetaFactory.create_batch(5)
#         for rec in saved_search_meta:
#             self.assertIsInstance(rec, models.SavedSearchMeta)
