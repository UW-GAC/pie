"""Form classes for the tags app."""

from django import forms

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


class TaggableStudyFilteredTraitQuerysetMixin():

    def __init__(self, *args, **kwargs):
        """Override __init__ to make the form study-specific."""
        # Get the user and remove it from kwargs (b/c/ of UserFormKwargsMixin on the view.)
        self.user = kwargs.pop('user')
        # Call super here to set up all of the fields.
        super(TaggableStudyFilteredTraitQuerysetMixin, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        studies = list(UserData.objects.get(user=self.user).taggable_studies.all())
        if len(studies) == 1:
            self.title += ' for study {} ({})'.format(studies[0].phs, studies[0].i_study_name)
        else:
            study_string = '; '.join(['{} ({})'.format(x.phs, x.i_study_name) for x in studies])
            self.title += ' for studies ' + study_string
        self.fields['trait'].queryset = SourceTrait.objects.filter(
            source_dataset__source_study_version__study__in=studies,
            source_dataset__source_study_version__i_is_deprecated=False
        )
        # Not related to study filtering, but put formatting and submit button here to prevent repetition.
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-2'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_method = 'post'
        button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
        self.helper.layout.append(button_save)


# class TagByPkMixin():


class TaggedTraitForm(TaggableStudyFilteredTraitQuerysetMixin, forms.ModelForm):
    """Form for creating TaggedTrait objects."""

    title = 'Tag a phenotype'
    trait = forms.ModelChoiceField(queryset=SourceTrait.objects.all(),
                                   required=True,
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
        super(TaggedTraitForm, self).__init__(*args, **kwargs)


# class ManyTaggedTraitsForm(forms.Form):
#     """Form for creating TaggedTrait objects."""
# 
#     title = 'Tag phenotypes'
#     traits = forms.ModelMultipleChoiceField(
#         queryset=SourceTrait.objects.all(),
#         required=True,
#         widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
#         help_text='Select one or more phenotypes.')
#     tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
#     # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
#     # Submitting an empty value for this field sets the field to False.
#     recommended = forms.BooleanField(required=False)
# 
#     def __init__(self, *args, **kwargs):
#         super(TaggedTraitMultipleForm, self).__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.form_class = 'form-horizontal'
#         self.helper.label_class = 'col-sm-2'
#         self.helper.field_class = 'col-sm-6'
#         self.helper.form_method = 'post'
#         button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
#         self.helper.layout.append(button_save)
# 
# 
# class StudyManyTaggedTraitsForm(ManyTaggedTraitsForm):
# 
#     def __init__(self, *args, **kwargs):
#         """Override __init__ to make the form study-specific."""
#         study_pk = kwargs.pop('study_pk')
#         super(StudyManyTaggedTraitsForm, self).__init__(*args, **kwargs)
#         study = Study.objects.get(pk=study_pk)
#         self.title += ' for study {} ({})'.format(study.phs, study.i_study_name)
#         self.fields['traits'].queryset = SourceTrait.objects.filter(
#             source_dataset__source_study_version__study__pk=study_pk)
# 
# 
# class ManyTaggedTraitsFromTagForm(forms.Form):
#     """Form for creating TaggedTrait objects from a specific Tag object."""
# 
#     title = 'Tag phenotypes'
#     traits = forms.ModelMultipleChoiceField(
#         queryset=SourceTrait.objects.all(),
#         required=True,
#         widget=autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
#         help_text='Select one or more phenotypes.')
#     # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
#     # Submitting an empty value for this field sets the field to False.
#     recommended = forms.BooleanField(required=False)
# 
#     def __init__(self, *args, **kwargs):
#         super(TaggedTraitMultipleFromTagForm, self).__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.form_class = 'form-horizontal'
#         self.helper.label_class = 'col-sm-2'
#         self.helper.field_class = 'col-sm-6'
#         self.helper.form_method = 'post'
#         button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
#         self.helper.layout.append(button_save)
# 
# 
# class TagSpecificTraitForm(forms.Form):
#     """Form for creating TaggedTrait objects from a specific SourceTrait object."""
# 
#     title = 'Tag the phenotype'
#     tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(), required=True)
#     # Set required=False for recommended - otherwise it will be required to be checked, which disallows False values.
#     # Submitting an empty value for this field sets the field to False.
#     recommended = forms.BooleanField(required=False)
# 
#     def __init__(self, *args, **kwargs):
#         super(TagSpecificTraitForm, self).__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.form_class = 'form-horizontal'
#         self.helper.label_class = 'col-sm-2'
#         self.helper.field_class = 'col-sm-6'
#         self.helper.form_method = 'post'
#         button_save = generate_button_html('submit', 'Save', btn_type='submit', css_class='btn-primary')
#         self.helper.layout.append(button_save)
