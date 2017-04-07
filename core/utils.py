"""
Utility functions, to be used across the entire project. After suggestion from
Two Scoops of Django 1.8.
"""

import exrex

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern
from django.test import TestCase, Client

from .factories import *

User = get_user_model()


def collect_all_urls(urlpatterns):
    """Returns sample urls for views in app"""
    url_list = []
    for root_pattern in urlpatterns:
        # first pattern is iterable, hence 1 element list
        find_all_urls([root_pattern], [], url_list)
    return url_list

def find_all_urls(root_patterns, parents, url_list):
    """Produce a url based on a pattern"""
    for url in root_patterns:
        regex_string = url.regex.pattern
        if isinstance(url, RegexURLResolver):
            # print('Parent: ',regex_string)
            parents.append(next(exrex.generate(regex_string, limit=1)))
            find_all_urls(url.url_patterns, parents, url_list) # call this function recursively
        elif isinstance(url, RegexURLPattern):
            url_list.append(''.join(parents) + next(exrex.generate(regex_string, limit=1)))


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


class ViewsSuperuserLoginTestCase(TestCase):
    """TestCase to use for accessing views that require Superuser login.
    
    Creates a superuser and logs them into the site.
    """
    
    def setUp(self):
        super(ViewsSuperuserLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = USER_FACTORY_PASSWORD
        self.user = SuperUserFactory.create()
        self.client.login(username=self.user.email, password=self.user_password)        
        
class LoginRequiredTestCase(TestCase):
    """Tests all views in this app that they are using login_required"""

    def assert_redirect_all_urls(self, urlpatterns, pattern_root):
        """Use this in a subclass to ensure all urls from urlpatterns redirect to login."""
        url_list = collect_all_urls(urlpatterns)
        for url in url_list:
            full_url = '/' + pattern_root + '/' + url
            # print('URL: ', full_url)
            response = self.client.get(full_url)
            # print (response)
            self.assertRedirects(response, reverse('login') + '?next=' + full_url)