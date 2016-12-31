"""
Utility functions, to be used across the entire project. After suggestion from
Two Scoops of Django 1.8.
"""


from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from .factories import UserFactory, USER_FACTORY_PASSWORD

User = get_user_model()


class ViewsAutoLoginTestCase(TestCase):
    """TestCase to use for accessing views that require user login.
    
    Creates a user and logs them into the site, allowing access to the @login_required
    (or LoginRequiredMixin) views. Mostly used in test_views.py scripts.
    """
    
    def setUp(self):
        super(ViewsAutoLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = USER_FACTORY_PASSWORD
        self.user = UserFactory.create()
        self.client.login(username=self.user.email, password=self.user_password)