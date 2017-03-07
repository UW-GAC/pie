"""Test the functions and classes for views.py"""

from copy import copy
import re

from django.test import TestCase, Client
from django.http import QueryDict
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern

from core.utils import ViewsAutoLoginTestCase, LoginRequiredTestCase
from profiles.models import Search, UserData
from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort
from .factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory 
from .forms import SourceTraitCrispySearchForm, HarmonizedTraitCrispySearchForm
from .tables import SourceTraitTable, HarmonizedTraitTable, StudyTable
from .urls import urlpatterns
from .views import TABLE_PER_PAGE, search


# NB: The database is reset for each test method within a class!
# NB: for test methods with multiple assertions, the first failed assert statement
# will preclude any subsequent assertions


class SourceSearchTestCase(TestCase):
    
    def test_search_source_trait_name_exact(self):
        """Test that the search function finds an exact match in the SourceTrait name field, but doesn't find a non-match."""
        st_match = SourceTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('foo_bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)
    
    def test_search_source_trait_name_substring(self):
        """Test that the search function finds a substring match in the SourceTrait name field, but doesn't find a non-match."""
        st_match = SourceTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_source_trait_description_exact(self):
        """Test that the search function finds an exact match in the SourceTrait i_description field, but doesn't find a non-match."""
        st_match = SourceTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('foo and bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)
    
    def test_search_source_trait_description_substring(self):
        """Test that the search function finds a substring match in the SourceTrait i_description field, but doesn't find a non-match."""
        st_match = SourceTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)
        
    def test_search_source_trait_name_in_study(self):
        """Test that the search function finds a matching name in one particular study, but doesn't find a match from a different study. """
        study1 = StudyFactory.create(i_study_name="FHS")
        study2 = StudyFactory.create(i_study_name="CFS")
        source_dataset1 = SourceDatasetFactory.create(source_study_version__study=study1)
        source_dataset2 = SourceDatasetFactory.create(source_study_version__study=study2)
        st_match = SourceTraitFactory.create(
            i_trait_name='foo_bar',
            i_trait_id=1,
            source_dataset=source_dataset1
        )
        st_nonmatch = SourceTraitFactory.create(
            i_trait_name='foo_bar',
            i_trait_id=2,
            source_dataset=source_dataset2
        )
        search1 = search(
            'bar', 'source',
            study_pks=[study1.i_accession]
        )
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)


class HarmonizedSearchTestCase(TestCase):

    def test_search_harmonized_trait_name_exact(self):
        """Test that the search function finds an exact match in the HarmonizedTrait name field, but doesn't find a non-match."""
        st_match = HarmonizedTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = HarmonizedTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('foo_bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)
    
    def test_search_harmonized_trait_name_substring(self):
        """Test that the search function finds a substring match in the HarmonizedTrait name field, but doesn't find a non-match."""
        st_match = HarmonizedTraitFactory.create(i_trait_name='foo_bar', i_trait_id=1)
        st_nonmatch = HarmonizedTraitFactory.create(i_trait_name='sum_es', i_trait_id=2)
        search1 = search('bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)

    def test_search_harmonized_trait_description_exact(self):
        """Test that the search function finds an exact match in the HarmonizedTrait i_description field, but doesn't find a non-match."""
        st_match = HarmonizedTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = HarmonizedTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('foo and bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)
    
    def test_search_harmonized_trait_description_substring(self):
        """Test that the search function finds a substring match in the HarmonizedTrait i_description field, but doesn't find a non-match."""
        st_match = HarmonizedTraitFactory.create(i_description='foo and bar', i_trait_id=1)
        st_nonmatch = HarmonizedTraitFactory.create(i_description='sum and es', i_trait_id=2)
        search1 = search('bar', 'harmonized')
        # Check that the matching trait is found, but the non-match is not.
        self.assertIn(st_match, search1)
        self.assertNotIn(st_nonmatch, search1)


class SourceTraitViewsTestCase(ViewsAutoLoginTestCase):
    """Unit tests for the SourceTrait views."""
    
    def test_source_trait_table_empty(self):
        """Tests that the source_trait_table view works with an empty queryset and that the SourceTraitTable object has no rows."""
        # No valid SourceTraits exist here.
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)
    
    def test_source_trait_table_one_page(self):
        """Tests that the source_trait_table view works with fewer rows than will require a second page."""
        # Make less than one page of SourceTraits.
        n_traits = TABLE_PER_PAGE - 2
        SourceTraitFactory.create_batch(n_traits)
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
        SourceTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the source trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_source_trait_detail_valid(self):
        """Tests that the SourceTrait detail page returns 200 with a valid pk."""
        trait = SourceTraitFactory.create()
        # Test that the page works with a valid pk.
        url = reverse('trait_browser:source:detail', args=[trait.i_trait_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_source_trait_detail_invalid(self):
        """Tests that the SourceTrait detail page returns 404 with an invalid pk."""
        # No valid SourceTraits exist here.
        url = reverse('trait_browser:source:detail', args=[10])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_source_trait_absolute_url(self):
        """Tests the get_absolute_url() method of the SourceTrait object returns a 200 as a response."""
        trait = SourceTraitFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_source_trait_no_search_url(self):
        """Tests that the search_url is not in the response context."""
        # search_url should not be in this view
        url = reverse('trait_browser:source:all')
        response = self.client.get(url)
        with self.assertRaises(KeyError):
            response.context['search_url']


class StudySourceTableViewsTestCase(ViewsAutoLoginTestCase):
    """Unit tests for the SourceTrait by Study views."""
    
    def test_study_source_table_empty(self):
        """Tests that the study_source_table view works with an empty queryset and that the StudyTable object has no rows."""
        url = reverse('trait_browser:source:study:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is study_table a StudyTable object?
        self.assertIsInstance(response.context['study_table'], StudyTable)
        # Does the source study table object have 0 rows?
        self.assertEqual(len(response.context['study_table'].rows), 0)

    def test_study_source_table_one_page(self):
        """Tests that the study_source_table view works with fewer rows than will require a second page."""
        # Make less than one page of Studies.
        n_studies = TABLE_PER_PAGE - 2
        StudyFactory.create_batch(n_studies)
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
        StudyFactory.create_batch(n_studies)
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
        """Tests that the study_source_trait_table view works with an empty queryset and that the SourceTraitTable object has no rows."""
        # No valid SourceTraits exist here.
        this_study = StudyFactory.create()
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)

    def test_study_source_trait_table_one_page(self):
        """Tests that the study_source_trait_table view works with one page of results and that the SourceTraitTable object the correct number of rows."""
        n_traits = TABLE_PER_PAGE - 2
        this_study = StudyFactory.create()
        SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)
    
    def test_study_source_trait_table_one_page_plus_other_study(self):
        """Tests that the study_source_trait_table view works with one page of results and that the SourceTraitTable object the correct number of rows, when there is a second study."""
        n_traits = TABLE_PER_PAGE - 2
        this_study = StudyFactory.create()
        SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        other_study = StudyFactory.create()
        SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=other_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_study_source_trait_table_two_pages(self):
        """Tests that the study_source_trait_table view works with two pages of results and that the SourceTraitTable object the correct number of rows."""
        n_traits = TABLE_PER_PAGE * 2
        this_study = StudyFactory.create()
        SourceTraitFactory.create_batch(n_traits, source_dataset__source_study_version__study=this_study)
        url = reverse('trait_browser:source:study:detail', args=[this_study.i_accession])
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object?
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have correct number of rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)
        
    def test_study_source_trait_table_absolute_url(self):
        """Tests the get_absolute_url() method of the Study object returns a 200 as a response."""
        trait = StudyFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_study_source_get_search_url_response(self):
        """Tests that the get_search_url method returns a valid and correct url for a given study."""
        this_study = StudyFactory.create()
        url = this_study.get_search_url()
        response = self.client.get(url)
        # url should work
        self.assertEqual(response.status_code, 200)
        # url should be using correct i_accession value as checked box
        self.assertEqual(response.context['form'].initial['study'], str(this_study.i_accession))


class SourceTraitSearchViewTestCase(ViewsAutoLoginTestCase):

    def test_source_trait_search_with_valid_results(self):
        """Tests that the source_trait_search view has a 200 reponse code and the number of results is accurate when search text is entered and there are search results to display."""
        # Make ten random SourceTraits.
        SourceTraitFactory.create_batch(10)
        # Make one SourceTrait that will match your (improbable) search term.
        SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows),1)    # There's 1 result row.
    
    def test_source_trait_search_with_no_results(self):
        """Tests that the source_trait_search view has a 200 reponse code when search text is entered and there are no search results to display."""
        SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows), 0) # There's 0 results rows.
    
    def test_source_trait_search_with_no_search_text_entered(self):
        """Test that there is no trait table displayed when no search text is entered and the form is not bound to data."""
        SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': ''})
        self.assertEqual(response.status_code, 200)    # The view will display something.
        self.assertFalse(response.context['results'])    # results is False.
        self.assertNotIn('trait_table', response.context)    # trait_table is found.
        self.assertTrue(response.context['form'].is_bound)    # Form is bound to data
        self.assertEqual(response.context['trait_type'], 'source')    # trait type is still correct
        self.assertIsInstance(response.context['form'], SourceTraitCrispySearchForm)    # Form is of the correct type

        
    def test_source_trait_search_with_valid_results_and_study_filter(self):
        """Tests that the source_trait_search view has a 200 reponse code and the number of results is accurate when search text and study filter is entered and there are search results to display."""
        SourceTraitFactory.create_batch(10)
        good_trait = SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl',
                                         'study':[good_trait.source_dataset.source_study_version.study.i_accession]})
        self.assertEqual(response.status_code, 200)    # The page displays something.
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows),1)    # There's 1 result row.

    def test_source_trait_search_with_no_results_and_study_filter(self):
        """Tests that the source_trait_search view has a 200 response code and the number of results is accurate when search text and study filter is entered and there are no valid search results to display."""
        traits = SourceTraitFactory.create_batch(10)
        good_trait = SourceTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'text': 'asdfghjkl',
                                         'study':[traits[0].source_dataset.source_study_version.study.i_accession]})
        self.assertEqual(response.status_code, 200)    # The page displays something.
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows), 0)    # There's 0 results rows.

    def test_source_trait_search_with_no_search_text_entered_and_study_filter(self):
        """Test that there is no trait table displayed when no search text is entered, but the study filter is entered, and the form is not bound to data. """
        SourceTraitFactory.create_batch(10)
        url = reverse('trait_browser:source:search')
        response = self.client.get(url, {'study': [st.pk for st in Study.objects.all()[:3]]})
        self.assertEqual(response.status_code, 200)    # The page displays something.
        self.assertFalse(response.context['results'])    # results is False.
        self.assertNotIn('trait_table', response.context)    # The trait_table object exists.
        self.assertFalse(response.context['form'].is_bound)    # Form is not bound to data.

    def test_source_trait_search_has_no_initial_checkboxes(self):
        """Tests that the base search url does not have an initial checkbox."""
        url = reverse('trait_browser:source:search')
        response = self.client.get(url)
        self.assertEqual(len(response.context['form'].initial), 0)

    def test_source_search_is_saved(self):
        """ Test that a source search is saved """
        search_type = 'source'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        response = self.client.get(url, {'text': text})
        self.assertEqual(response.status_code, 200)
        # search exists and has the default search count of 1
        self.assertIsInstance(Search.objects.get(param_text=text, search_count=1, search_type=search_type), Search)

    def test_source_search_with_study_is_saved(self):
        """ Test that a source search with a study is saved """
        search_type = 'source'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        study = StudyFactory.create()
        response = self.client.get(url, {'text': text, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # search exists with appropriate text and study and has the default search count
        search_with_study = Search.objects.get(
            param_text=text,
            search_count=1,
            param_studies=study.pk,
            search_type=search_type
        )
        self.assertIsInstance(search_with_study, Search)

    def test_save_search_to_profile(self):
        """ Test that a source search with a study is saved and can be saved to a profile """

        # create a search
        search_type = 'source'
        get_url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        study = StudyFactory.create()
        response = self.client.get(get_url, {'text': text, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # save the search
        post_url = reverse('trait_browser:save_search')
        search_string = 'text={}&study={}'.format(text, study.pk)
        response = self.client.post(post_url, {'trait_type': search_type, 'search_params': search_string})
        self.assertEqual(response.status_code, 302)
        # ensure saved search exists for the user
        user_searches = UserData.objects.get(user_id=self.user.id).saved_searches.all()
        search = Search.objects.get(param_text=text, search_type='source')
        self.assertIn(search, user_searches)


class HarmonizedTraitViewsTestCase(ViewsAutoLoginTestCase):
    """Unit tests for the HarmonizedTrait views."""
    
    def test_harmonized_trait_table_empty(self):
        """Tests that the harmonized_trait_table view works with an empty queryset and that the HarmonizedTraitTable object has no rows."""
        # No valid HarmonizedTraits exist here.
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Is trait_table a HarmonizedTraitTable object?
        self.assertIsInstance(response.context['trait_table'], HarmonizedTraitTable)
        # Does the harmonized trait table object have 0 rows?
        self.assertEqual(len(response.context['trait_table'].rows), 0)
    
    def test_harmonized_trait_table_one_page(self):
        """Tests that the harmonized_trait_table view works with fewer rows than will require a second page."""
        # Make less than one page of HarmonizedTraits.
        n_traits = TABLE_PER_PAGE - 2
        HarmonizedTraitFactory.create_batch(n_traits)
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
        HarmonizedTraitFactory.create_batch(n_traits)
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the harmonized trait table object have n_traits rows?
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_harmonized_trait_detail_valid(self):
        """Tests that the HarmonizedTrait detail page returns 200 with a valid pk."""
        trait = HarmonizedTraitFactory.create()
        # Test that the page works with a valid pk.
        url = reverse('trait_browser:harmonized:detail', args=[trait.i_trait_id])
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
        trait = HarmonizedTraitFactory.create()
        response = self.client.get(trait.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_harmonized_trait_no_search_url(self):
        """Tests that the harmonized trait table view does not contain a search_url in the response context."""
        # search_url should not be in this view
        url = reverse('trait_browser:harmonized:all')
        response = self.client.get(url)
        with self.assertRaises(KeyError):
            response.context['search_url']


class HarmonizedTraitSearchViewTestCase(ViewsAutoLoginTestCase):

    def test_harmonized_trait_search_with_valid_results(self):
        """Tests that the harmonized_trait_search view has a 200 reponse code and the number of results is accurate when search text is entered and there are search results to display."""
        # Make ten random HarmonizedTraits.
        HarmonizedTraitFactory.create_batch(10)
        # Make one HarmonizedTrait that will match your (improbable) search term.
        HarmonizedTraitFactory.create(i_trait_name='asdfghjkl')
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], HarmonizedTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows),1)    # There's 1 result row.
    
    def test_harmonized_trait_search_with_no_results(self):
        """Tests that the harmonized_trait_search view has a 200 reponse code when search text is entered and there are no search results to display."""
        HarmonizedTraitFactory.create_batch(10)
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': 'asdfghjkl'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results'])    # results is True.
        self.assertIsInstance(response.context['trait_table'], HarmonizedTraitTable)    # trait_table is a table object.
        self.assertEqual(len(response.context['trait_table'].rows), 0) # There's 0 results rows.
    
    def test_harmonized_trait_search_with_no_search_text_entered(self):
        """Test that there is no trait table displayed when no search text is entered and the form is not bound to data."""
        HarmonizedTraitFactory.create_batch(10)
        url = reverse('trait_browser:harmonized:search')
        response = self.client.get(url, {'text': ''})
        self.assertEqual(response.status_code, 200)    # The view will display something.
        self.assertFalse(response.context['results'])    # results is False.
        self.assertNotIn('trait_table', response.context)    # trait_table is found.
        self.assertTrue(response.context['form'].is_bound)    # Form is bound to data
        self.assertEqual(response.context['trait_type'], 'harmonized')    # trait type is still correct
        self.assertIsInstance(response.context['form'], HarmonizedTraitCrispySearchForm)    # Form is of the correct type

    def test_harmonized_search_is_saved(self):
        search_type = 'harmonized'
        url = reverse('trait_browser:{}:search'.format(search_type))
        text = 'text'
        response = self.client.get(url, {'text': text})
        self.assertEqual(response.status_code, 200)
        # search exists and has the default search count of 1
        self.assertIsInstance(Search.objects.get(param_text=text, search_count=1, search_type=search_type), Search)


class TraitBrowserLoginRequiredTestCase(LoginRequiredTestCase):
    
    def test_trait_browser_login_required(self):
        """All trait_browser urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls(urlpatterns, 'phenotypes')


class SourceTraitPHVAutocompleteTestCase(ViewsAutoLoginTestCase):
    """Autocomplete view works as expected."""
    
    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Create a source trait with linked source dataset and source study version.
        source_trait = SourceTraitFactory.create(i_trait_id=5, source_dataset__i_id=6, i_dbgap_variable_accession=60, source_dataset__source_study_version__i_id=5)
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
        source_traits = SourceTraitFactory.create_batch(10)
        st1 = source_traits[0]
        url = reverse('trait_browser:source:autocomplete')
        response = self.client.get(url, {'q': st1.i_dbgap_variable_accession})
        phv_re = re.compile(r'phv\d{8}')
        phvs_in_content = [match for match in phv_re.findall(str(response.content))]
        self.assertTrue(len(phvs_in_content) == 1)
        self.assertTrue('phv{:08d}'.format(st1.i_dbgap_variable_accession) in phvs_in_content)
