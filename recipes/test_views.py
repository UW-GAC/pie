from django.test import TestCase

from core.utils import LoginRequiredTestCase
from recipes.urls import urlpatterns


class RecipesLoginRequiredTestCase(LoginRequiredTestCase):
    
    def test_recipes_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls(urlpatterns, 'recipe')