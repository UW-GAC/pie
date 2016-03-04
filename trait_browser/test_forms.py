"""Test the functions and classes from forms.py."""

from django.test import TestCase
from django.core.urlresolvers import reverse

from .forms import SourceTraitCrispySearchForm
from .factories import StudyFactory, SourceTraitFactory
from .models import Study


class SourceTraitCrispySearchFormTestCase(TestCase):

    def test_form_with_valid_text_no_study(self):
        """Test that the form is valid when given valid search text, but no study."""
        input = {'text': 'some_string'}
        form = SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())
    
    def test_form_with_valid_text_and_one_study(self):
        """Test that the form is valid when given valid search text and one valid study."""
        studies = StudyFactory.create_batch(10)
        input = {'text': 'some_string', 'study': [studies[0].study_id]}
        form = SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())
    
    def test_form_with_valid_text_and_multiple_studies(self):
        """Test that the form is valid when given valid search text and multiple valid studies."""
        studies = StudyFactory.create_batch(10)
        input = {
            'text': 'some_string',
            'study': [studies[0].study_id, studies[3].study_id]
        }
        form = SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())
        
    def test_form_with_invalid_text_and_one_study(self):
        """Test that the form is invalid when given invalid search text and one valid study."""
        studies = StudyFactory.create_batch(10)
        input = {
            'text': '',
            'study': [studies[0].study_id, studies[3].study_id]
        }
        form = SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())
    
    def test_form_with_valid_text_and_invalid_study(self):
        """Test that the form is invalid when given valid search text and an invalid study id."""
        input = {'text': 'some_string', 'study': [23]}
        form = SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_is_not_valid_with_invalid_text(self):
        """Test that the form is invalid when given an empty search string."""
        input = {'text': ''}
        form = SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())
    
    def test_form_with_no_input_data(self):
        """Test that the form is not bound when it's not given input data."""
        form = SourceTraitCrispySearchForm()
        self.assertFalse(form.is_bound)
    
    def test_form_has_error_with_invalid_search_text(self):
        """Test that the form has an error on the text field when given an empty search string"""
        input = {'text': ''}
        form = SourceTraitCrispySearchForm(input)
        form.is_valid()
        self.assertTrue(form.has_error('text'))
        
    def test_form_has_error_with_invalid_study(self):
        """Test that the form has an error on the study field when given an invalid study name"""
        traits = SourceTraitFactory.create_batch(5)
        studies = Study.objects.all()
        study_ids = [st.study_id for st in studies]
        # Get the first study id from 1-100 that is not in the valid studies
        bad_study_id = [n for n in range(1, 101) if n not in study_ids][0]
        input = {'text': traits[0].name, 'study': [bad_study_id]}
        form = SourceTraitCrispySearchForm(input)
        form.is_valid()
        # print(form.STUDIES)
        # print(bad_study_id)
        self.assertTrue(form.has_error('study'))
        
    def test_form_has_accurate_set_of_studies(self):
        """Test that the choices for the form match the valid set of studies available at search time."""
        studies = StudyFactory.create_batch(5)
        input = {'text': 'some_string'}
        form = SourceTraitCrispySearchForm(input)
        current_studies = [[st.pk, st.name] for st in Study.objects.all().order_by('name')]
        # print(current_studies)
        # print(form.STUDIES)
        self.assertEqual(current_studies, form.STUDIES)