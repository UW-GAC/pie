"""Form classes for the trait_browser app."""

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div
from crispy_forms.bootstrap import FormActions
from dal import autocomplete

from . import models


ERROR_ONLY_SHORT_WORDS = 'Enter at least one term with more than two letters.'

# Custom layouts for searching.
name_checkbox_layout = Layout(
    Div(
        Div(
            'name',
            'match_exact_name',
            css_class='panel-body',
        ),
        css_class='panel panel-default'
    )
)

dataset_name_checkbox_layout = Layout(
    Div(
        Div(
            'dataset_name',
            'dataset_match_exact_name',
            css_class='panel-body',
        ),
        css_class='panel panel-default'
    )
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

    warning_message = None

    def clean(self, value):
        """Custom cleaning for fields to be passed to watson search calls.

        This method checks that checks that at least one long word was passed,
        if anything was passed. It then removes any short words from the query.
        """
        data = super(WatsonSearchField, self).clean(value)
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
        help_text='Search dataset descriptions. Words less than three letters are ignored.'
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
            Div(
                name_checkbox_layout,
                'description',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
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
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:studies:autocomplete:by-name'),
        help_text="""Search only in selected studies. Start typing the dbGaP study name to filter the list, then
                     select the intended study. More than one study may be selected.
                     """
    )

    def __init__(self, *args, **kwargs):
        """Initialize form instance by adding study and dataset propery fields to the layout."""
        super(SourceDatasetSearchMultipleStudiesForm, self).__init__(*args, **kwargs)
        # Add the additional field to the form.
        self.helper.Layout = Layout(
            Div(
                name_checkbox_layout,
                'description',
                'studies',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
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
        help_text='Search within variable descriptions. Words less than three letters are ignored.'
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
            Div(
                name_checkbox_layout,
                'description',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
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
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:studies:autocomplete:by-name'),
        help_text="""Search only in selected studies. Start typing the dbGaP study name to filter the list, then
                     select the intended study. More than one study may be selected.
                     """
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
        # Add the additional field to the form.
        self.helper.layout = Layout(
            Div(
                name_checkbox_layout,
                'description',
                dataset_name_checkbox_layout,
                'dataset_description',
                'studies',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
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
                    'trait_browser:source:studies:detail:datasets:autocomplete:by-name-or-pht',
                    args=[study.pk]
                )
            ),
            help_text="""Search only in selected datasets. Start by typing the dbGaP dataset accession (pht) or
                         dataset name to filter the list (example: 'pht1234', '1234', '01234', or 'ex0_7s'). More
                         than one dataset may be selected."""
        )
        self.helper.layout = Layout(
            Div(
                name_checkbox_layout,
                'description',
                'datasets',
                buttons_layout,
                css_class='col-sm-10 col-sm-offset-1'
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
        help_text='Search within variable descriptions. Words less than three letters are ignored.'
    )
    # Specify how form should be displayed.
    helper = FormHelper()
    helper.form_method = 'get'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.layout = Layout(
        Div(
            name_checkbox_layout,
            'description',
            buttons_layout,
            css_class='col-sm-10 col-sm-offset-1'
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
