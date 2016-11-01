"""Test the functionality of the admin interface for the entire phenotype_inventory project."""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class SuperuserAutoLoginTestCase(TestCase):

    def setUp(self):
        super(SuperuserAutoLoginTestCase, self).setUp()

        self.client = Client()
        self.user = User.objects.create_superuser('super', 'foo@bar.com', 'passwd')
        self.client.login(username='super', password='passwd')


class AdminTestCase(SuperuserAutoLoginTestCase):
    """Unit tests for Trait Browser admin interface."""
    
    def test_admin_exists(self):
        """Tests that the admin site has a functioning URL."""
        url = reverse('admin:index')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)