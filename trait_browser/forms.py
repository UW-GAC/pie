"""Form classes for the trait_browser app."""

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div
from crispy_forms.bootstrap import FormActions, InlineCheckboxes
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
        help_text='Search dbGaP phenotype variable names.')
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
    studies = forms.ModelMultipleChoiceField(
        queryset=models.Study.objects.all(),
        required=False,
        label='Study/Studies',
        widget=autocomplete.ModelSelect2Multiple(
            url='trait_browser:source:studies:autocomplete:by-name'),
        help_text="""Search only in selected studies. Start typing the dbGaP study name to filter the list, then
        select the intended study. More than one study may be selected."""
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
        cleaned_data = super(SourceTraitSearchForm, self).clean()
        if not cleaned_data['name'] and not cleaned_data['description']:
            raise forms.ValidationError(
                'Either variable name or description must be filled in.'
            )


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
            raise forms.ValidationError(
                'Either variable name or description must be filled in.'
            )


class SourceTraitCrispySearchForm(forms.Form):
    """Form to handle searching within SourceTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    text = forms.CharField(
        label='search text', max_length=100,
        help_text='Case insensitive. Searches within both phenotype names and descriptions.'
    )
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.form_method = 'get'
    helper.layout = Layout(
        Field('text'),
        InlineCheckboxes('study'),
        FormActions(
            Submit('submit', 'Search', css_class='btn-primary btn-disable'),
        )
    )

    # Override the init method, to allow dynamic setting of the choices for the
    # study field, which enables proper testing.
    def __init__(self, *args, **kwargs):
        super(SourceTraitCrispySearchForm, self).__init__(*args, **kwargs)
        self.STUDIES = [[x.pk, x.i_study_name] for x in models.Study.objects.all().order_by('i_study_name')]
        self.fields['study'] = forms.MultipleChoiceField(
            choices=self.STUDIES, widget=forms.CheckboxSelectMultiple(), required=False,
            help_text='If no studies are selected, source phenotypes from all studies will be searched.'
        )


class HarmonizedTraitCrispySearchForm(forms.Form):
    """Form to handle searching within HarmonizedTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    text = forms.CharField(
        label='search text', max_length=100,
        help_text='Case insensitive. Searches within both phenotype names and descriptions.'
    )
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.form_method = 'get'
    helper.layout = Layout(
        Field('text'),
        FormActions(
            Submit('submit', 'Search', css_class='btn-primary btn-disable'),
        )
    )
