"""Test the functions and classes for views.py."""

from django.core.urlresolvers import reverse
from django.test import TestCase

from . import models
from . import factories
from trait_browser.factories import StudyFactory

from core.utils import LoginRequiredTestCase, UserLoginTestCase


class ProfileViewTestCase(UserLoginTestCase):

    def test_working(self):
        url = reverse('profiles:profile')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)


class ProfileViewWithoutLoginTestCase(TestCase):

    def test_redirects(self):
        url = reverse('profiles:profile')
        response = self.client.get(url)
        # Redirected?
        expected_url = '{url}?next={redirect}'.format(redirect=reverse('profiles:profile'), url=reverse('login'))
        self.assertRedirects(response, expected_url)


class RemoveSearchTestCase(UserLoginTestCase):
    """Test removal of searches."""

    def test_search_removal(self):
        search_type = 'source'
        study = StudyFactory.create()
        search = factories.SearchFactory.create(search_type=search_type, param_studies=[study])
        save_url = reverse('trait_browser:save_search')
        text = search.param_text
        study = [x[0] for x in search.param_studies.values_list('i_accession')][0]
        search_string = 'text={}&study={}'.format(text, study)
        self.client.post(save_url, {'trait_type': search_type, 'search_params': search_string})
        searches = models.SavedSearchMeta.objects.filter(profile__user_id=self.user.id, active=True)
        remove_url = reverse('profiles:profile')
        self.client.post(remove_url, {'search_type': search_type, 'search_id': search.id})
        self.assertEqual(searches.count(), 0)


class ProfilesLoginRequiredTestCase(LoginRequiredTestCase):

    def test_profiles_login_required(self):
        """All profiles urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('profiles')
