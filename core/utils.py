"""Utility functions, to be used across the entire project.

Following a suggestion from Two Scoops of Django 1.8.
"""

import exrex
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern
from django.test import TestCase, Client

from . import factories

User = get_user_model()


def collect_all_urls(urlpatterns):
    """Returns sample urls for views in app."""
    url_list = []
    for root_pattern in urlpatterns:
        # first pattern is iterable, hence 1 element list
        find_all_urls([root_pattern], [], url_list)
    return url_list


def find_all_urls(root_patterns, parents, url_list):
    """Produce a url based on a pattern."""
    for url in root_patterns:
        regex_string = url.regex.pattern
        if isinstance(url, RegexURLResolver):
            # print('Parent: ',regex_string)
            parents.append(next(exrex.generate(regex_string, limit=1)))
            find_all_urls(url.url_patterns, parents, url_list)  # Call this function recursively.
        elif isinstance(url, RegexURLPattern):
            url_list.append(''.join(parents) + next(exrex.generate(regex_string, limit=1)))


def get_autocomplete_view_ids(response):
    """Get the pks of objects returned by an autocomplete view, from the parsed response content."""
    content = json.loads(response.content.decode('utf-8'))
    results = content['results']
    ids = [el['id'] for el in results]
    return ids


class UserLoginTestCase(TestCase):
    """TestCase that creates a user and logs in as that user.

    Creates a user and logs them into the site, allowing access to the @login_required
    (or LoginRequiredMixin) views. Mostly used in test_views.py scripts.
    """

    def setUp(self):
        super(UserLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.UserFactory.create()
        self.client.login(username=self.user.email, password=self.user_password)


class DCCAnalystLoginTestCase(TestCase):
    """TestCase that creates a dcc_analyst user and logs in as that user.

    Creates a user, adds them to dcc_analyst group, and logs them into the site.
    """

    def setUp(self):
        super(DCCAnalystLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.UserFactory.create()
        dcc_analysts = Group.objects.get(name='dcc_analysts')
        self.user.groups.add(dcc_analysts)
        self.user.is_staff = True
        self.user.save()
        self.user.refresh_from_db()
        self.client.login(username=self.user.email, password=self.user_password)


class DCCDeveloperLoginTestCase(TestCase):
    """TestCase that creates a dcc_developer user and logs in as that user.

    Creates a user, adds them to dcc_developer group, and logs them into the site.
    """

    def setUp(self):
        super(DCCDeveloperLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.UserFactory.create()
        dcc_developers = Group.objects.get(name='dcc_developers')
        self.user.groups.add(dcc_developers)
        self.user.is_staff = True
        self.user.save()
        self.user.refresh_from_db()
        self.client.login(username=self.user.email, password=self.user_password)


class RecipeSubmitterLoginTestCase(TestCase):
    """TestCase that creates a recipe_submitter user and logs in as that user.

    Creates a user, adds them to recipe_submitter group, and logs them into the site.
    """

    def setUp(self):
        super(RecipeSubmitterLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.UserFactory.create()
        recipe_submitters = Group.objects.get(name='recipe_submitters')
        self.user.groups.add(recipe_submitters)
        self.user.refresh_from_db()
        self.client.login(username=self.user.email, password=self.user_password)


class SuperuserLoginTestCase(TestCase):
    """TestCase to use for accessing views that require Superuser login.

    Creates a superuser and logs them into the site.
    """

    def setUp(self):
        super(SuperuserLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.SuperUserFactory.create()
        self.client.login(username=self.user.email, password=self.user_password)


class LoginRequiredTestCase(TestCase):
    """Tests all views in this app that they are using login_required."""

    def assert_redirect_all_urls(self, urlpatterns, pattern_root):
        """Use this in a subclass to ensure all urls from urlpatterns redirect to login."""
        url_list = collect_all_urls(urlpatterns)
        for url in url_list:
            full_url = '/' + pattern_root + '/' + url
            # print('URL: ', full_url)
            response = self.client.get(full_url)
            # print (response)
            self.assertRedirects(response, reverse('login') + '?next=' + full_url,
                                 msg_prefix='{} is not login required'.format(full_url))
