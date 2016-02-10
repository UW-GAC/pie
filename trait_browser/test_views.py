from django.test import TestCase
from django.core.urlresolvers import reverse
from .models import SourceEncodedValue, SourceTrait, Study
from .tables import SourceTraitTable
from .views import TABLE_PER_PAGE, search

def create_study(name='Some Study', study_id=1):
    """Create a simple Study object, for testing views.
    Has default values so only set what you want to change."""
    study = Study(study_id=study_id, dbgap_id="phs000{0}".format(id), name=name)
    study.save()
    return study

def create_source_trait(dcc_trait_id=1, name='some_trait',
                        description='a very interesting trait',
                        data_type='string',
                        study=Study.objects.all()[0],
                        phs_string=Study.objects.all()[0].dbgap_id,
                        phv_string="phv000001"):
    """Create a simple SourceTrait object, for testing views.
    Has default values so only set what you want to change."""
    s_trait = SourceTrait(dcc_trait_id=dcc_trait_id, name=name,
                          description=description, data_type=data_type,
                          study=study, phs_string=phs_string,
                          phv_string=phv_string)
    s_trait.save()
    return s_trait

class TraitBrowserSearchTestCase(TestCase):
    
    def test_search_source_trait_name_exact(self):
        """Test that the search function finds an exact match in the SourceTrait
        name field, but doesn't find a non-match."""
        # Set up study and SourceTrait objects
        study = create_study()
        st_match = create_source_trait(name='foo_bar', dcc_trait_id=1)
        st_nonmatch = create_source_trait(name='sum_es', dcc_trait_id=2)
        # Get the search results
        search1 = search('foo_bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
    
    def test_search_source_trait_name_substring(self):
        """Test that the search function finds a substring match in the SourceTrait
        name field, but doesn't find a non-match."""
        # Set up study and SourceTrait objects
        study = create_study()
        st_match = create_source_trait(name='foo_bar', dcc_trait_id=1)
        st_nonmatch = create_source_trait(name='sum_es', dcc_trait_id=2)
        # Get the search results
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 

    def test_search_source_trait_description_exact(self):
        """Test that the search function finds an exact match in the SourceTrait
        description field, but doesn't find a non-match."""
        # Set up study and SourceTrait objects
        study = create_study()
        st_match = create_source_trait(description='foo and bar', dcc_trait_id=1)
        st_nonmatch = create_source_trait(description='sum and es', dcc_trait_id=2)
        # Get the search results
        search1 = search('foo and bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
    
    def test_search_source_trait_description_substring(self):
        """Test that the search function finds a substring match in the SourceTrait
        description field, but doesn't find a non-match."""
        # Set up study and SourceTrait objects
        study = create_study()
        st_match = create_source_trait(description='foo and bar', dcc_trait_id=1)
        st_nonmatch = create_source_trait(description='sum and es', dcc_trait_id=2)
        # Get the search results
        search1 = search('bar', 'source')
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 
        
    def test_search_source_trait_name_in_study(self):
        """Test that the search function finds a matching name in one particular
        study, but doesn't find a match from a different study. """
        # Set up study and SourceTrait objects
        study1 = create_study(study_id=1, name='Study 1')
        study2 = create_study(study_id=2, name='Study 2')
        st_match = create_source_trait(name='foo_bar', dcc_trait_id=1,
                                       study=Study.objects.get(study_id=1))
        st_nonmatch = create_source_trait(name='foo_bar', dcc_trait_id=2,
                                          study=Study.objects.get(study_id=2))
        # Get the search results
        search1 = search('bar', 'source', studies=[(1, 'Study 1')])
        # Check that the matching trait is found, but the non-match is not
        self.assertIn(st_match, search1) 
        self.assertNotIn(st_nonmatch, search1) 


class TraitBrowserViewsTestCase(TestCase):
    
    # The database is reset for each test method!
    
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
        create_study()
        n_traits = TABLE_PER_PAGE - 2
        for n in range(n_traits):
            create_source_trait(dcc_trait_id=n+1)
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
        create_study()
        n_traits = TABLE_PER_PAGE * 2
        for n in range(n_traits):
            create_source_trait(dcc_trait_id=n+1)
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
        create_study()
        create_source_trait()
        # Get the pk of a valid SourceTrait
        good_pk = SourceTrait.objects.all()[0].dcc_trait_id
        # Test that the page works with a valid pk
        url = reverse('trait_browser_source_trait_detail', args=[good_pk])
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
    
    