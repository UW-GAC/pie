"""Form classes for the trait_browser app."""

from django import forms
from django.urls import reverse

import string

from crispy_forms.bootstrap import Accordion, AccordionGroup, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, Row
from dal import autocomplete

from . import models


ERROR_ONLY_SHORT_WORDS = 'Enter at least one term with more than two letters.'
ERROR_ALLOWED_CHARACTERS = 'Include only uppercase and lowercase letters, digits, underscores, and apostrophes.'


class MultilineField(Field):
    """Superclass to allow multiple form fields on one line.

    This class is a subclass of django-crispy-form's Field class. It is not
    intended to be used directly. Instead, one of its subclasses should be used.
    """

    template = 'crispy_forms/_shared_row_fields.html'

    def __init__(self, field, input_class, *args, **kwargs):
        """Add the specified css class for the input tag to the object."""
        super(MultilineField, self).__init__(field, *args, **kwargs)
        self.input_class = input_class

    def render(self, form, form_style, context, extra_context=None, **kwargs):
        if extra_context is None:
            extra_context = {}
        extra_context['input_class'] = self.input_class
        return super(MultilineField, self).render(form, form_style, context, extra_context=extra_context, **kwargs)


class MultilineStartingField(MultilineField):
    """Class to create the first form field on a given line.

    This class adds the form-group class to the div starting a set of fields.
    It must be used before a MultilineEndingField field.
    """

    def render(self, *args, **kwargs):
        extra_context = kwargs.get('extra_context')
        if extra_context is None:
            extra_context = {}
        extra_context['add_starting_formgroup'] = True
        extra_context['add_ending_formgroup'] = False
        return super(MultilineStartingField, self).render(extra_context=extra_context, *args, **kwargs)


class MultilineEndingField(MultilineField):
    """Class to create the first form field on a given line.

    This class adds the form-group class to the div following a set of fields.
     It must be used after a MultilineStartingField field.
    """

    def render(self, *args, **kwargs):
        extra_context = kwargs.get('extra_context')
        if extra_context is None:
            extra_context = {}
        extra_context['add_starting_formgroup'] = False
        extra_context['add_ending_formgroup'] = True
        return super(MultilineEndingField, self).render(extra_context=extra_context, *args, **kwargs)


# Custom layouts for searching.
name_checkbox_layout = Layout(
    MultilineStartingField('name', 'col-sm-6'),
    MultilineEndingField('match_exact_name', 'col-sm-4')
)

dataset_name_checkbox_layout = Layout(
    MultilineStartingField('dataset_name', 'col-sm-6'),
    MultilineEndingField('dataset_match_exact_name', 'col-sm-4')
)

buttons_layout = Layout(
    FormActions(
        Submit('submit', 'Search', css_class='btn-primary btn-disable'),
        # For some reason, adding btn-disable to the css_class does not work properly. Unfortunately the tests
        # still pass; I can't figure out how to make them fail if btn-disable is included.
        Submit('reset', 'Reset', css_class='btn-info'),
    )
)


class WatsonSearchField(forms.CharField):

    ALLOWED_CHARACTERS = set(string.ascii_letters + string.digits + string.whitespace + '_' + '\'')
    warning_message = None

    def clean(self, value):
        """Custom cleaning for fields to be passed to watson search calls.

        This method checks that checks that at least one long word was passed,
        if anything was passed. It then removes any short words from the query.
        """
        data = super(WatsonSearchField, self).clean(value)
        # Check that search term is composed only of allowed characters.
        if not set(data).issubset(self.ALLOWED_CHARACTERS):
            raise forms.ValidationError(ERROR_ALLOWED_CHARACTERS)
        words = data.split()
        short_words = [word for word in words if len(word) < 3]
        long_words = [word for word in words if word not in short_words]
        if len(short_words) > 0:
            self.warning_message = 'Ignored short words in "{field}" field: {words}'.format(
                words=' '.join(short_words),
                field=self.label
            )
            # Raise an error if all words were short words.
            if len(long_words) == 0:
                raise forms.ValidationError(ERROR_ONLY_SHORT_WORDS)
        return ' '.join(long_words)


class SourceDatasetSearchForm(forms.Form):
    """Form to handle django-watson searches for SourceDataset objects."""

    name = forms.CharField(
        label='Dataset name',
        max_length=100,
        required=False,
        help_text="Search dataset names."
    )
    match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    description = WatsonSearchField(
        label='Dataset description',
        max_length=100,
        required=False,
        help_text=('Search dataset descriptions. Words less than three letters are ignored. Only alphanumeric '
                   'characters, apostrophes, and underscores are allowed.')
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with formatting and submit button."""
        super(SourceDatasetSearchForm, self).__init__(*args, **kwargs)
        # Specify how form should be displayed.
        self.helper = FormHelper(self)
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-10'
        self.helper.layout = Layout(
            Row(
                Div(
                    name_checkbox_layout,
                    'description',
                    buttons_layout,
                    css_class='col-sm-10 col-sm-offset-1'
                )
            )
        )

    def clean(self):
        """Perform additional multi-field cleaning to make sure that either description or name is entered."""
        super(SourceDatasetSearchForm, self).clean()
        # If one of the fields failed its validation/cleaning, it will not be in cleaned data.
        name = self.cleaned_data.get('name')
        description = self.cleaned_data.get('description')
        if name is not None and description is not None:
            if not name and not description:
                raise forms.ValidationError('Either dataset name or description must be filled in.')


class SourceDatasetSearchMultipleStudiesForm(SourceDatasetSearchForm):
    """Form to handle django-watson searches for SourceDataset objects within a specific study."""

    studies = forms.ModelMultipleChoiceField(
        queryset=models.Study.objects.all(),
        required=False,
        label='Study/Studies',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:studies:autocomplete:by-name-or-phs'),
        help_text=('Search only in selected studies. Start typing the dbGaP study accession or name to filter the '
                   'list (example: Framingham, phs7, phs000007, 7), then select the intended study. More than one '
                   'study may be selected.')
    )

    def __init__(self, *args, **kwargs):
        """Initialize form instance by adding study and dataset propery fields to the layout."""
        super(SourceDatasetSearchMultipleStudiesForm, self).__init__(*args, **kwargs)
        # Add the additional field to the form.
        self.helper.layout = Layout(
            Row(
                Div(
                    name_checkbox_layout,
                    'description',
                    'studies',
                    buttons_layout,
                    css_class='col-sm-10 col-sm-offset-1'
                )
            )
        )


class SourceTraitSearchForm(forms.Form):
    """Form to handle django-watson searches for SourceTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    name = forms.CharField(
        label='Variable name',
        max_length=100,
        required=False,
        help_text='Search variable names.'
    )
    match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    description = WatsonSearchField(
        label='Variable description',
        max_length=100,
        required=False,
        help_text=('Search within variable descriptions. Words less than three letters are ignored. Only alphanumeric '
                   'characters, apostrophes, and underscores are allowed.')
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with formatting and submit button."""
        super(SourceTraitSearchForm, self).__init__(*args, **kwargs)
        # Specify how form should be displayed.
        self.helper = FormHelper(self)
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-10'
        self.helper.layout = Layout(
            Row(
                Div(
                    name_checkbox_layout,
                    'description',
                    buttons_layout,
                    css_class='col-sm-10 col-sm-offset-1'
                )
            )
        )

    def clean(self):
        """Perform additional multi-field cleaning to make sure that either description or name is entered."""
        super(SourceTraitSearchForm, self).clean()
        # If one of the fields failed its validation/cleaning, it will not be in cleaned data.
        name = self.cleaned_data.get('name')
        description = self.cleaned_data.get('description')
        if name is not None and description is not None:
            if not name and not description:
                raise forms.ValidationError('Either variable name or description must be filled in.')


class SourceTraitSearchMultipleStudiesForm(SourceTraitSearchForm):
    """Form to handle django-watson searches for SourceTrait objects within a specific study."""

    studies = forms.ModelMultipleChoiceField(
        queryset=models.Study.objects.all(),
        required=False,
        label='Study/Studies',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:studies:autocomplete:by-name-or-phs'),
        help_text=('Search only in selected studies. Start typing the dbGaP study accession or name to filter the '
                   'list (example: Framingham, phs7, phs000007, 7), then select the intended study. More than one '
                   'study may be selected.')
    )
    dataset_name = forms.CharField(
        label='Dataset name',
        max_length=100,
        required=False,
        help_text='Search only within study datasets matching this name.'
    )
    dataset_match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    dataset_description = WatsonSearchField(
        label='Dataset description',
        max_length=100,
        required=False,
        help_text='Search only within study datasets matching this description.'
    )

    def __init__(self, *args, **kwargs):
        """Initialize form instance by adding study and dataset propery fields to the layout."""
        super(SourceTraitSearchMultipleStudiesForm, self).__init__(*args, **kwargs)

        # Set the status of the collapsible panel depending on which data have been passed to form.
        panel_active = False
        if self.is_bound and self.data:
            if self.data.get('dataset_description') or self.data.get('dataset_name') or self.data.get('studies'):
                panel_active = True

        # Add the additional field to the form.
        self.helper.layout = Layout(
            Row(
                Div(
                    name_checkbox_layout,
                    'description',
                    Accordion(
                        AccordionGroup(
                            'Additional filtering by study and dataset',
                            dataset_name_checkbox_layout,
                            'dataset_description',
                            'studies',
                            active=panel_active
                        )
                    ),
                    buttons_layout,
                    css_class='col-sm-10 col-sm-offset-1'
                )
            )
        )


class SourceTraitSearchOneStudyForm(SourceTraitSearchForm):

    ERROR_DEPRECATED_DATASET = 'Datasets must be from the most recent study version.'
    ERROR_DIFFERENT_STUDY = 'Datasets must be from this study.'

    def __init__(self, study, *args, **kwargs):
        """Initialize form instance.

        Add a datasets field to the superclass layout.
        """
        self.study = study
        super(SourceTraitSearchOneStudyForm, self).__init__(*args, **kwargs)
        # Add an autocomplete field for datasets belonging to this study.
        self.fields['datasets'] = forms.ModelMultipleChoiceField(
            # Use .all() instead of .current() to get an appropriate error message from the clean message.
            queryset=models.SourceDataset.objects.all(),
            required=False,
            label='Dataset(s)',
            widget=autocomplete.ModelSelect2Multiple(
                url=reverse(
                    'trait_browser:source:studies:pk:datasets:autocomplete:by-name-or-pht',
                    args=[study.pk]
                )
            ),
            help_text="""Search only in selected datasets. Start by typing the dbGaP dataset accession (pht) or
                         dataset name to filter the list (example: 'pht1234', '1234', '01234', or 'ex0_7s'). More
                         than one dataset may be selected."""
        )
        self.helper.layout = Layout(
            Row(
                Div(
                    name_checkbox_layout,
                    'description',
                    'datasets',
                    buttons_layout,
                    css_class='col-sm-10 col-sm-offset-1'
                )
            )
        )

    def clean_datasets(self):
        data = self.cleaned_data['datasets']
        for dataset in data:
            if dataset.source_study_version.study != self.study:
                raise forms.ValidationError(self.ERROR_DIFFERENT_STUDY)
            if dataset.source_study_version.i_is_deprecated:
                raise forms.ValidationError(self.ERROR_DEPRECATED_DATASET)
        return data


class SourceObjectLookupForm(forms.Form):

    types = (
        ('study', 'Study'),
        ('dataset', 'Dataset'),
        ('trait', 'Variable'),
    )
    object_type = forms.ChoiceField(
        choices=types,
        label='dbGaP object type',
        help_text='Select what type of dbGaP accessioned object to find.'
    )

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-6'
    helper.layout = Layout(
        'object_type',
        FormActions(
            Submit('submit', 'Next', css_class='btn-primary btn-disable')
        )
    )


lookup_form_helper = FormHelper()
lookup_form_helper.form_class = 'form_horizontal'
lookup_form_helper.label_class = 'col-sm-1'
lookup_form_helper.field_class = 'col-sm-11'
lookup_form_helper.layout = Layout(
    Div(
        'object',
        FormActions(
            Submit('submit', 'Submit', css_class='btn-primary btn-disable')
        ),
        css_class='col-sm-10 col-sm-offset-1'
    )
)


class StudyLookupForm(forms.Form):

    object = forms.ModelChoiceField(
        queryset=models.Study.objects.all(),
        required=True,
        label='Study',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:studies:autocomplete:by-name-or-phs'),
        help_text=('Select the study to find. Start typing the dbGaP study name or accession to filter the '
                   'list (example: Framingham, phs7, phs000007, 7), then select the intended study.')
    )
    helper = lookup_form_helper


class SourceDatasetLookupForm(forms.Form):

    object = forms.ModelChoiceField(
        queryset=models.SourceDataset.objects.current(),
        required=True,
        label='Dataset',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:datasets:autocomplete:by-name-or-pht'),
        help_text=('Select the dataset to find. Start typing the dbGaP dataset name or accession to filter the '
                   'list (example: ex0_7s, pht9, pht000009, 000009, 9), then select the intended dataset. '
                   'Note that dataset names may not be unique.')
    )
    helper = lookup_form_helper


class SourceTraitLookupForm(forms.Form):

    object = forms.ModelChoiceField(
        queryset=models.SourceTrait.objects.current(),
        required=True,
        label='Variable',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:traits:autocomplete:by-name-or-phv'),
        help_text=('Select the variable to find. Start typing the dbGaP variable name or accession to filter the '
                   'list (example: MF33, phv507, phv00000507, 00000507, 507), then select the intended variable. '
                   'Note that variable names may not be unique.')
    )
    helper = lookup_form_helper


class HarmonizedTraitSearchForm(forms.Form):
    """Form to handle django-watson searches for HarmonizedTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    name = forms.CharField(
        label='Variable name',
        max_length=100,
        required=False,
        help_text='Search variable names.')
    match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    description = WatsonSearchField(
        label='Variable description',
        max_length=100,
        required=False,
        help_text=('Search within variable descriptions. Words less than three letters are ignored. Only alphanumeric '
                   'characters, apostrophes, and underscores are allowed.')
    )
    # Specify how form should be displayed.
    helper = FormHelper()
    helper.form_method = 'get'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.layout = Layout(
        Row(
            Div(
                name_checkbox_layout,
                'description',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
            )
        )
    )

    def clean(self):
        """Perform additional multi-field cleaning to make sure that either description or name is entered."""
        cleaned_data = super(HarmonizedTraitSearchForm, self).clean()
        # If one of the fields failed its validation/cleaning, it will not be in cleaned data.
        name = self.cleaned_data.get('name')
        description = self.cleaned_data.get('description')
        if name is not None and description is not None:
            if not name and not description:
                raise forms.ValidationError('Either variable name or description must be filled in.')
