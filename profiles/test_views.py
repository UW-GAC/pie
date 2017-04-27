"""Test the functions and classes for views.py"""

from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import *
from .factories import *
from trait_browser.factories import StudyFactory

from core.utils import UserLoginTestCase


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
        expected_url = '{url}?next={redirect}'.format(redirect=reverse('profiles:profile'),
            url=reverse('login'))
        self.assertRedirects(response, expected_url)


class RemoveSearchTestCase(UserLoginTestCase):
    """ Test removal of searches """

    def test_search_removal(self):
        search_type = 'source'
        # create a study
        study = StudyFactory.create()
        # create a search
        search = SearchFactory.create(search_type=search_type, param_studies=[study])
        # print(search)
        # save search
        save_url = reverse('trait_browser:save_search')
        text = search.param_text
        study = [x[0] for x in search.param_studies.values_list('i_accession')][0]
        search_string = 'text={}&study={}'.format(text, study)
        self.client.post(save_url, {'trait_type': search_type, 'search_params': search_string})
        searches = SavedSearchMeta.objects.filter(user_data__user_id=self.user.id, active=True)
        # print('Saved searches: ', searches.count())
        # remove search
        remove_url = reverse('profiles:profile')
        # use search_id from saved search to remove
        self.client.post(remove_url, {'search_type': search_type, 'search_id': search.id})
        # print('Saved searches: ', searches.count())
        # make sure there are no more active
        self.assertEqual(searches.count(), 0)
