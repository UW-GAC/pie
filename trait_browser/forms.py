"""Form classes for the trait_browser app."""

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div
from crispy_forms.bootstrap import FormActions
from dal import autocomplete

from . import models


ERROR_ONLY_SHORT_WORDS = 'Only short words entered.'

class WatsonSearchField(forms.CharField):

    def clean(self, value):
        """Custom cleaning for fields to be passed to watson search calls.

        This method checks that checks that at least one long word was passed,
        if anything was passed. It then removes any short words from the query.
        """
        data = super(WatsonSearchField, self).clean(value)
        words = data.split()
        short_words = [word for word in words if len(word) < 3]
        long_words = [word for word in words if word not in short_words]
        if len(words) > 0 and len(long_words) == 0:
            raise forms.ValidationError(ERROR_ONLY_SHORT_WORDS)
        return ' '.join(long_words)


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
    description = WatsonSearchField(
        label='Variable description',
        max_length=100,
        required=False,
        help_text='Search dbGaP phenotype variable descriptions. Words less than three letters are ignored.'#,
        #validators=[validate_watson_search_field]
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
        select the intended study. More than one study may be selected."""
    )

    def __init__(self, *args, **kwargs):
        super(SourceTraitSearchMultipleStudiesForm, self).__init__(*args, **kwargs)
        # Add the studies field to the form.
        self.helper.layout[0].append('studies')


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
    description = WatsonSearchField(
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
        # If one of the fields failed its validation/cleaning, it will not be in cleaned data.
        name = self.cleaned_data.get('name')
        description = self.cleaned_data.get('description')
        if name is not None and description is not None:
            if not name and not description:
                raise forms.ValidationError('Either variable name or description must be filled in.')
