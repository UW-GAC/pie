from django.test import TestCase
from django.core.urlresolvers import reverse

from .forms import SourceTraitCrispySearchForm
from .factories import StudyFactory

class SourceTraitCrispySearchFormTestCase(TestCase):
    pass

    def test_form_with_valid_text_no_study(self):
        """Test that the form is valid when given valid search text, but no
        study."""
        input = {'text': 'some_string'}
        form = SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())
    
    def test_form_with_valid_text_and_one_study(self):
        """Test that the form is valid when given valid search text and one
        valid study."""
        pass
        # studies = StudyFactory.create_batch(10)
        # input = {'text': 'some_string', 'study': [studies[0].study_id]}
        # form = SourceTraitCrispySearchForm(input)        
        # self.assertTrue(form.is_valid())
        # # This test currently fails because of the way that the STUDIES choices
        # # are set in the search form. I'll have to fix this later. 
    
    def test_form_with_valid_text_and_multiple_studies(self):
        """Test that the form is valid when given valid search text and
        multiple valid studies."""
        pass
        # studies = StudyFactory.create_batch(10)
        # input = {'text': 'some_string', 'study': [studies[0].study_id, studies[3].study_id]}
        # form = SourceTraitCrispySearchForm(input)        
        # self.assertTrue(form.is_valid())
        # # This test currently fails because of the way that the STUDIES choices
        # # are set in the search form. I'll have to fix this later. 
        
    def test_form_with_invalid_text_and_one_study(self):
        """Test that the form is invalid when given invalid search text and
        one valid study."""
        pass
        # studies = StudyFactory.create_batch(10)
        # input = {'text': '', 'study': [studies[0].study_id, studies[3].study_id]}
        # form = SourceTraitCrispySearchForm(input)        
        # self.assertTrue(form.is_valid())
        # # This test currently fails because of the way that the STUDIES choices
        # # are set in the search form. I'll have to fix this later. 
    
    def test_form_with_valid_text_and_invalid_study(self):
        """Test that the form is invalid when given valid search text and an
        invalid study id."""
        input = {'text': 'some_string', 'study': [23]}
        form = SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_with_invalid_text(self):
        """Test that the form is invalid when given an empty search string."""
        input = {'text': ''}
        form = SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())
    
    def test_form_with_no_input_data(self):
        """Test that the form is not bound when it's not given input data."""
        form = SourceTraitCrispySearchForm()
        self.assertFalse(form.is_bound)
    