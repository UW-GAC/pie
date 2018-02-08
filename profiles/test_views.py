"""Test the functions and classes for views.py."""

from django.core.urlresolvers import reverse
from django.test import TestCase

from . import models
from . import factories
from trait_browser.factories import StudyFactory

from core.utils import LoginRequiredTestCase, UserLoginTestCase


class ProfileViewTestCase(UserLoginTestCase):

    def test_working(self):
        url = reverse('profiles:profile')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)


class ProfileViewWithoutLoginTestCase(TestCase):

    def test_redirects(self):
        url = reverse('profiles:profile')
        response = self.client.get(url)
        # Redirected?
        expected_url = '{url}?next={redirect}'.format(redirect=reverse('profiles:profile'), url=reverse('login'))
        self.assertRedirects(response, expected_url)


class ProfilesLoginRequiredTestCase(LoginRequiredTestCase):

    def test_profiles_login_required(self):
        """All profiles urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('profiles')
