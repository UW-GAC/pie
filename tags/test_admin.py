"""Tests of custom Admins."""

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from core.utils import SuperuserLoginTestCase

from . import admin
from . import factories
from . import models


class TaggedTraitAdminTest(SuperuserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.admin = admin.TaggedTraitAdmin(models.TaggedTrait, AdminSite())

    def test_has_delete_permission_for_a_reviewed_tagged_trait_followup(self):
        """Returns False for tagged traits that require study followup."""
        tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, comment='foo',
                                          status=models.DCCReview.STATUS_FOLLOWUP)
        request = RequestFactory()
        request.user = self.user
        self.assertFalse(self.admin.has_delete_permission(request, obj=tagged_trait))

    def test_has_delete_permission_for_a_reviewed_tagged_trait_confirmed(self):
        """Returns False for confirmed tagged traits."""
        tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        request = RequestFactory()
        request.user = self.user
        self.assertFalse(self.admin.has_delete_permission(request, obj=tagged_trait))

    def test_has_delete_permission_for_unreviewed_tagged_trait(self):
        """Returns True for tagged traits that have not been reviewed."""
        tagged_trait = factories.TaggedTraitFactory.create()
        request = RequestFactory()
        request.user = self.user
        self.assertTrue(self.admin.has_delete_permission(request, obj=tagged_trait))
