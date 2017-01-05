"""Test the functions and classes for views.py"""

from django.core.urlresolvers import reverse
from django.test import TestCase

from core.utils import ViewsAutoLoginTestCase


class ProfileViewTestCase(ViewsAutoLoginTestCase):

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
        expected_url = '{url}?next={redirect}'.format(redirect=reverse('profiles:profile'), 
            url=reverse('login'))
        self.assertRedirects(response, expected_url)