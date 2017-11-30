"""Form classes for the tags app."""

from django import forms
from django.utils.safestring import mark_safe

from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Div, Layout, Fieldset, HTML, Submit
from dal import autocomplete

from . import models
from profiles.models import UserData
from trait_browser.models import SourceTrait, Study


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
    """Form for creating a single TaggedTrait object."""

    title = 'Tag a phenotype'
    subtitle = 'Label a phenotype with the selected tag'
    trait = forms.ModelChoiceField(queryset=SourceTrait.objects.all(),
                                   required=True,
                                   label='Phenotype',
                                   widget=autocomplete.ModelSelect2(url='trait_browser:source:taggable-autocomplete'))
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
        """Override __init__ to make the form study-specific."""
        # Get the user and remove it from kwargs (b/c/ of UserFormKwargsMixin on the view.)
        self.user = kwargs.pop('user')
        # Call super here to set up all of the fields.
        super(TaggedTraitForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        studies = list(UserData.objects.get(user=self.user).taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can tag phenotypes from the study {} ({})'.format(studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can tag phenotypes from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['trait'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        # Form formatting and add a submit button.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


class TaggedTraitByTagForm(forms.Form):
    """Form for creating a single TaggedTrait object with a specific tag."""

    title = 'Tag a phenotype'
    subtitle = 'Label a phenotype'
    trait = forms.ModelChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        label='Phenotype',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:taggable-autocomplete'),
        help_text='Select one or more phenotypes.')
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        # Get the user and remove it from kwargs (b/c/ of UserFormKwargsMixin on the view.)
        self.user = kwargs.pop('user')
        # Call super here to set up all of the fields.
        super(TaggedTraitByTagForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        studies = list(UserData.objects.get(user=self.user).taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can tag phenotypes from the study {} ({})'.format(studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can tag phenotypes from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['trait'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        # Form formatting and add a submit button.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


class ManyTaggedTraitsForm(forms.Form):
    """Form for creating many TaggedTrait objects."""

    title = 'Tag phenotypes'
    subtitle = 'Label phenotypes with the selected tag'
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=False,
        label='Phenotype(s)',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:taggable-autocomplete'),
        help_text='Select one or more phenotypes.')
    recommended_traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=False,
        label='Recommended phenotype(s)',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:taggable-autocomplete'),
        help_text='Select one or more phenotypes.')

    def __init__(self, *args, **kwargs):
        # Get the user and remove it from kwargs (b/c/ of UserFormKwargsMixin on the view.)
        self.user = kwargs.pop('user')
        # Call super here to set up all of the fields.
        super(ManyTaggedTraitsForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        studies = list(UserData.objects.get(user=self.user).taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can tag phenotypes from the study {} ({})'.format(studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can tag phenotypes from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['traits'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        self.fields['recommended_traits'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        # Form formatting and add a submit button.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)

    def clean(self):
        """Custom cleaning to check that at least one trait is selected."""
        cleaned_data = super(ManyTaggedTraitsForm, self).clean()
        traits = cleaned_data.get('traits', [])
        recommended_traits = cleaned_data.get('recommended_traits', [])
        if len(traits) == 0 and len(recommended_traits) == 0:
            traits_error = forms.ValidationError(
                u"""You must specify at least one phenotype in the 'phenotypes' or 'recommended phenotypes' field."""
            )
            self.add_error('traits', traits_error)
            self.add_error('recommended_traits', traits_error)
        return cleaned_data


class ManyTaggedTraitsByTagForm(forms.Form):
    """Form for creating many TaggedTrait objects for a specific tag."""

    title = 'Tag phenotypes'
    subtitle = 'Label phenotypes'
    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=False,
        label='Phenotype(s)',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:taggable-autocomplete'),
        help_text='Select one or more phenotypes.')
    recommended_traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=False,
        label='Recommended phenotype(s)',
        widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:taggable-autocomplete'),
        help_text='Select one or more phenotypes.')

    def __init__(self, *args, **kwargs):
        # Get the user and remove it from kwargs (b/c/ of UserFormKwargsMixin on the view.)
        self.user = kwargs.pop('user')
        # Call super here to set up all of the fields.
        super(ManyTaggedTraitsByTagForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        studies = list(UserData.objects.get(user=self.user).taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can tag phenotypes from the study {} ({})'.format(studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can tag phenotypes from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['traits'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        self.fields['recommended_traits'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        # Form formatting and add a submit button.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)

    def clean(self):
        """Custom cleaning to check that at least one trait is selected."""
        cleaned_data = super(ManyTaggedTraitsByTagForm, self).clean()
        traits = cleaned_data.get('traits', [])
        recommended_traits = cleaned_data.get('recommended_traits', [])
        if len(traits) == 0 and len(recommended_traits) == 0:
            traits_error = forms.ValidationError(
                u"""You must specify at least one phenotype in the 'phenotypes' or 'recommended phenotypes' field."""
            )
            self.add_error('traits', traits_error)
            self.add_error('recommended_traits', traits_error)
        return cleaned_data


class TagSpecificTraitForm(forms.Form):
    """Form for creating TaggedTrait objects from a specific SourceTrait object."""

    title = 'Tag the phenotype'
    subtitle = 'Select a tag to label the phenotype'
    subtitle2 = ''
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
    # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
    # Submitting an empty value for this field sets the field to False.
    recommended = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(TagSpecificTraitForm, self).__init__(*args, **kwargs)
        # Form formatting and add a submit button.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)
