"""Test the functions and classes for views.py"""

import exrex

from django.test import TestCase, Client
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern

from core.utils import ViewsAutoLoginTestCase
from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort
from .factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory 
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


class TraitBrowserLoginRequiredTest(TestCase):
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
            fullurl = '/phenotypes/' + url
            # print('URL: ', fullurl)
            response = self.client.get(fullurl)
            # print (response)
            self.assertRedirects(response, reverse('login') + '?next=' + fullurl)