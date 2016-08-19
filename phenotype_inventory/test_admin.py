"""Test the functionality of the admin interface for the entire phenotype_inventory project."""

from django.test import TestCase
from django.core.urlresolvers import reverse


class AdminTestCase(TestCase):
    """Unit tests for the views about source traits."""
    
    def test_admin_exists(self):
        """Tests that the admin site has a functioning URL."""
        url = reverse('admin:index')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 302)
        # This gives a 302 (redirect) rather than a 200 code, because it
        # redirects you to the login page. I'll change this later.