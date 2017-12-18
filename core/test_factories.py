"""Test the factory functions, which are used for testing."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from . import factories
from .build_test_db import build_test_db
from profiles.models import Profile
import trait_browser.models


User = get_user_model()


class UserFactoryTestCase(TestCase):

    def test_user_factory_build(self):
        """Test that a User instance is returned by UserFactory.build()."""
        user = factories.UserFactory.build()
        self.assertIsInstance(user, User)

    def test_user_factory_create(self):
        """Test that a User instance is returned by UserFactory.create()."""
        user = factories.UserFactory.create()
        self.assertIsInstance(user, User)

    def test_user_factory_build_batch(self):
        """Test that a User instance is returned by UserFactory.build_batch(5)."""
        users = factories.UserFactory.build_batch(5)
        for one in users:
            self.assertIsInstance(one, User)

    def test_user_factory_create_batch(self):
        """Test that a User instance is returned by UserFactory.create_batch(5)."""
        users = factories.UserFactory.create_batch(5)
        for one in users:
            self.assertIsInstance(one, User)

    def test_profile_created(self):
        """Creating a user automatically creates an associated Profile."""
        users = factories.UserFactory.create_batch(5)
        for one in users:
            self.assertIsInstance(one.profile, Profile)


class SuperUserFactoryTestCase(TestCase):

    def test_admin_user_factory_build(self):
        """Test that a User instance is returned by factories.SuperUserFactory.build()."""
        user = factories.SuperUserFactory.build()
        self.assertIsInstance(user, User)

    def test_admin_user_factory_create(self):
        """Test that a User instance is returned by factories.SuperUserFactory.create()."""
        user = factories.SuperUserFactory.create()
        self.assertIsInstance(user, User)

    def test_admin_user_factory_build_batch(self):
        """Test that a User instance is returned by factories.SuperUserFactory.build_batch(5)."""
        users = factories.SuperUserFactory.build_batch(5)
        for one in users:
            self.assertIsInstance(one, User)

    def test_admin_user_factory_create_batch(self):
        """Test that a User instance is returned by factories.SuperUserFactory.create_batch(5)."""
        users = factories.SuperUserFactory.create_batch(5)
        for one in users:
            self.assertIsInstance(one, User)

    def test_admin_user_factory_is_superuser(self):
        """Test that a User instance is returned by factories.SuperUserFactory.create()."""
        user = factories.SuperUserFactory.create()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class BuildTestDbTestCase(TestCase):

    def test_build_db_global_studies_error(self):
        """Test that calling build_test_db() with too small a value for n_global_studies raises ValueError."""
        with self.assertRaises(ValueError):
            build_test_db(
                n_global_studies=1, n_subcohort_range=(2, 3), n_dataset_range=(3, 9),
                n_trait_range=(2, 16), n_enc_value_range=(2, 9))

    def test_build_db_trait_range_error(self):
        """Test that calling build_test_db() with invalid values for n_trait_range raises ValueError."""
        with self.assertRaises(ValueError):
            build_test_db(
                n_global_studies=3, n_subcohort_range=(2, 3), n_dataset_range=(3, 9),
                n_trait_range=(22, 16), n_enc_value_range=(2, 9))

    def test_build_db1(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(
            n_global_studies=3, n_subcohort_range=(2, 3), n_dataset_range=(3, 9),
            n_trait_range=(3, 16), n_enc_value_range=(2, 9))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(trait_browser.models.GlobalStudy.objects.count() > 0)
        self.assertTrue(trait_browser.models.Study.objects.count() > 0)
        self.assertTrue(trait_browser.models.Subcohort.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceStudyVersion.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceDataset.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitEncodedValue.objects.count() > 0)

    def test_build_db2(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(
            n_global_studies=10, n_subcohort_range=(2, 3), n_dataset_range=(3, 9),
            n_trait_range=(3, 16), n_enc_value_range=(2, 9))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(trait_browser.models.GlobalStudy.objects.count() > 0)
        self.assertTrue(trait_browser.models.Study.objects.count() > 0)
        self.assertTrue(trait_browser.models.Subcohort.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceStudyVersion.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceDataset.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitEncodedValue.objects.count() > 0)

    def test_build_db3(self):
        """Test that building a db of fake data works. Run the same test several times with different values."""
        build_test_db(
            n_global_studies=3, n_subcohort_range=(1, 2), n_dataset_range=(1, 2),
            n_trait_range=(3, 4), n_enc_value_range=(1, 2))
        # Make sure there are saved objects for each of the models.
        self.assertTrue(trait_browser.models.GlobalStudy.objects.count() > 0)
        self.assertTrue(trait_browser.models.Study.objects.count() > 0)
        self.assertTrue(trait_browser.models.Subcohort.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceStudyVersion.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceDataset.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.SourceTraitEncodedValue.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitSet.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTrait.objects.count() > 0)
        self.assertTrue(trait_browser.models.HarmonizedTraitEncodedValue.objects.count() > 0)
