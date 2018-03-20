"""Form classes for the trait_browser app."""

from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div
from crispy_forms.bootstrap import FormActions
from dal import autocomplete

from . import models


class SourceTraitSearchForm(forms.Form):
    """Form to handle django-watson searches for SourceTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    name = forms.CharField(
        label='Variable name',
        max_length=100,
        required=False,
        help_text='Search dbGaP phenotype variable names.'
    )
    match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    description = forms.CharField(
        label='Variable description',
        max_length=100,
        required=False,
        help_text='Search dbGaP phenotype variable descriptions.'
    )

    def __init__(self, *args, **kwargs):
        super(SourceTraitSearchForm, self).__init__(*args, **kwargs)
        # Specify how form should be displayed.
        self.helper = FormHelper(self)
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-10'
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        'name',
                        'match_exact_name',
                        css_class='panel-body',
                    ),
                    css_class='panel panel-default'
                ),
                'description',
                css_class='col-sm-10 col-sm-offset-1'
            )
        )
        # Add submit and reset buttons.
        self.helper.layout.append(
            FormActions(
                Submit('submit', 'Search', css_class='btn-primary btn-disable'),
                # For some reason, adding btn-disable to the css_class does not work properly. Unfortunately the tests
                # still pass; I can't figure out how to make them fail if btn-disable is included.
                Submit('reset', 'Reset', css_class='btn-info'),
            )
        )

    def clean(self):
        """Perform additional multi-field cleaning to make sure that either description or name is entered."""
        cleaned_data = super(SourceTraitSearchForm, self).clean()
        if not cleaned_data['name'] and not cleaned_data['description']:
            raise forms.ValidationError('Either variable name or description must be filled in.')


class SourceTraitSearchMultipleStudiesForm(SourceTraitSearchForm):
    """Form to handle django-watson searches for SourceTrait objects within a specific study."""

    studies = forms.ModelMultipleChoiceField(
        queryset=models.Study.objects.all(),
        required=False,
        label='Study/Studies',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:studies:autocomplete:by-name'),
        help_text="""Search only in selected studies. Start typing the dbGaP study name to filter the list, then
        select the intended study. More than one study may be selected."""
    )

    def __init__(self, *args, **kwargs):
        super(SourceTraitSearchMultipleStudiesForm, self).__init__(*args, **kwargs)
        # Add the studies field to the form.
        self.helper.layout[0].append('studies')


class SourceTraitSearchOneStudyForm(SourceTraitSearchForm):

    ERROR_DEPRECATED_DATASET = 'Datasets must be from the most recent study version.'
    ERROR_DIFFERENT_STUDY = 'Datasets must be from this study.'

    def __init__(self, study, *args, **kwargs):
        self.study = study
        super(SourceTraitSearchOneStudyForm, self).__init__(*args, **kwargs)
        # Add an autocomplete field for datasets belonging to this study.
        self.fields['datasets'] = forms.ModelMultipleChoiceField(
            # Use .all() instead of .current() to get an appropriate error message from the clean message.
            queryset=models.SourceDataset.objects.all(),
            required=False,
            label='Dataset(s)',
            widget=autocomplete.ModelSelect2Multiple(
                url=reverse('trait_browser:source:studies:detail:datasets:autocomplete:by-name-or-pht', args=[study.pk])
            ),
            help_text="""Search only in selected datasets. Start by typing the dbGaP variable accession (pht) or
                         dataset name to filter the list (example: 'pht1234', '1234', '01234', or 'ex0_7s'). More
                         than one dataset may be selected."""
        )
        self.helper.layout[0].append('datasets')

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
        help_text='Search harmonized phenotype variable names.')
    match_exact_name = forms.BooleanField(
        label='Match whole name',
        required=False,
        initial=True
    )
    description = forms.CharField(
        label='Variable description',
        max_length=100,
        required=False,
        help_text='Search harmonized phenotype variable descriptions.'
    )
    # Specify how form should be displayed.
    helper = FormHelper()
    helper.form_method = 'get'
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.layout = Layout(
        Div(
            Div(
                Div(
                    'name',
                    'match_exact_name',
                    css_class='panel-body',
                ),
                css_class='panel panel-default'
            ),
            'description',
            'studies',
            css_class='col-sm-10 col-sm-offset-1'
        )
    )
    # Add submit and reset buttons.
    helper.layout.append(
        FormActions(
            Submit('submit', 'Search', css_class='btn-primary btn-disable'),
            # For some reason, adding btn-disable to the css_class does not work properly. Unfortunately the tests
            # still pass; I can't figure out how to make them fail if btn-disable is included.
            Submit('reset', 'Reset', css_class='btn-info'),
        )
    )

    def clean(self):
        """Perform additional multi-field cleaning to make sure that either description or name is entered."""
        cleaned_data = super(HarmonizedTraitSearchForm, self).clean()
        if not cleaned_data['name'] and not cleaned_data['description']:
            raise forms.ValidationError('Either variable name or description must be filled in.')
