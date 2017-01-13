""" """

import exrex

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern
from django.test import TestCase, Client


User = get_user_model()


def collect_all_urls(urlpatterns):
    """Returns sample urls for views in app"""
    urlList = []
    for rootpattern in urlpatterns:
        # first pattern is iterable, hence 1 element list
        find_all_urls([rootpattern], [], urlList)
    return urlList

def find_all_urls(rootpatterns, parents, urlList):
    """Produce a url based on a pattern"""
    for url in rootpatterns:
        regex_string = url.regex.pattern
        if isinstance(url, RegexURLResolver):
            # print('Parent: ',regex_string)
            parents.append(next(exrex.generate(regex_string, limit=1)))
            find_all_urls(url.url_patterns, parents, urlList) # call this function recursively
        elif isinstance(url, RegexURLPattern):
            urlList.append(''.join(parents) + next(exrex.generate(regex_string, limit=1)))


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
        urlList = collect_all_urls(urlpatterns)
        for url in urlList:
            fullurl = '/' + pattern_root + '/' + url
            print('URL: ', fullurl)
            response = self.client.get(fullurl)
            # print (response)
            self.assertRedirects(response, reverse('login') + '?next=' + fullurl)