""" """

import exrex

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern
from django.test import TestCase, Client


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

    # since all views require login, this needs to be run before each test
    # make a class that we can extend for the other test cases
    def setUp(self):
        super(ViewsAutoLoginTestCase, self).setUp()

        self.client = Client()
        self.user = User.objects.create_user('unit@test.com', 'passwd')
        self.client.login(email='unit@test.com', password='passwd')
        
        
class LoginRequiredTestCase(TestCase):
    """Tests all views in this app that they are using login_required"""

    def assert_redirect_all_urls(self, urlpatterns, pattern_root):
        """Use this in a subclass to ensure all urls from urlpatterns redirect to login."""
        url_list = collect_all_urls(urlpatterns)
        for url in url_list:
            full_url = '/' + pattern_root + '/' + url
            print('URL: ', full_url)
            response = self.client.get(full_url)
            # print (response)
            self.assertRedirects(response, reverse('login') + '?next=' + full_url)