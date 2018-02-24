"""Form classes for the trait_browser app."""

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions, InlineCheckboxes
from dal import autocomplete

from . import models


class SourceTraitSearchForm(forms.Form):
    """Form to handle django-watson searches for SourceTrait objects.

    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """

    name = forms.CharField(
        label='variable name',
        max_length=100,
        required=False,
        help_text='Search for exact source variable names.')
    q = forms.CharField(
        label='search text',
        max_length=100,
        required=False,
        help_text='Search within source variable descriptions.'
    )
    studies = forms.ModelMultipleChoiceField(
        queryset=models.Study.objects.all(),
        required=False,
        label='Studies',
        widget=autocomplete.ModelSelect2Multiple(
            url='trait_browser:source:studies:autocomplete:by-name'),
        help_text='Search within these studies.'
    )

    def __init__(self, *args, **kwargs):
        super(SourceTraitSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'get'
        # Add a submit button.
        self.helper.layout.append(
            FormActions(
                Submit('submit', 'Search', css_class='btn-primary btn-disable'),
            )
        )

    def clean(self):
        cleaned_data = super(SourceTraitSearchForm, self).clean()
        if not cleaned_data['name'] and not cleaned_data['q']:
            raise forms.ValidationError(
                'At least one field must be filled in.'
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
