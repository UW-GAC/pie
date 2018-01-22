"""Form classes for the tags app."""

from django import forms
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from dal import autocomplete

from . import models
from trait_browser.models import SourceTrait, Study


EXISTING_TAGGED_TRAIT_ERROR_STRING = u"""The tag {tag_name} has already been applied to dbGaP phenotype variable {phv}
                                         ({trait_name}). Select a different phenotype and try again.."""
MISSING_TRAITS_ERROR = forms.ValidationError(
    u"""You must specify at least one phenotype in the 'phenotypes' or 'recommended phenotypes' field."""
)
REPEATED_TRAIT_ERROR = forms.ValidationError(
    u"""You cannot repeat a phenotype in both the 'phenotypes' and 'recommended phenotypes' field."""
)
LOWER_TITLE_EXISTS_ERROR = forms.ValidationError(
    u"""A tag with the same (case-insensitive) title already exists."""
)


def generate_button_html(name, value, btn_type="submit", css_class="btn-primary"):
    """Make html for a submit button."""
    params = {'name': name,
              'value': value,
              'btn_type': btn_type,
              'css_class': css_class}
    html = "<input type='%(btn_type)s' name='%(name)s', value='%(value)s', class='btn %(css_class)s', id='button-id-%(name)s'/>"  # noqa: E501
    button_html = HTML(html % params)
    return button_html


class TagAdminForm(forms.ModelForm):
    """Custom form for the Tag admin page."""

    class Meta:
        model = models.Tag
        fields = ('title', 'description', 'instructions', )
        help_texts = {'title': 'A short, unique title.',
                      'description': 'A detailed description of the phenotype concept described by this tag.',
                      'instructions': 'Very detailed instructions for which traits fit with this tag.', }

    def clean(self):
        """Custom cleaning to enforce uniqueness of lower_title before it's saved."""
        cleaned_data = super(TagAdminForm, self).clean()
        title = cleaned_data.get('title')
        if title is not None:
            lower_title = title.lower()
            if models.Tag.objects.filter(lower_title=lower_title).exists():
                self.add_error('title', LOWER_TITLE_EXISTS_ERROR)


class TaggedTraitForm(forms.ModelForm):
    """Form for creating a single TaggedTrait object."""

    title = 'Apply a tag to a phenotype'
    subtitle = 'Select a tag and a dbGaP phenotype variable to apply it to'
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'))
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
        if self.user.is_staff:
            studies = list(Study.objects.all())
        else:
            studies = list(self.user.profile.taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to phenotypes from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to phenotypes from the following studies:'
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

    def clean(self):
        """Custom cleaning to check that traits aren't already tagged."""
        cleaned_data = super(TaggedTraitForm, self).clean()
        trait = cleaned_data.get('trait')
        tag = cleaned_data.get('tag')
        if tag is not None and trait is not None:
            if trait in tag.traits.all():
                already_tagged_error = forms.ValidationError(
                    EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                        tag_name=tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                )
                self.add_error('trait', already_tagged_error)
        return cleaned_data


class TaggedTraitAdminForm(forms.ModelForm):
    """Custom form for the TaggedTrait admin pages."""

    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'))
    trait = forms.ModelChoiceField(
        queryset=SourceTrait.objects.filter(source_dataset__source_study_version__i_is_deprecated=False),
        required=True, label='Phenotype',
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

    def clean(self):
        """Custom cleaning to check that the trait isn't already tagged."""
        cleaned_data = super(TaggedTraitAdminForm, self).clean()
        trait = cleaned_data.get('trait')
        tag = cleaned_data.get('tag')
        if tag is not None and trait is not None:
            if trait in tag.traits.all():
                already_tagged_error = forms.ValidationError(
                    EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                        tag_name=tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                )
                self.add_error('trait', already_tagged_error)
        return cleaned_data


class TaggedTraitByTagForm(forms.Form):
    """Form for creating a single TaggedTrait object with a specific tag."""

    title = 'Apply this tag to a phenotype'
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
        tag_pk = kwargs.pop('tag_pk')
        self.tag = get_object_or_404(models.Tag, pk=tag_pk)
        # Call super here to set up all of the fields.
        super(TaggedTraitByTagForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        if self.user.is_staff:
            studies = list(Study.objects.all())
        else:
            studies = list(self.user.profile.taggable_studies.all())
        self.subtitle = mark_safe(
            'Select a dbGaP phenotype variable to apply the <mark>{}</mark> tag to'.format(self.tag.title))
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to phenotypes from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to phenotypes from the following studies:'
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

    def clean(self):
        """Custom cleaning to check that traits aren't already tagged."""
        cleaned_data = super(TaggedTraitByTagForm, self).clean()
        trait = cleaned_data.get('trait')
        if trait is not None:
            if trait in self.tag.traits.all():
                already_tagged_error = forms.ValidationError(
                    EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                        tag_name=self.tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                )
                self.add_error('trait', already_tagged_error)
        return cleaned_data


class ManyTaggedTraitsForm(forms.Form):
    """Form for creating many TaggedTrait objects."""

    title = 'Apply a tag to multiple phenotypes'
    subtitle = 'Select a tag and one or more dbGaP phenotype variables to apply it to'
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'))
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
        if self.user.is_staff:
            studies = list(Study.objects.all())
        else:
            studies = list(self.user.profile.taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to phenotypes from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to phenotypes from the following studies:'
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
        """Custom cleaning to check that at least one trait is selected, and traits aren't already tagged."""
        cleaned_data = super(ManyTaggedTraitsForm, self).clean()
        traits = cleaned_data.get('traits', [])
        recommended_traits = cleaned_data.get('recommended_traits', [])
        tag = cleaned_data.get('tag')
        if tag is not None:
            for trait in traits:
                if trait in tag.traits.all():
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('traits', already_tagged_error)
            for trait in recommended_traits:
                if trait in tag.traits.all():
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('recommended_traits', already_tagged_error)
        if len(traits) == 0 and len(recommended_traits) == 0:
            self.add_error('traits', MISSING_TRAITS_ERROR)
            self.add_error('recommended_traits', MISSING_TRAITS_ERROR)
        if len(set(traits) & set(recommended_traits)) > 0:
            self.add_error('traits', REPEATED_TRAIT_ERROR)
            self.add_error('recommended_traits', REPEATED_TRAIT_ERROR)
        return cleaned_data


class ManyTaggedTraitsByTagForm(forms.Form):
    """Form for creating many TaggedTrait objects for a specific tag."""

    title = 'Apply this tag to multiple phenotypes'
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
        tag_pk = kwargs.pop('tag_pk')
        self.tag = get_object_or_404(models.Tag, pk=tag_pk)
        # Call super here to set up all of the fields.
        super(ManyTaggedTraitsByTagForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        if self.user.is_staff:
            studies = list(Study.objects.all())
        else:
            studies = list(self.user.profile.taggable_studies.all())
        self.subtitle = mark_safe(
            'Select a dbGaP phenotype variable to apply the <mark>{}</mark> tag to'.format(self.tag.title))
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to phenotypes from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to phenotypes from the following studies:'
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
        """Custom cleaning to check that at least one trait is selected, and traits aren't already tagged."""
        cleaned_data = super(ManyTaggedTraitsByTagForm, self).clean()
        traits = cleaned_data.get('traits', [])
        recommended_traits = cleaned_data.get('recommended_traits', [])
        for trait in traits:
            if trait in self.tag.traits.all():
                already_tagged_error = forms.ValidationError(
                    EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                        tag_name=self.tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                )
                self.add_error('traits', already_tagged_error)
        for trait in recommended_traits:
            if trait in self.tag.traits.all():
                already_tagged_error = forms.ValidationError(
                    EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                        tag_name=self.tag.title, phv=trait.variable_accession, trait_name=trait.i_trait_name)
                )
                self.add_error('recommended_traits', already_tagged_error)
        if len(traits) == 0 and len(recommended_traits) == 0:
            self.add_error('traits', MISSING_TRAITS_ERROR)
            self.add_error('recommended_traits', MISSING_TRAITS_ERROR)
        if len(set(traits) & set(recommended_traits)) > 0:
            self.add_error('traits', REPEATED_TRAIT_ERROR)
            self.add_error('recommended_traits', REPEATED_TRAIT_ERROR)
        return cleaned_data


class TagSpecificTraitForm(forms.Form):
    """Form for creating TaggedTrait objects from a specific SourceTrait object."""

    title = 'Apply a tag to this phenotype'
    subtitle = 'Select a tag to apply to this dbGaP phenotype variable'
    subtitle2 = ''
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'))
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