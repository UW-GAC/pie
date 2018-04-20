"""Utility functions, to be used across the entire project.

Following a suggestion from Two Scoops of Django 1.8.
"""

import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.urlresolvers import resolve, reverse
from django.test import TestCase, Client

from .build_test_db import build_test_db
from . import factories
from trait_browser.factories import StudyFactory

User = get_user_model()


def get_app_urls(app_name):
    """Get all of the urls for the given app name.

    Uses django-extensions management command show_urls to get the entire project's urls,
    and then pulls out only the ones that are for the module of app_name.
    """
    output = StringIO()
    call_command('show_urls', '--format=json', stdout=output)
    urls_json = json.loads(output.getvalue())
    app_urls = [d['url'] for d in urls_json if app_name in d['module']]
    return app_urls


def get_autocomplete_view_ids(response):
    """Get the pks of objects returned by an autocomplete view, from the parsed response content."""
    content = json.loads(response.content.decode('utf-8'))
    results = content['results']
    ids = [int(el['id']) for el in results]
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


class PhenotypeTaggerLoginTestCase(TestCase):
    """TestCase that creates a phenotype_tagger user and logs in as that user.

    Creates a user, adds them to phenotype_tagger group, and logs them into the site.
    """

    def setUp(self):
        super(PhenotypeTaggerLoginTestCase, self).setUp()

        self.client = Client()
        self.user_password = factories.USER_FACTORY_PASSWORD
        self.user = factories.UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        self.study = StudyFactory.create()
        self.user.profile.taggable_studies.add(self.study)
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
        self.user.is_staff = True
        self.user.save()
        self.user.refresh_from_db()
        self.client.login(username=self.user.email, password=self.user_password)


class LoginRequiredTestCase(TestCase):
    """Tests all views in an app to ensure that they are using login_required."""

    @classmethod
    def setUpClass(cls):
        super(LoginRequiredTestCase, cls).setUpClass()
        # Create a bunch of test data first, so that pk-specific URLs still work.
        build_test_db(
            n_global_studies=3, n_subcohort_range=(2, 3), n_dataset_range=(3, 9),
            n_trait_range=(3, 16), n_enc_value_range=(2, 9))

    def assert_redirect_all_urls(self, app_name):
        """Use this in a subclass to ensure all urls from urlpatterns redirect to login."""
        url_list = get_app_urls(app_name)
        for url in url_list:
            final_url = url
            if '<' in url and '>' in url:
                if '<pk>' in url:
                    print(url)
                    # print(resolve(url.replace('<pk>', '1')).func.view_class)
                    # The URL test will fail if a pk of 1 doesn't exist. I can use the above call to get the view
                    # class from the URL, and then use that to get a valid pk. BUT it will only work in
                    # Django 1.9+, so it will have to wait until the upgrade.
                    final_url = url.replace('<pk>', '1')
                else:
                    raise ValueError('URL {} has a regex that is not <pk>'.format(url))  # pragma: no cover
            response = self.client.get(final_url)
            self.assertRedirects(response, reverse('login') + '?next=' + final_url,
                                 msg_prefix='URL {} is not login required'.format(final_url))
            # print('URL {} passes login_required test...'.format(url))
