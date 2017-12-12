"""Test the functions and classes for views.py."""

from copy import copy
import re

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase

from core.utils import UserLoginTestCase, LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, get_autocomplete_view_ids
from profiles.models import Search, Profile
from tags.models import TaggedTrait
from tags.factories import TagFactory
from . import models
from . import factories
from . import forms
from . import tables
from .views import TABLE_PER_PAGE, search


# NB: The database is reset for each test method within a class!
# NB: for test methods with multiple assertions, the first failed assert statement
# will preclude any subsequent assertions


class SourceSearchTestCase(TestCase):

    def test_search_source_trait_name_exact(self):
        """Finds an exact match in the SourceTrait name field, but doesn't find a non-match."""
        st_match = factories.SourceTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = factories.SourceTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('foo_bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_source_trait_name_substring(self):
        """Finds a substring match in the SourceTrait name field, but doesn't find a non-match."""
        st_match = factories.SourceTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = factories.SourceTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_source_trait_description_exact(self):
        """Finds an exact match in the SourceTrait i_description field, but doesn't find a non-match."""
        st_match = factories.SourceTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = factories.SourceTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('foo and bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_source_trait_description_substring(self):
        """Finds a substring match in the SourceTrait i_description field, but doesn't find a non-match."""
        st_match = factories.SourceTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = factories.SourceTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_source_trait_name_in_study(self):
        """Finds a matching name in one particular study, but doesn't find a match from a different study."""
        study1 = factories.StudyFactory.create(i_study_name="FHS")
        study2 = factories.StudyFactory.create(i_study_name="CFS")
        source_dataset1 = factories.SourceDatasetFactory.create(source_study_version__study=study1)
        source_dataset2 = factories.SourceDatasetFactory.create(source_study_version__study=study2)
        st_match = factories.SourceTraitFactory.create(
            i_trait_name='foo_bar', i_trait_id=1, source_dataset=source_dataset1)
        st_nonmatch = factories.SourceTraitFactory.create(
            i_trait_name='foo_bar', i_trait_id=2, source_dataset=source_dataset2)
        search1 = search('bar', 'source', study_pks=[study1.i_accession])
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)


class HarmonizedSearchTestCase(TestCase):

    def test_search_harmonized_trait_name_exact(self):
        """Finds an exact match in the HarmonizedTrait name field, but doesn't find a non-match."""
        st_match = factories.HarmonizedTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = factories.HarmonizedTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('foo_bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_harmonized_trait_name_substring(self):
        """Finds a substring match in the HarmonizedTrait name field, but doesn't find a non-match."""
        st_match = factories.HarmonizedTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = factories.HarmonizedTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_harmonized_trait_description_exact(self):
        """Finds an exact match in the HarmonizedTrait i_description field, but doesn't find a non-match."""
        st_match = factories.HarmonizedTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = factories.HarmonizedTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('foo and bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_harmonized_trait_description_substring(self):
        """Finds a substring match in the HarmonizedTrait i_description field, but doesn't find a non-match."""
        st_match = factories.HarmonizedTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = factories.HarmonizedTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)


class SourceTraitDetailTest(UserLoginTestCase):

    def setUp(self):
        super(SourceTraitDetailTest, self).setUp()
        Profile.objects.create(user=self.user)
        self.trait = factories.SourceTraitFactory.create()

    def get_url(self, *args):
        return reverse('trait_browser:source:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertIn('source_trait', context)
        self.assertEqual(context['source_trait'], self.trait)
        self.assertIn('tags', context)
        self.assertEqual(context['tags'], [])
        self.assertIn('user_is_study_tagger', context)
        self.assertFalse(context['user_is_study_tagger'])

    def test_no_tagging_button(self):
        """Regular user does not see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertNotContains(response, 'Tag this phenotype')


class SourceTraitDetailPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(SourceTraitDetailPhenotypeTaggerTest, self).setUp()
        self.trait = factories.SourceTraitFactory.create()
        self.tag = TagFactory.create()
        Profile.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.trait.source_dataset.source_study_version.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_has_tagging_button(self):
        """A phenotype tagger does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertContains(response, 'Tag this phenotype')

    def test_user_is_study_tagger_true(self):
        """user_is_study_tagger is true in the view's context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertTrue(context['user_is_study_tagger'])


class SourceTraitViewsTestCase(UserLoginTestCase):
    """Unit tests for the SourceTrait views."""

    def test_source_trait_table_empty(self):
        """Without any SourceTraits, returns 200 code and the SourceTraitTable object has no rows."""
        # No valid SourceTraits exist here.
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        # Does the source trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_source_trait_table_one_page(self):
        """Tests that the source_trait_table view works with fewer rows than will require a second page."""
        # Make less than one page of SourceTraits.
        n_traits = TABLE_PER_PAGE - 2
        factories.SourceTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the source trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_source_trait_table_two_pages(self):
        """Tests that the source_trait_table view works with two pages' worth of rows."""
        # Make less than one page of SourceTraits.
        n_traits = TABLE_PER_PAGE * 2
        factories.SourceTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the source trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_source_trait_absolute_url(self):
        """Tests the get_absolute_url() method of the SourceTrait object returns a 200 as a response."""
        trait = factories.SourceTraitFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_source_trait_no_search_url(self):
        """Tests that the search_url is not in the response context."""
        # search_url should not be in this view
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        with self.assertRaises(KeyError):
            response.context['search_url']


class StudySourceTableViewsTestCase(UserLoginTestCase):
    """Unit tests for the SourceTrait by Study views."""

    def test_study_source_table_empty(self):
        """Without any source traits, the StudyTable object has no rows and the view returns 200."""
        url = reverse('trait_browser:source:study:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is study_table a StudyTable object?
        self.assertIsInstance(response.context['study_table'], tables.StudyTable)
        # Does the source study table object have 0 rows?
        self.assertEqual(len(response.context['study_table'].rows), 0)

    def test_study_source_table_one_page(self):
        """Tests that the study_source_table view works with fewer rows than will require a second page."""
        # Make less than one page of Studies.
        n_studies = TABLE_PER_PAGE - 2
        factories.StudyFactory.create_batch(n_studies)
        url = reverse('trait_browser:source:study:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the study table object have n_studies rows?
        self.assertEqual(len(response.context['study_table'].rows), n_studies)

    def test_study_source_table_two_pages(self):
        """Tests that the study_source_table view works with two pages' worth of rows."""
        # Make less than one page of Studies.
        n_studies = TABLE_PER_PAGE * 2
        factories.StudyFactory.create_batch(n_studies)
        url = reverse('trait_browser:source:study:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the study source table object have n_studies rows?
        self.assertEqual(len(response.context['study_table'].rows), n_studies)

    def test_study_source_trait_table_invalid(self):
        """Tests that the study_source_trait_table view returns 404 with an invalid pk."""
        # No valid Studies
        url = reverse('trait_browser:source:study:detail', args=[10])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_study_source_trait_table_empty(self):
        """Wihtout any source traits, view returns 200 code and the table has 0 rows."""
        # No valid SourceTraits exist here.
        this_study = factories.StudyFactory.create()
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        # Does the source trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_study_source_trait_table_one_page(self):
        """Source trait table has correct number of rows with only one page of results."""
        n_traits = TABLE_PER_PAGE - 2
        this_study = factories.StudyFactory.create()
        factories.SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_study_source_trait_table_one_page_plus_other_study(self):
        """Table has correct number of rows with one page of results, even when there's another study."""
        n_traits = TABLE_PER_PAGE - 2
        this_study = factories.StudyFactory.create()
        factories.SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        other_study = factories.StudyFactory.create()
        factories.SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=other_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_study_source_trait_table_two_pages(self):
        """Table has correct number of rows when there are two pages of SourceTrait results."""
        n_traits = TABLE_PER_PAGE * 2
        this_study = factories.StudyFactory.create()
        factories.SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_study_source_trait_table_absolute_url(self):
        """Tests the get_absolute_url() method of the Study object returns a 200 as a response."""
        trait = factories.StudyFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_study_source_get_search_url_response(self):
        """Tests that the get_search_url method returns a valid and correct url for a given study."""
        this_study = factories.StudyFactory.create()
        url = this_study.get_search_url()
        response = self.client.get(url)
        # url should work
        self.assertEqual(response.status_code, 200)
        # url should be using correct i_accession value as checked box
        self.assertEqual(response.context['form'].initial['study'], str(this_study.i_accession))


class SourceTraitSearchViewTestCase(UserLoginTestCase):

    def test_source_trait_search_with_valid_results(self):
        """Returns 200 code and correct number of search results when valid results exist."""
        # Make ten random SourceTraits.
        factories.SourceTraitFactory.create_batch(10)
        # Make one SourceTrait that will match your (improbable) search term.
        factories.SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 1)

    def test_source_trait_search_with_no_results(self):
        """Returns 200 code and empty table when there are no valid search results."""
        factories.SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_source_trait_search_with_no_search_text_entered(self):
        """There is no trait table displayed when no search text is entered and the form is not bound to data."""
        factories.SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['results'])
        self.assertNotIn('trait_table', response.context)
        self.assertTrue(response.context['form'].is_bound)
        self.assertEqual(response.context['trait_type'], 'source')
        self.assertIsInstance(response.context['form'], forms.SourceTraitCrispySearchForm)

    def test_source_trait_search_with_valid_results_and_study_filter(self):
        """Returns 200 code and correct number of results when there are valid results for study-filtered search."""
        factories.SourceTraitFactory.create_batch(10)
        good_trait = factories.SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl',
                                         'study': [good_trait.source_dataset.source_study_version.study.i_accession]})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 1)

    def test_source_trait_search_with_no_results_and_study_filter(self):
        """Returns 0 results and 200 code for invalid study-filtered search."""
        traits = factories.SourceTraitFactory.create_batch(10)
        good_trait = factories.SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl',
                                         'study': [traits[0].source_dataset.source_study_version.study.i_accession]})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.SourceTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_source_trait_search_with_no_search_text_entered_and_study_filter(self):
        """Trait table is not in context when study filter is checked but form is unbound."""
        factories.SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'study': [st.pk for st in models.Study.objects.all()[:3]]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['results'])
        self.assertNotIn('trait_table', response.context)
        self.assertFalse(response.context['form'].is_bound)

    def test_source_trait_search_has_no_initial_checkboxes(self):
        """Tests that the base search url does not have an initial checkbox."""
        url = reverse('trait_browser:source:search')
        response = self.client.get(url)
        self.assertEqual(len(response.context['form'].initial), 0)

    def test_source_search_is_saved(self):
        """The search is saved after being submitted."""
        search_type = 'source'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        response = self.client.get(url, {'text': text})
        self.assertEqual(response.status_code, 200)
        # Search exists and has the default search count of 1.
        self.assertIsInstance(Search.objects.get(param_text=text, search_count=1, search_type=search_type), Search)

    def test_source_search_with_study_is_saved(self):
        """A source search with a study is saved after being submitted."""
        search_type = 'source'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        study = factories.StudyFactory.create()
        response = self.client.get(url, {'text': text, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # search exists with appropriate text and study and has the default search count
        search_with_study = Search.objects.get(
            param_text=text, search_count=1, param_studies=study.pk, search_type=search_type)
        self.assertIsInstance(search_with_study, Search)

    def test_save_search_to_profile(self):
        """A source search with a study is saved and can be saved to a profile."""
        # Create a search.
        search_type = 'source'
        get_url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        study = factories.StudyFactory.create()
        response = self.client.get(get_url, {'text': text, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # Save the search.
        post_url = reverse('trait_browser:save_search')
        search_string = 'text={}&study={}'.format(text, study.pk)
        response = self.client.post(post_url, {'trait_type': search_type, 'search_params': search_string})
        self.assertEqual(response.status_code, 302)
        # Ensure saved search exists for the user.
        user_searches = Profile.objects.get(user_id=self.user.id).saved_searches.all()
        search = Search.objects.get(param_text=text, search_type='source')
        self.assertIn(search, user_searches)


class SourceDatasetViewTest(UserLoginTestCase):
    """Unit tests for the SourceDataset views."""

    def test_source_dataset_absolute_url(self):
        """Tests the get_absolute_url() method of the SourceDataset object returns a 200 as a response."""
        dataset = factories.SourceDatasetFactory.create()
        source_traits = factories.SourceTraitFactory.create_batch(10, source_dataset=dataset)
        response = self.client.get(dataset.get_absolute_url())
        self.assertEqual(response.status_code, 200)


class HarmonizedTraitViewsTestCase(UserLoginTestCase):
    """Unit tests for the HarmonizedTrait views."""

    def test_harmonized_trait_table_empty(self):
        """Returns 200 code and 0 results when no valid results exist."""
        # No valid HarmonizedTraits exist here.
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a HarmonizedTraitTable object?
        self.assertIsInstance(response.context['trait_table'], tables.HarmonizedTraitTable)
        # Does the harmonized trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_harmonized_trait_table_one_page(self):
        """Tests that the harmonized_trait_table view works with fewer rows than will require a second page."""
        # Make less than one page of HarmonizedTraits.
        n_traits = TABLE_PER_PAGE - 2
        factories.HarmonizedTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the harmonized trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_harmonized_trait_table_two_pages(self):
        """Tests that the harmonized_trait_table view works with two pages' worth of rows."""
        # Make less than one page of HarmonizedTraits.
        n_traits = TABLE_PER_PAGE * 2
        factories.HarmonizedTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the harmonized trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_harmonized_trait_detail_valid(self):
        """Tests that the HarmonizedTrait detail page returns 200 with a valid pk."""
        trait = factories.HarmonizedTraitFactory.create()
        # Test that the page works with a valid pk.
        url = reverse('trait_browser:harmonized:detail', args=[trait.harmonized_trait_set_version.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonized_trait_detail_invalid(self):
        """Tests that the HarmonizedTrait detail page returns 404 with an invalid pk."""
        # No valid HarmonizedTraits exist here.
        url = reverse('trait_browser:harmonized:detail', args=[10])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_harmonized_trait_absolute_url(self):
        """Tests the get_absolute_url() method of the SourceTrait object returns a 200 as a response."""
        trait = factories.HarmonizedTraitFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_harmonized_trait_no_search_url(self):
        """Tests that the harmonized trait table view does not contain a search_url in the response context."""
        # search_url should not be in this view
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        with self.assertRaises(KeyError):
            response.context['search_url']


class HarmonizedTraitSetVersionViewsTest(UserLoginTestCase):
    """Unit tests for the HarmonizedTraitSet views."""

    def test_harmonized_trait_set_absolute_url(self):
        """get_absolute_url() returns a 200 as a response."""
        instance = factories.HarmonizedTraitSetVersionFactory.create()
        response = self.client.get(instance.get_absolute_url())
        self.assertEqual(response.status_code, 200)


class HarmonizedTraitSearchViewTestCase(UserLoginTestCase):

    def test_harmonized_trait_search_with_valid_results(self):
        """Returns 200 code and correct number of results when only 1 result exists."""
        # Make ten random HarmonizedTraits.
        factories.HarmonizedTraitFactory.create_batch(10)
        # Make one HarmonizedTrait that will match your (improbable) search term.
        factories.HarmonizedTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.HarmonizedTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 1)

    def test_harmonized_trait_search_with_no_results(self):
        """Returns 200 code and 0 results when there are no matches."""
        factories.HarmonizedTraitFactory.create_batch(10)
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])
        self.assertIsInstance(response.context['trait_table'], tables.HarmonizedTraitTable)
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_harmonized_trait_search_with_no_search_text_entered(self):
        """There is no trait table displayed when no search text is entered and the form is not bound to data."""
        factories.HarmonizedTraitFactory.create_batch(10)
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['results'])
        self.assertNotIn('trait_table', response.context)
        self.assertTrue(response.context['form'].is_bound)
        self.assertEqual(response.context['trait_type'], 'harmonized')
        self.assertIsInstance(response.context['form'], forms.HarmonizedTraitCrispySearchForm)

    def test_harmonized_search_is_saved(self):
        """Search for a harmonized trait is saved after submitting the search form."""
        search_type = 'harmonized'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        response = self.client.get(url, {'text': text})
        self.assertEqual(response.status_code, 200)
        # Search exists and has the default search count of 1.
        self.assertIsInstance(Search.objects.get(param_text=text, search_count=1, search_type=search_type), Search)


class TraitBrowserLoginRequiredTestCase(LoginRequiredTestCase):

    def test_trait_browser_login_required(self):
        """All trait_browser urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('trait_browser')


class SourceTraitPHVAutocompleteTestCase(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Create a source trait with linked source dataset and source study version.
        source_trait = factories.SourceTraitFactory.create(
            i_trait_id=5, source_dataset__i_id=6, i_dbgap_variable_accession=60,
            source_dataset__source_study_version__i_id=5)
        ds = source_trait.source_dataset
        ssv = source_trait.source_dataset.source_study_version
        # Copy the source study version and increment it.
        ssv2 = copy(ssv)
        ssv2.i_version += 1
        ssv2.i_id += 1
        ssv2.save()
        # Make the old ssv deprecated.
        ssv.i_is_deprecated = True
        ssv.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        ds2 = copy(ds)
        ds2.i_id += 1
        ds2.source_study_version = ssv2
        ds2.save()
        # Copy the source trait and increment it. Link it to the new source dataset.
        source_trait2 = copy(source_trait)
        source_trait2.source_dataset = ds2
        source_trait2.i_trait_id += 1
        source_trait2.save()
        # Get results from the autocomplete view and make sure only the new version is found.
        url = reverse('trait_browser:source:autocomplete')
        response = self.client.get(url, {'q': source_trait2.i_dbgap_variable_accession})
        id_re = re.compile(r'"id": (\d+)')
        ids_in_content = [match[0] for match in id_re.findall(str(response.content))]
        self.assertTrue(len(ids_in_content) == 1)
        self.assertTrue(str(source_trait2.i_trait_id) in ids_in_content)

    def test_proper_phv_in_queryset(self):
        """Queryset returns only the proper phv number."""
        source_traits = factories.SourceTraitFactory.create_batch(10)
        st1 = source_traits[0]
        url = reverse('trait_browser:source:autocomplete')
        response = self.client.get(url, {'q': st1.i_dbgap_variable_accession})
        phv_re = re.compile(r'phv\d{8}')
        phvs_in_content = [match for match in phv_re.findall(str(response.content))]
        self.assertTrue(len(phvs_in_content) == 1)
        self.assertTrue('phv{:08d}'.format(st1.i_dbgap_variable_accession) in phvs_in_content)


class TaggableStudyFilteredSourceTraitPHVAutocompleteTestCase(PhenotypeTaggerLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(TaggableStudyFilteredSourceTraitPHVAutocompleteTestCase, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        self.source_traits = factories.SourceTraitFactory.create_batch(8, source_dataset=self.source_dataset)
        Profile.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:taggable-autocomplete')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only traits from the user's taggable studies."""
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            8, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertNotIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_proper_phv_in_queryset(self):
        """Queryset returns only the proper phv number."""
        query_trait = self.source_traits[0]
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': query_trait.i_dbgap_variable_accession})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), 1)
        self.assertIn(query_trait.pk, returned_pks)
        self.assertNotIn(self.source_traits[2].pk, returned_pks)

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)


class HarmonizedTraitFlavorNameAutocompleteViewTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Create a source trait with linked source dataset and source study version.
        # Make some fake data here.
        # Get results from the autocomplete view and make sure only the new version is found.
        # url = reverse('trait_browser:source:autocomplete')
        # response = self.client.get(url, {'q': source_trait2.i_dbgap_variable_accession})
        # id_re = re.compile(r'"id": (\d+)')
        # ids_in_content = [match[0] for match in id_re.findall(str(response.content))]
        # self.assertTrue(len(ids_in_content) == 1)
        # self.assertTrue(str(source_trait2.i_trait_id) in ids_in_content)
        pass

    def test_proper_phv_in_queryset(self):
        """Queryset returns only the proper phv number."""
        harmonized_traits = factories.HarmonizedTraitFactory.create_batch(10)
        ht1 = harmonized_traits[0]
        url = reverse('trait_browser:harmonized:autocomplete')
        response = self.client.get(url, {'q': ht1.trait_flavor_name})
        names_re = re.compile(r'"text": "(.+?)"')
        names_in_content = [match for match in names_re.findall(str(response.content))]
        self.assertTrue(len(names_in_content) == 1)
        self.assertEqual(names_in_content[0], ht1.trait_flavor_name)


class SourceTraitTaggingTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(SourceTraitTaggingTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.trait = factories.SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = TagFactory.create()
        Profile.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.study)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('trait_browser:source:tagging', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('trait' in context)
        self.assertEqual(context['trait'], self.trait)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.trait.pk), {'tag': self.tag.pk, 'recommended': False})
        new_object = TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, TaggedTrait)
        self.assertRedirects(response, reverse('trait_browser:source:detail', args=[self.trait.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_tag(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['tag'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.trait.pk),
                                    {'tag': self.tag.pk, 'recommended': False})
        new_object = TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_trait_not_in_taggable_studies(self):
        """View returns 403 code when the trait is not in the user's taggable_studies."""
        # Remove the study linked to the trait, but add another study so that taggable_studies is not empty.
        self.user.profile.taggable_studies.remove(self.study)
        another_study = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(another_study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)
