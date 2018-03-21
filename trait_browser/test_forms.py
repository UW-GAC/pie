"""Test the functions and classes from forms.py."""

from django.test import TestCase

from . import factories
from . import forms
from . import models


class SourceTraitSearchFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceTraitSearchForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_invalid_with_blank_name_and_description(self):
        """Form is invalid if both name and description are blank."""
        study = factories.StudyFactory.create()
        input = {'description': '', 'name': '', 'studies': [study.pk]}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name(self):
        """Form is valid when given appropriate search text and a trait name."""
        input = {'description': 'text', 'name': 'abc'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_false(self):
        """Form is valid if exact_name_match checkbox is False."""
        input = {'name': 'abc', 'exact_name_match': False}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_true(self):
        """Form is valid if exact_match checkbox is True."""
        input = {'name': 'abc', 'exact_name_match': True}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())


class SourceTraitSearchMultipleStudiesFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceTraitSearchMultipleStudiesForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_invalid_with_blank_name_and_description(self):
        """Form is invalid if both name and description are blank."""
        study = factories.StudyFactory.create()
        input = {'description': '', 'name': '', 'studies': [study.pk]}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())

    def test_form_with_valid_description_and_no_studies(self):
        """Form is valid when given appropriate search text and no studies."""
        input = {'description': 'some string'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_description_and_one_study(self):
        """Form is valid when given appropriate search text and one study."""
        study = factories.StudyFactory.create()
        input = {'description': 'some string', 'studies': [study.pk]}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_with_valid_description_and_two_studies(self):
        """Form is valid when given appropriate search text and two studies."""
        studies = factories.StudyFactory.create_batch(2)
        input = {'description': 'some string', 'studies': [study.pk for study in studies]}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name(self):
        """Form is valid when given appropriate search text and a trait name."""
        input = {'description': 'text', 'name': 'abc'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name_and_study(self):
        """Form is valid when given appropriate search text, an existing study, and a trait name."""
        study = factories.StudyFactory.create()
        input = {'description': 'text', 'studies': [study.pk], 'name': 'abc'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_false(self):
        """Form is valid if exact_name_match checkbox is False."""
        input = {'name': 'abc', 'exact_name_match': False}
        form = forms.SourceTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_true(self):
        """Form is valid if exact_match checkbox is True."""
        input = {'name': 'abc', 'exact_name_match': True}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())


class SourceTraitSearchOneStudyFormTest(TestCase):

    def setUp(self):
        self.study = factories.StudyFactory.create()
        self.search_form = forms.SourceTraitSearchOneStudyForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form(self.study)
        self.assertFalse(form.is_bound)

    def test_form_is_invalid_with_blank_name_and_description(self):
        """Form is invalid if both name and description are blank."""
        study = factories.StudyFactory.create()
        input = {'description': '', 'name': ''}
        form = self.search_form(self.study, input)
        self.assertFalse(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name(self):
        """Form is valid when given appropriate search text and a trait name."""
        input = {'description': 'text', 'name': 'abc'}
        form = self.search_form(self.study, input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_false(self):
        """Form is valid if exact_name_match checkbox is False."""
        input = {'name': 'abc', 'exact_name_match': False}
        form = self.search_form(self.study, input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_true(self):
        """Form is valid if exact_match checkbox is True."""
        input = {'name': 'abc', 'exact_name_match': True}
        form = self.search_form(self.study, input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_one_dataset_selected(self):
        dataset = factories.SourceDatasetFactory.create(source_study_version__study=self.study)
        input = {'name': 'abc', 'exact_name_match': True, 'datasets': [dataset.pk]}
        form = self.search_form(self.study, input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_two_datasets_selected(self):
        dataset_1 = factories.SourceDatasetFactory.create(source_study_version__study=self.study)
        dataset_2 = factories.SourceDatasetFactory.create(source_study_version__study=self.study)
        input = {'name': 'abc', 'exact_name_match': True, 'datasets': [dataset_1.pk, dataset_2.pk]}
        form = self.search_form(self.study, input)
        self.assertTrue(form.is_valid())

    def test_form_is_invalid_with_dataset_from_a_different_study(self):
        other_study = factories.StudyFactory.create()
        dataset = factories.SourceDatasetFactory.create(source_study_version__study=other_study)
        input = {'name': 'abc', 'exact_name_match': True, 'datasets': [dataset.pk]}
        form = self.search_form(self.study, input)
        self.assertFalse(form.is_valid())
        self.assertIn('datasets', form.errors)
        self.assertIn(self.search_form.ERROR_DIFFERENT_STUDY, form.errors['datasets'])

    def test_form_is_invalid_with_a_deprecated_dataset_from_same_study(self):
        study_version = factories.SourceStudyVersionFactory.create(study=self.study, i_is_deprecated=True)
        dataset = factories.SourceDatasetFactory.create(source_study_version=study_version)
        input = {'name': 'abc', 'exact_name_match': True, 'datasets': [dataset.pk]}
        form = self.search_form(self.study, input)
        self.assertFalse(form.is_valid())
        self.assertIn('datasets', form.errors)
        self.assertIn(self.search_form.ERROR_DEPRECATED_DATASET, form.errors['datasets'])


class HarmonizedTraitSearchFormTest(TestCase):

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = forms.HarmonizedTraitSearchForm()
        self.assertFalse(form.is_bound)

    def test_form_is_invalid_with_blank_name_and_description(self):
        """Form is invalid if both name and description are blank."""
        input = {'description': '', 'name': ''}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertFalse(form.is_valid())

    def test_form_with_valid_description_and_no_studies(self):
        """Form is valid when given appropriate search text and no studies."""
        input = {'description': 'some string'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_valid_description_and_trait_name(self):
        """Form is valid when given appropriate search text and a trait name."""
        input = {'description': 'text', 'name': 'abc'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_false(self):
        """Form is valid if exact_name_match checkbox is False."""
        input = {'name': 'abc', 'exact_name_match': False}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_exact_name_match_checkbox_true(self):
        """Form is valid if exact_match checkbox is True."""
        input = {'name': 'abc', 'exact_name_match': True}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
