import exrex

from django.test import TestCase
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern

from recipes.urls import urlpatterns


class RecipesLoginRequiredTest(TestCase):
    """Tests all views in this app that they are using login_required"""
    def collect_all_urls(self):
        """Returns sample urls for views in app"""
        urlList = []
        for rootpattern in urlpatterns:
            # first pattern is iterable, hence 1 element list
            self.find_all_urls([rootpattern], [], urlList)
        return urlList

    def find_all_urls(self, rootpatterns, parents, urlList):
        """Produce a url based on a pattern"""
        for url in rootpatterns:
            regex_string = url.regex.pattern
            if isinstance(url, RegexURLResolver):
                # print('Parent: ',regex_string)
                parents.append(next(exrex.generate(regex_string, limit=1)))
                self.find_all_urls(url.url_patterns, parents, urlList) # call this function recursively
            elif isinstance(url, RegexURLPattern):
                urlList.append(''.join(parents) + next(exrex.generate(regex_string, limit=1)))

    def test_all_urls(self):
        """Test to ensure all views redirect to login for this app"""
        urlList = self.collect_all_urls()
        for url in urlList:
            fullurl = '/recipe/' + url
            print(fullurl)
            response = self.client.get(fullurl)
            self.assertRedirects(response, reverse('login') + '?next=' + fullurl)