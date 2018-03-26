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

    def test_form_invalid_with_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field."""
        input = {'description': 'of'}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS],
        })

    def test_form_valid_with_name_and_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field even if name is present."""
        input = {'description': 'of', 'name': 'bmi'}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS]
        })

    def test_short_words_removed_from_description(self):
        """Short words are removed from the description field."""
        input = {'description': 'number of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number')

    def test_short_words_removed_from_description_when_separated_by_tabs(self):
        """Short words are removed from the description field."""
        input = {'description': 'number\tof\tdays'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days')

    def test_short_words_removed_from_description_when_separated_by_extra_whitespace(self):
        """Short words are removed from the description field."""
        input = {'description': 'number  of    days measured'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days measured')

    def test_updates_warning_message_field_with_one_short_word(self):
        """warning_message field is updated if one short word is removed."""
        input = {'description': 'number of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: to of')


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

    def test_form_invalid_with_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field."""
        input = {'description': 'of'}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS],
        })

    def test_form_valid_with_name_and_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field even if name is present."""
        input = {'description': 'of', 'name': 'bmi'}
        form = self.search_form(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS]
        })

    def test_short_words_removed_from_description(self):
        """Short words are removed from the description field."""
        input = {'description': 'number of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number')

    def test_short_words_removed_from_description_when_separated_by_tabs(self):
        """Short words are removed from the description field."""
        input = {'description': 'number\tof\tdays'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days')

    def test_short_words_removed_from_description_when_separated_by_extra_whitespace(self):
        """Short words are removed from the description field."""
        input = {'description': 'number  of    days measured'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days measured')

    def test_updates_warning_message_field_with_one_short_word(self):
        """warning_message field is updated if one short word is removed."""
        input = {'description': 'number of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: to of')


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

    def test_form_invalid_with_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field."""
        input = {'description': 'of'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS],
        })

    def test_form_valid_with_name_and_only_short_words_in_description(self):
        """Form is invalid when only short words are entered in the description field even if name is present."""
        input = {'description': 'of', 'name': 'bmi'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'description': [forms.ERROR_ONLY_SHORT_WORDS]
        })

    def test_short_words_removed_from_description(self):
        """Short words are removed from the description field."""
        input = {'description': 'number of'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number')

    def test_three_letter_words_not_removed_from_description(self):
        """Short words are removed from the description field."""
        input = {'description': 'bmi'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'bmi')

    def test_short_words_removed_from_description_when_separated_by_tabs(self):
        """Short words are removed from the description field."""
        input = {'description': 'number\tof\tdays'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days')

    def test_short_words_removed_from_description_when_separated_by_extra_whitespace(self):
        """Short words are removed from the description field."""
        input = {'description': 'number  of    days measured'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['description'], 'number days measured')

    def test_updates_warning_message_field_with_one_short_word(self):
        """warning_message field is updated if one short word is removed."""
        input = {'description': 'number of'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Omitted short words in Variable description field: to of')
