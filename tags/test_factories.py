"""Test the tags app factory functions, which are largley used in other tests."""


from django.test import TestCase

from . import factories
from . import models


class TagFactoryTest(TestCase):
    model = models.Tag
    model_factory = factories.TagFactory

    def test_factory_build(self):
        """A model instance is returned by model_factory.build()."""
        instance = self.model_factory.build()
        self.assertIsInstance(instance, self.model)

    def test_factory_create(self):
        """A model instance is returned by model_factory.create()."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance, self.model)

    def test_factory_build_batch(self):
        """A model instance is returned by model_factory.build_batch(5)."""
        instances = self.model_factory.build_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)

    def test_factory_create_batch(self):
        """A model instance is returned by model_factory.create_batch(5)."""
        instances = self.model_factory.create_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)


class TaggedTraitFactoryTest(TestCase):
    model = models.TaggedTrait
    model_factory = factories.TaggedTraitFactory

    def test_factory_build(self):
        """A model instance is returned by model_factory.build()."""
        instance = self.model_factory.build()
        self.assertIsInstance(instance, self.model)

    def test_factory_create(self):
        """A model instance is returned by model_factory.create()."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance, self.model)

    def test_factory_build_batch(self):
        """A model instance is returned by model_factory.build_batch(5)."""
        instances = self.model_factory.build_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)

    def test_factory_create_batch(self):
        """A model instance is returned by model_factory.create_batch(5)."""
        instances = self.model_factory.create_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)


class DCCReviewFactoryTest(TestCase):
    model = models.DCCReview
    model_factory = factories.DCCReviewFactory

    def test_factory_build(self):
        """A model instance is returned by model_factory.build()."""
        instance = self.model_factory.build()
        self.assertIsInstance(instance, self.model)

    def test_factory_create(self):
        """A model instance is returned by model_factory.create()."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance, self.model)

    def test_factory_build_batch(self):
        """A model instance is returned by model_factory.build_batch(5)."""
        instances = self.model_factory.build_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)

    def test_factory_create_batch(self):
        """A model instance is returned by model_factory.create_batch(5)."""
        instances = self.model_factory.create_batch(5)
        for one in instances:
            self.assertIsInstance(one, self.model)

    def test_status_confirmed(self):
        """A comment is not created if the status is confirmed."""
        instance = self.model_factory.create(status=models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(instance.comment, '')

    def test_status_followup(self):
        """A comment is created if the status is needs followup."""
        instance = self.model_factory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        self.assertNotEqual(instance.comment, '')
        self.assertIsInstance(instance.comment, str)
