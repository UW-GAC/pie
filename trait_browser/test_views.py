from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import SourceEncodedValue, SourceTrait, Study
from .factories import SourceEncodedValueFactory, SourceTraitFactory, StudyFactory
from .tables import SourceTraitTable
from .views import TABLE_PER_PAGE, search

# NB: The database is reset for each test method within a class!

class TraitBrowserSearchTestCase(TestCase):
    
    def test_search_source_trait_name_exact(self):
        """Test that the search function finds an exact match in the SourceTrait
        name field, but doesn't find a non-match."""
        # Set up SourceTrait objects
        st_match = SourceTraitFactory.create(name='foo_bar', dcc_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(name='sum_es', dcc_trait_id=2)
        # Get the search results
        search1 = search('foo_bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
    
    def test_search_source_trait_name_substring(self):
        """Test that the search function finds a substring match in the SourceTrait
        name field, but doesn't find a non-match."""
        # Set up SourceTrait objects
        st_match = SourceTraitFactory.create(name='foo_bar', dcc_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(name='sum_es', dcc_trait_id=2)
        # Get the search results
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 

    def test_search_source_trait_description_exact(self):
        """Test that the search function finds an exact match in the SourceTrait
        description field, but doesn't find a non-match."""
        # Set up SourceTrait objects
        st_match = SourceTraitFactory.create(description='foo and bar', dcc_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(description='sum and es', dcc_trait_id=2)
        # Get the search results
        search1 = search('foo and bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
    
    def test_search_source_trait_description_substring(self):
        """Test that the search function finds a substring match in the SourceTrait
        description field, but doesn't find a non-match."""
        # Set up SourceTrait objects
        st_match = SourceTraitFactory.create(description='foo and bar', dcc_trait_id=1)
        st_nonmatch = SourceTraitFactory.create(description='sum and es', dcc_trait_id=2)
        # Get the search results
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
        
    def test_search_source_trait_name_in_study(self):
        """Test that the search function finds a matching name in one particular
        study, but doesn't find a match from a different study. """
        # Set up study and SourceTrait objects
        study1 = StudyFactory.create()
        study2 = StudyFactory.create()
        st_match = SourceTraitFactory.create(name='foo_bar', dcc_trait_id=1,
                                             study=study1)
        st_nonmatch = SourceTraitFactory.create(name='foo_bar', dcc_trait_id=2,
                                                study=study2)
        # Get the search results
        search1 = search('bar', 'source', studies=[(study1.study_id, study1.name)])
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 


class TraitBrowserViewsTestCase(TestCase):
    
    
    def test_source_trait_table_empty(self):
        """Tests that the source_trait_table view works with an empty queryset
        and that the SourceTraitTable object has no rows."""
        # No valid SourceTraits exist
        url = reverse('trait_browser_source_trait_table')
        response = self.client.get(url)
        # Does the URL work
        self.assertEqual(response.status_code, 200)
        # Is trait_table a SourceTraitTable object
        self.assertIsInstance(response.context['trait_table'], SourceTraitTable)
        # Does the source trait table object have 0 rows
        self.assertEqual(len(response.context['trait_table'].rows), 0)
    
    def test_source_trait_table_one_page(self):
        """Tests that the source_trait_table view works with fewer rows than
        will require a second page."""
        # Make less than one page of SourceTraits
        n_traits = TABLE_PER_PAGE - 2
        SourceTraitFactory.create_batch(n_traits)
        # Test the view
        url = reverse('trait_browser_source_trait_table')
        response = self.client.get(url)
        # Does the URL work
        self.assertEqual(response.status_code, 200)
        # Does the source trait table object have n_traits rows
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_source_trait_table_two_pages(self):
        """Tests that the source_trait_table view works with two pages' worth of
        rows."""
        # Make less than one page of SourceTraits
        n_traits = TABLE_PER_PAGE * 2
        SourceTraitFactory.create_batch(n_traits)
        # Test the view
        url = reverse('trait_browser_source_trait_table')
        response = self.client.get(url)
        # Does the URL work
        self.assertEqual(response.status_code, 200)
        # Does the source trait table object have n_traits rows
        self.assertEqual(len(response.context['trait_table'].rows), n_traits)

    def test_source_trait_detail_valid(self):
        """Tests that the SourceTrait detail page returns 200 with a valid pk"""
        # Set up a valid study and source trait
        trait = SourceTraitFactory.create()
        # Test that the page works with a valid pk
        url = reverse('trait_browser_source_trait_detail', args=[trait.dcc_trait_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_source_trait_detail_invalid(self):
        """Tests that the SourceTrait detail page returns 404 with an invalid pk"""
        # No valid SourceTraits exist
        url = reverse('trait_browser_source_trait_detail', args=[10])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    # Will need to implement test_forms.py first before trying to test this view
    def test_source_trait_search(self):
        pass
    
    