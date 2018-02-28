"""Test the functions and classes from forms.py."""

from django.test import TestCase

from . import factories
from . import forms
from . import models


class SourceTraitSearchFormTest(TestCase):

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = forms.SourceTraitSearchForm()
        self.assertFalse(form.is_bound)

    def test_form_is_invalid_with_blank_name_and_description(self):
        """Form is invalid if both name and description are blank."""
        study = factories.StudyFactory.create()
        input = {'description': '', 'name': '', 'studies': [study.pk]}
        form = forms.SourceTraitSearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_with_valid_description_and_no_studies(self):
        """Form is valid when given appropriate search text and no studies."""
        input = {'description': 'some string'}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_description_and_one_study(self):
        """Form is valid when given appropriate search text and one study."""
        study = factories.StudyFactory.create()
        input = {'description': 'some string', 'studies': [study.pk]}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_description_and_two_studies(self):
        """Form is valid when given appropriate search text and two studies."""
        studies = factories.StudyFactory.create_batch(2)
        input = {'description': 'some string', 'studies': [study.pk for study in studies]}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name(self):
        """Form is valid when given appropriate search text and a trait name."""
        input = {'description': 'text', 'name': 'abc'}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name_and_study(self):
        """Form is valid when given appropriate search text, an existing study, and a trait name."""
        study = factories.StudyFactory.create()
        input = {'description': 'text', 'studies': [study.pk], 'name': 'abc'}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_false(self):
        """Form is valid if exact_name_match checkbox is False."""
        input = {'name': 'abc', 'exact_name_match': False}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_true(self):
        """Form is valid if exact_match checkbox is True."""
        input = {'name': 'abc', 'exact_name_match': True}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())


class SourceTraitCrispySearchFormTestCase(TestCase):

    def test_form_with_valid_text_no_study(self):
        """Test that the form is valid when given valid search text, but no study."""
        input = {'text': 'some_string'}
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_text_and_one_study(self):
        """Test that the form is valid when given valid search text and one valid study."""
        studies = factories.StudyFactory.create_batch(10)
        input = {'text': 'some_string', 'study': [studies[0].pk]}
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_text_and_multiple_studies(self):
        """Test that the form is valid when given valid search text and multiple valid studies."""
        studies = factories.StudyFactory.create_batch(10)
        input = {
            'text': 'some_string',
            'study': [studies[0].pk, studies[3].pk]
        }
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_with_invalid_text_and_one_study(self):
        """Test that the form is invalid when given invalid search text and one valid study."""
        studies = factories.StudyFactory.create_batch(10)
        input = {
            'text': '',
            'study': [studies[0].pk, studies[3].pk]
        }
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_with_valid_text_and_invalid_study(self):
        """Test that the form is invalid when given valid search text and an invalid study id."""
        input = {'text': 'some_string', 'study': [23]}
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_is_not_valid_with_invalid_text(self):
        """Test that the form is invalid when given an empty search string."""
        input = {'text': ''}
        form = forms.SourceTraitCrispySearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_with_no_input_data(self):
        """Test that the form is not bound when it's not given input data."""
        form = forms.SourceTraitCrispySearchForm()
        self.assertFalse(form.is_bound)

    def test_form_has_error_with_invalid_search_text(self):
        """Test that the form has an error on the text field when given an empty search string."""
        input = {'text': ''}
        form = forms.SourceTraitCrispySearchForm(input)
        form.is_valid()
        self.assertTrue(form.has_error('text'))

    def test_form_has_error_with_invalid_study(self):
        """Test that the form has an error on the study field when given an invalid study name."""
        traits = factories.SourceTraitFactory.create_batch(5)
        studies = models.Study.objects.all()
        study_ids = [st.pk for st in studies]
        # Get the first study id from 1-100 that is not in the valid studies
        bad_study_id = [n for n in range(1, 101) if n not in study_ids][0]
        input = {'text': traits[0].i_trait_name, 'study': [bad_study_id]}
        form = forms.SourceTraitCrispySearchForm(input)
        form.is_valid()
        self.assertTrue(form.has_error('study'))

    def test_form_has_accurate_set_of_studies(self):
        """Test that the choices for the form match the valid set of studies available at search time."""
        studies = factories.StudyFactory.create_batch(5)
        input = {'text': 'some_string'}
        form = forms.SourceTraitCrispySearchForm(input)
        current_studies = [[st.pk, st.i_study_name] for st in models.Study.objects.all().order_by('i_study_name')]
        self.assertEqual(current_studies, form.STUDIES)
