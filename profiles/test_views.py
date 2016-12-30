"""Test the functions and classes for views.py"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core.urlresolvers import reverse

# NB: The database is reset for each test method within a class!
# NB: for test methods with multiple assertions, the first failed assert statement
# will preclude any subsequent assertions

class ViewsAutoLoginTestCase(TestCase):

    # since all views require login, this needs to be run before each test
    # make a class that we can extend for the other test cases
    def setUp(self):
        super(ViewsAutoLoginTestCase, self).setUp()

        self.client = Client()
        self.user = User.objects.create_user('unittest', 'foo@bar.com', 'passwd')
        self.client.login(username='unittest', password='passwd')

class ProfileViewTestCase(ViewsAutoLoginTestCase):

    def test_working(self):
        url = reverse('user_accounts:profile')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)

class ProfileViewWithoutLoginTestCase(TestCase):

    def test_redirects(self):
        url = reverse('user_accounts:profile')
        response = self.client.get(url)
        # Redirected?
        expected_url = '{url}?next={redirect}'.format(redirect=reverse('user_accounts:profile'), 
            url=reverse('django.contrib.auth.views.login'))

        self.assertRedirects(response, expected_url)
