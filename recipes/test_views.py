from django.test import TestCase
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern

from rstr import xeger

class RecipesLoginRequiredTest(TestCase):
    """Tests all views in this app that they are using login_required"""
    def collect_all_urls(self):
        app = __import__('recipes.urls')
        urlList = []
        for rootpattern in app.urls.urlpatterns:
            # first pattern is iterable, hence 1 element list
            self.find_all_urls([rootpattern], [], urlList)
        return urlList

    def find_all_urls(self, rootpatterns, parents, urlList):
        for pattern in rootpatterns:
            if isinstance(pattern, RegexURLResolver):
                parents.append(xeger(pattern.regex))
                self.find_all_urls(pattern.url_patterns, parents, urlList) # call this function recursively
            elif isinstance(pattern, RegexURLPattern):
                urlList.append(''.join(parents) + xeger(pattern.regex))

    def test_all_urls(self):
        urlList = self.collect_all_urls()
        for url in urlList:
            fullurl = '/recipe/' + url
            print(fullurl, url)
            response = self.client.get(fullurl)
            self.assertRedirects(response, reverse('login') + '?next=' + fullurl)