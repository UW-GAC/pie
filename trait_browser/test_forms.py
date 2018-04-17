"""Test the functions and classes from forms.py."""

from django.test import TestCase

from . import factories
from . import forms
from . import models


class SourceDatasetSearchFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceDatasetSearchForm

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
                         'Ignored short words in "Dataset description" field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Ignored short words in "Dataset description" field: to of')

    def test_error_if_special_characters_are_passed(self):
        """Fails with description search terms that include special characters."""
        characters = ['%', '#', '<', '>', '=', '?', '-']
        for character in characters:
            description = "special{char}character".format(char=character)
            input = {'description': description}
            form = self.search_form(input)
            self.assertFalse(form.is_valid(), msg='valid for term with {char}'.format(char=character))
            self.assertEqual(form.errors, {'description': [forms.ERROR_ALLOWED_CHARACTERS]},
                             msg='incorrect error for term with {char}'.format(char=character))


class SourceDatasetSearchMultipleStudiesFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceDatasetSearchMultipleStudiesForm

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
                         'Ignored short words in "Dataset description" field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Ignored short words in "Dataset description" field: to of')


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
                         'Ignored short words in "Variable description" field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Ignored short words in "Variable description" field: to of')


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
                         'Ignored short words in "Variable description" field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Ignored short words in "Variable description" field: to of')

    def test_form_is_valid_with_dataset_name(self):
        """Form is valid if dataset_name is passed."""
        input = {'name': 'abc', 'dataset_name': 'foo'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_dataset_name_and_match_exact_name(self):
        """Form is valid if dataset_name is passed and match_exact_name is True."""
        input = {'name': 'abc', 'dataset_name': 'foo', 'dataset_match_exact_name': True}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_dataset_description(self):
        """Form is valid if dataset_description is passed."""
        input = {'name': 'abc', 'dataset_description': 'foo'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_dataset_name_and_description(self):
        """Form is valid if dataset_name and description are passed."""
        input = {'name': 'abc', 'dataset_name': 'foo', 'dataset_description': 'bar'}
        form = self.search_form(input)
        self.assertTrue(form.is_valid())

    def test_form_is_valid_with_dataset_name_match_exact_name_and_description(self):
        """Form is valid if dataset_name, dataset_match_exact_name, and description are passed."""
        input = {
            'name': 'abc',
            'dataset_name': 'foo',
            'dataset_description': 'bar',
            'dataest_match_exact_name': True
        }
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


class SourceAccessionLookupSelectFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceAccessionLookupSelectForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_valid_with_choices(self):
        """Form is valid with all allowed choices."""
        for choice in ('study', 'dataset', 'trait'):
            form = self.search_form({'object_type': choice})
            self.assertTrue(form.is_valid(), msg='form not valid for choice {}'.format(choice))

    def test_form_is_invalid_with_invalid_choice(self):
        """Form is invalid with a choice that's not allowed."""
        form = self.search_form({'object_type': 'invalid'})
        self.assertFalse(form.is_valid())


class SourceAccessionLookupStudyFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceAccessionLookupStudyForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_valid_with_existing_study(self):
        """Form is valid with an existing study."""
        study = factories.StudyFactory.create()
        form = self.search_form({'object': study.pk})
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_missing_study(self):
        """Form is invalid if no study is given."""
        form = self.search_form({'object': ''})
        self.assertFalse(form.is_valid())


class SourceAccessionLookupDatasetFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceAccessionLookupDatasetForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_valid_with_existing_dataset(self):
        """Form is valid with an existing dataset."""
        dataset = factories.SourceDatasetFactory.create()
        form = self.search_form({'object': dataset.pk})
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_missing_dataset(self):
        """Form is invalid if no dataset is given."""
        form = self.search_form({'object': ''})
        self.assertFalse(form.is_valid())


class SourceAccessionLookupTraitFormTest(TestCase):

    def setUp(self):
        self.search_form = forms.SourceAccessionLookupTraitForm

    def test_form_with_no_input_data(self):
        """Form is not bound when it's not given input data."""
        form = self.search_form()
        self.assertFalse(form.is_bound)

    def test_form_is_valid_with_existing_trait(self):
        """Form is valid with an existing source trait."""
        trait = factories.SourceTraitFactory.create()
        form = self.search_form({'object': trait.pk})
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_missing_trait(self):
        """Form is invalid if no trait is given."""
        form = self.search_form({'object': ''})
        self.assertFalse(form.is_valid())


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
                         'Ignored short words in "Variable description" field: of')

    def test_updates_warning_message_field_with_two_short_words(self):
        """warning_message field is updated if two short words are removed."""
        input = {'description': 'number to of'}
        form = forms.HarmonizedTraitSearchForm(input)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['description'].warning_message,
                         'Ignored short words in "Variable description" field: to of')
