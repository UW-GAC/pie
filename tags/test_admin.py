"""Tests of custom Admins."""

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from core.exceptions import DeleteNotAllowedError
from core.utils import DCCAnalystLoginTestCase, SuperuserLoginTestCase

from . import admin
from . import factories
from . import models


class TaggedTraitAdminTest(SuperuserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.admin = admin.TaggedTraitAdmin(models.TaggedTrait, AdminSite())

    def test_has_delete_permission_for_a_reviewed_tagged_trait_followup(self):
        """Returns True for tagged traits that require study followup."""
        tagged_trait = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, comment='foo',
                                          status=models.DCCReview.STATUS_FOLLOWUP)
        request = RequestFactory()
        request.user = self.user
        self.assertTrue(self.admin.has_delete_permission(request, obj=tagged_trait))

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


class TaggedTraitAdminDeleteTest(DCCAnalystLoginTestCase):

    # The deletion of a single tagged trait in the admin uses TaggedTrait.delete().
    # The deletion of multiple tagged traits uses TaggedTraitQuerySet.delete().

    def test_admin_delete_confirmed_tagged_trait_fails(self):
        """Admin edit page does not allow deletion of a confirmed tagged trait and linked dcc review."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        tagged_trait = dcc_review.tagged_trait
        delete_url = reverse('admin:tags_taggedtrait_delete', args=[tagged_trait.pk])
        get_response = self.client.get(delete_url)
        self.assertEqual(get_response.status_code, 403)
        post_response = self.client.post(delete_url, {'submit': ''})
        self.assertEqual(post_response.status_code, 403)
        messages = list(post_response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        self.assertIn(tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(dcc_review, models.DCCReview.objects.all())

    def test_admin_delete_need_followup_tagged_trait_archives(self):
        """Admin edit page archives a need_followup tagged trait and does not delete its linked dcc review."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP, comment='foo')
        tagged_trait = dcc_review.tagged_trait
        delete_url = reverse('admin:tags_taggedtrait_delete', args=[tagged_trait.pk])
        get_response = self.client.get(delete_url)
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(delete_url, {'submit': ''})
        self.assertEqual(post_response.status_code, 302)
        messages = list(post_response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        tagged_trait.refresh_from_db()
        self.assertTrue(tagged_trait.archived)
        self.assertIn(tagged_trait, models.TaggedTrait.objects.archived())
        self.assertIn(dcc_review, models.DCCReview.objects.all())

    def test_admin_delete_unreviewed_tagged_trait_succeeds(self):
        """Admin edit page deletes an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        delete_url = reverse('admin:tags_taggedtrait_delete', args=[tagged_trait.pk])
        get_response = self.client.get(delete_url)
        self.assertEqual(get_response.status_code, 200)
        post_response = self.client.post(delete_url, {'submit': ''})
        self.assertEqual(post_response.status_code, 302)
        messages = list(post_response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))
        self.assertNotIn(tagged_trait, models.TaggedTrait.objects.all())

    # For more information on admin bulk delete tests (using changelist view), see source on GitHub for
    # django/tests/admin_views/test_actions AdminActionsTest.test_model_admin_default_delete_action
    # https://github.com/django/django/blob/0adfba968e28cfb4e4d681e658866debbbd68089/tests/admin_views/test_actions.py#L43  # noqa

    def test_admin_bulk_delete_confirmed_tagged_traits_fails(self):
        """Admin bulk delete fails to delete two confirmed tagged traits."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(2, status=models.DCCReview.STATUS_CONFIRMED)
        tagged_traits = models.TaggedTrait.objects.all()
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: [tt.pk for tt in tagged_traits],
                     'post': 'yes', }
        with self.assertRaises(DeleteNotAllowedError):
            response = self.client.post(delete_url, post_data)
        for tt in tagged_traits:
            self.assertIn(tt, models.TaggedTrait.objects.all())

    def test_admin_bulk_delete_confirmed_and_unreviewed_tagged_traits_fails(self):
        """Admin bulk delete fails to delete one confirmed and one unreviewed tagged trait."""
        unreviewed_tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        confirmed_tagged_trait = dcc_review.tagged_trait
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: models.TaggedTrait.objects.values_list('pk', flat=True),
                     'post': 'yes', }
        with self.assertRaises(DeleteNotAllowedError):
            response = self.client.post(delete_url, post_data)
        self.assertIn(unreviewed_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(confirmed_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(dcc_review, models.DCCReview.objects.all())

    def test_admin_bulk_delete_need_followup_and_unreviewed_tagged_traits_archives_and_deletes(self):
        """Admin bulk delete archives one need followup and deletes one unreviewed tagged trait."""
        unreviewed_tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP, comment='foo')
        need_followup_tagged_trait = dcc_review.tagged_trait
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: models.TaggedTrait.objects.values_list('pk', flat=True),
                     'post': 'yes', }
        response = self.client.post(delete_url, post_data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully deleted', str(messages[0]))
        self.assertNotIn(unreviewed_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(need_followup_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(dcc_review, models.DCCReview.objects.all())
        need_followup_tagged_trait.refresh_from_db()
        self.assertTrue(need_followup_tagged_trait.archived)
        self.assertIn(need_followup_tagged_trait, models.TaggedTrait.objects.archived())

    def test_admin_bulk_delete_confirmed_and_need_followup_tagged_traits_fails(self):
        """Admin bulk delete fails to delete one confirmed and one need_followup tagged trait."""
        need_followup_dcc_review = factories.DCCReviewFactory.create(
            status=models.DCCReview.STATUS_FOLLOWUP, comment='foo')
        need_followup_tagged_trait = need_followup_dcc_review.tagged_trait
        confirmed_dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        confirmed_tagged_trait = confirmed_dcc_review.tagged_trait
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: models.TaggedTrait.objects.values_list('pk', flat=True),
                     'post': 'yes', }
        with self.assertRaises(DeleteNotAllowedError):
            response = self.client.post(delete_url, post_data)
        self.assertIn(need_followup_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(confirmed_tagged_trait, models.TaggedTrait.objects.all())
        self.assertIn(need_followup_dcc_review, models.DCCReview.objects.all())
        self.assertIn(confirmed_dcc_review, models.DCCReview.objects.all())

    def test_admin_bulk_delete_need_followup_tagged_traits_archives(self):
        """Admin bulk delete successfully archives two unreviewed tagged traits, doesn't delete DCCReviews."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(2, status=models.DCCReview.STATUS_FOLLOWUP, comment='foo')
        tagged_traits = models.TaggedTrait.objects.all()
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: [tt.pk for tt in tagged_traits],
                     'post': 'yes', }
        response = self.client.post(delete_url, post_data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully deleted', str(messages[0]))
        for tt in tagged_traits:
            tt.refresh_from_db()
            self.assertTrue(tt.archived)
            self.assertIn(tt, models.TaggedTrait.objects.archived())
        for dccr in dcc_reviews:
            self.assertIn(dccr, models.DCCReview.objects.all())

    def test_admin_bulk_delete_unreviewed_tagged_traits_succeeds(self):
        """Admin bulk delete successfully deletes two unreviewed tagged traits."""
        tagged_traits = factories.TaggedTraitFactory.create_batch(2)
        delete_url = reverse('admin:tags_taggedtrait_changelist')
        post_data = {'action': 'delete_selected',
                     ACTION_CHECKBOX_NAME: [tt.pk for tt in tagged_traits],
                     'post': 'yes', }
        response = self.client.post(delete_url, post_data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully deleted', str(messages[0]))
        for tt in tagged_traits:
            self.assertNotIn(tt, models.TaggedTrait.objects.all())
