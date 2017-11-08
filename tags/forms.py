"""Form classes for the tags app."""

from django import forms

from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Div, Layout, Fieldset, HTML, Submit
from dal import autocomplete

from . import models
from trait_browser.models import SourceTrait


def generate_button_html(name, value, btn_type="submit", css_class="btn-primary"):
    """Make html for a submit button."""
    params = {'name': name,
              'value': value,
              'btn_type': btn_type,
              'css_class': css_class}
    html = "<input type='%(btn_type)s' name='%(name)s', value='%(value)s', class='btn %(css_class)s', id='button-id-%(name)s'/>"  # noqa: E501
    button_html = HTML(html % params)
    return button_html


class TaggedTraitForm(forms.ModelForm):
    """Form for creating TaggedTrait objects."""

    trait = forms.ModelChoiceField(queryset=SourceTrait.objects.all(),
                                   required=True,
                                   widget=autocomplete.ModelSelect2(url='trait_browser:source:autocomplete'))
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    class Meta:
        model = models.TaggedTrait
        fields = ('tag', 'trait', 'recommended', )
        help_texts = {'trait': 'Select a phenotype.',
                      'recommended': 'Is this the phenotype you recommend to use for harmonizing the tag concept?',
                      }

    def __init__(self, *args, **kwargs):
        super(TaggedTraitForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


class TaggedTraitMultipleForm(forms.Form):
    """Form for creating TaggedTrait objects."""

    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
        help_text='Select one or more phenotypes.')
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(TaggedTraitMultipleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


class TaggedTraitMultipleFromTagForm(forms.Form):
    """Form for creating TaggedTrait objects from a specific Tag object."""

    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
        help_text='Select one or more phenotypes.')
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(TaggedTraitMultipleFromTagForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


class TagSpecificTraitForm(forms.Form):
    """Form for creating TaggedTrait objects from a specific SourceTrait object."""

    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(TagSpecificTraitForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)
