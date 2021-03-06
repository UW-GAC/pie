"""Form classes for the tags app."""

from django import forms
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit
from dal import autocomplete, forward

from trait_browser.models import SourceTrait, Study

from . import models


EXISTING_TAGGED_TRAIT_ERROR_STRING = u"""The tag {tag_name} has already been applied to study variable {phv}
                                         ({trait_name}). Change your selection and try again."""
ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING = u"""The tag {tag_name} was previously applied to study variable {phv}
                                                  ({trait_name}) and removed during quality review.
                                                  Change your selection and try again."""
LOWER_TITLE_EXISTS_ERROR = forms.ValidationError(
    u"""A tag with the same (case-insensitive) title already exists."""
)

TAG_HELP = """Select a phenotype tag. Start typing the tag name to filter the list."""
TRAIT_HELP = """Select a study variable. Start typing the dbGaP variable accession (phv)
                or variable name to filter the list (example: 'phv55555', '55555', or 'rdirem2p').
                Note that variable names may not be unique.
                """
MANY_TRAITS_HELP = """Select one or more study variables. Start typing the dbGaP variable accession (phv)
                or variable name to filter the list (example: 'phv55555', '55555', or 'rdirem2p').
                Note that variable names may not be unique.
                """


def generate_button_html(name, value, btn_type="submit", css_class="btn-primary"):
    """Make html for a submit button."""
    params = {'name': name,
              'value': value,
              'btn_type': btn_type,
              'css_class': css_class}
    html = "<input type='%(btn_type)s' name='%(name)s', value='%(value)s', class='btn %(css_class)s', id='button-id-%(name)s'/>"  # noqa: E501
    button_html = HTML(html % params)
    return button_html


class SubmitCssClass(Submit):
    """Create a submit button with a different class than the default."""

    def __init__(self, *args, **kwargs):
        """Change CSS class of the submit button if given."""
        css_class = kwargs.get('css_class')
        super().__init__(*args, **kwargs)
        if css_class is not None:
            self.field_classes = 'btn {}'.format(css_class)


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
        # If the object doesn't exist already.
        if self.instance.pk is None:
            if title is not None:
                lower_title = title.lower()
                if models.Tag.objects.filter(lower_title=lower_title).exists():
                    self.add_error('title', LOWER_TITLE_EXISTS_ERROR)


class TaggedTraitForm(forms.ModelForm):
    """Form for creating a single TaggedTrait object."""

    title = 'Apply a tag to a study variable'
    subtitle = 'Select a tag and a study variable to apply it to'
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'),
                                 help_text=TAG_HELP)
    trait = forms.ModelChoiceField(queryset=SourceTrait.objects.all(),
                                   required=True,
                                   label='Variable',
                                   widget=autocomplete.ModelSelect2(
                                       url='trait_browser:source:traits:autocomplete:taggable:by-name-or-phv'),
                                   help_text=TRAIT_HELP)

    class Meta:
        model = models.TaggedTrait
        fields = ('tag', 'trait', )

    def __init__(self, *args, **kwargs):
        """Give the form options specific to the user and their taggable studies."""
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
            self.subtitle2 = 'You can apply tags to variables from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to variables from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['trait'].queryset = SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study__in=studies)
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
        # We don't need to check that the trait comes from a non-deprecated study version. That
        # is handled by the super's clean() method because the form __init__ method already uses
        # a filtered queryset for traits.
        trait = cleaned_data.get('trait')
        tag = cleaned_data.get('tag')
        if tag is not None and trait is not None:
            if trait in tag.all_traits.all():
                taggedtrait = models.TaggedTrait.objects.get(trait=trait, tag=tag)
                if taggedtrait.archived:
                    # Because this is a ModelForm, a non-field error is added when the TaggedTrait already exists.
                    archived_taggedtrait_error = forms.ValidationError(
                        ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', archived_taggedtrait_error)
                else:
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', already_tagged_error)
        return cleaned_data


class TaggedTraitAdminForm(forms.ModelForm):
    """Custom form for the TaggedTrait admin pages."""

    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'))
    trait = forms.ModelChoiceField(
        queryset=SourceTrait.objects.current().all(),
        required=True, label='Variable',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:traits:autocomplete:by-name-or-phv'))

    class Meta:
        model = models.TaggedTrait
        fields = ('tag', 'trait', )

    def clean(self):
        """Custom cleaning to check that the trait isn't already tagged."""
        cleaned_data = super(TaggedTraitAdminForm, self).clean()
        trait = cleaned_data.get('trait')
        tag = cleaned_data.get('tag')
        if tag is not None and trait is not None:
            if trait in tag.all_traits.all():
                taggedtrait = models.TaggedTrait.objects.get(trait=trait, tag=tag)
                if taggedtrait.archived:
                    archived_taggedtrait_error = forms.ValidationError(
                        ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', archived_taggedtrait_error)
                else:
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', already_tagged_error)
        return cleaned_data


class TaggedTraitByTagForm(forms.Form):
    """Form for creating a single TaggedTrait object with a specific tag."""

    title = 'Apply this tag to a study variable'
    trait = forms.ModelChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        label='Variable',
        widget=autocomplete.ModelSelect2(url='trait_browser:source:traits:autocomplete:taggable:by-name-or-phv'),
        help_text=TRAIT_HELP)

    def __init__(self, *args, **kwargs):
        """Give the form options specific to the user and their taggable studies."""
        self.user = kwargs.pop('user')  # For UserFormKwargsMixin.
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
            'Select a study variable to apply the <mark>{}</mark> tag to'.format(self.tag.title))
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to variables from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to variables from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['trait'].queryset = SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study__in=studies)
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
        # We don't need to check that the trait comes from a non-deprecated study version. That
        # is handled by the super's clean() method because the form __init__ method already uses
        # a filtered queryset for traits.
        cleaned_data = super(TaggedTraitByTagForm, self).clean()
        trait = cleaned_data.get('trait')
        if trait is not None:
            if trait in self.tag.all_traits.all():
                taggedtrait = models.TaggedTrait.objects.get(trait=trait, tag=self.tag)
                if taggedtrait.archived:
                    archived_taggedtrait_error = forms.ValidationError(
                        ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=self.tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', archived_taggedtrait_error)
                else:
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=self.tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('trait', already_tagged_error)
        return cleaned_data


class ManyTaggedTraitsForm(forms.Form):
    """Form for creating many TaggedTrait objects."""

    title = 'Apply a tag to multiple study variables'
    subtitle = 'Select a tag and one or more study variables to apply it to'
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'),
                                 help_text=TAG_HELP)
    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        label='Variable(s)',
        widget=autocomplete.ModelSelect2Multiple(
            url='trait_browser:source:traits:autocomplete:taggable:by-name-or-phv'),
        help_text=MANY_TRAITS_HELP)

    def __init__(self, *args, **kwargs):
        """Give the form options specific to the user and their taggable studies."""
        self.user = kwargs.pop('user')  # For UserFormKwargsMixin.
        # Call super here to set up all of the fields.
        super(ManyTaggedTraitsForm, self).__init__(*args, **kwargs)
        # Filter the queryset of traits by the user's taggable studies, and only non-deprecated.
        if self.user.is_staff:
            studies = list(Study.objects.all())
        else:
            studies = list(self.user.profile.taggable_studies.all())
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to variables from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to variables from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['traits'].queryset = SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study__in=studies)
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
        # We don't need to check that the trait comes from a non-deprecated study version. That
        # is handled by the super's clean() method because the form __init__ method already uses
        # a filtered queryset for traits.
        cleaned_data = super(ManyTaggedTraitsForm, self).clean()
        traits = cleaned_data.get('traits', [])
        tag = cleaned_data.get('tag')
        if tag is not None:
            for trait in traits:
                if trait in tag.all_traits.all():
                    taggedtrait = models.TaggedTrait.objects.get(trait=trait, tag=tag)
                    if taggedtrait.archived:
                        archived_taggedtrait_error = forms.ValidationError(
                            ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                                tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                        )
                        self.add_error('traits', archived_taggedtrait_error)
                    else:
                        already_tagged_error = forms.ValidationError(
                            EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                                tag_name=tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                        )
                        self.add_error('traits', already_tagged_error)
        return cleaned_data


class ManyTaggedTraitsByTagForm(forms.Form):
    """Form for creating many TaggedTrait objects for a specific tag."""

    title = 'Apply this tag to multiple study variables'
    traits = forms.ModelMultipleChoiceField(
        queryset=SourceTrait.objects.all(),
        required=True,
        label='Variable(s)',
        widget=autocomplete.ModelSelect2Multiple(
            url='trait_browser:source:traits:autocomplete:taggable:by-name-or-phv'),
        help_text=MANY_TRAITS_HELP)

    def __init__(self, *args, **kwargs):
        """Give the form options specific to the user and their taggable studies."""
        self.user = kwargs.pop('user')  # For UserFormKwargsMixin.
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
            'Select one or more study variables to apply the <mark>{}</mark> tag to'.format(self.tag.title))
        if len(studies) == 1:
            self.subtitle2 = 'You can apply tags to variables from the study {} ({})'.format(
                studies[0].i_study_name, studies[0].phs)
        else:
            self.subtitle2 = 'You can apply tags to variables from the following studies:'
            for study in studies:
                self.subtitle2 += """
                <ul>
                    <li>{} ({})</li>
                </ul>
                """.format(study.i_study_name, study.phs)
            self.subtitle2 = mark_safe(self.subtitle2)
        self.fields['traits'].queryset = SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study__in=studies)
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
        # We don't need to check that the trait comes from a non-deprecated study version. That
        # is handled by the super's clean() method because the form __init__ method already uses
        # a filtered queryset for traits.
        cleaned_data = super(ManyTaggedTraitsByTagForm, self).clean()
        traits = cleaned_data.get('traits', [])
        for trait in traits:
            if trait in self.tag.all_traits.all():
                taggedtrait = models.TaggedTrait.objects.get(trait=trait, tag=self.tag)
                if taggedtrait.archived:
                    archived_taggedtrait_error = forms.ValidationError(
                        ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=self.tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('traits', archived_taggedtrait_error)
                else:
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=self.tag.title, phv=trait.full_accession, trait_name=trait.i_trait_name)
                    )
                    self.add_error('traits', already_tagged_error)
        return cleaned_data


class TagSpecificTraitForm(forms.Form):
    """Form for creating TaggedTrait objects from a specific SourceTrait object."""

    title = 'Apply a tag to this study variable'
    subtitle = 'Select a tag to apply to this study variable'
    subtitle2 = ''
    tag = forms.ModelChoiceField(queryset=models.Tag.objects.all(),
                                 widget=autocomplete.ModelSelect2(url='tags:autocomplete'),
                                 help_text=TAG_HELP)

    def __init__(self, *args, **kwargs):
        """Give the form options specific to the trait to be tagged."""
        trait_pk = kwargs.pop('trait_pk')  # trait_pk added in the view.
        self.trait = get_object_or_404(SourceTrait, pk=trait_pk)
        super(TagSpecificTraitForm, self).__init__(*args, **kwargs)
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
        cleaned_data = super(TagSpecificTraitForm, self).clean()
        tag = cleaned_data.get('tag', None)
        if self.trait not in SourceTrait.objects.current():
            error = 'This study variable cannot be tagged because it is not from the most recent study version.'
            self.add_error(None, error)
        if tag is not None:
            if self.trait in tag.all_traits.all():
                taggedtrait = models.TaggedTrait.objects.get(trait=self.trait, tag=tag)
                if taggedtrait.archived:
                    archived_taggedtrait_error = forms.ValidationError(
                        ARCHIVED_EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
                    )
                    self.add_error('tag', archived_taggedtrait_error)
                else:
                    already_tagged_error = forms.ValidationError(
                        EXISTING_TAGGED_TRAIT_ERROR_STRING.format(
                            tag_name=tag.title, phv=self.trait.full_accession, trait_name=self.trait.i_trait_name)
                    )
                    self.add_error('tag', already_tagged_error)
        return cleaned_data


class DCCReviewBaseForm(forms.ModelForm):

    SUBMIT_CONFIRM = 'confirm'
    SUBMIT_FOLLOWUP = 'require-followup'

    def clean(self):
        """Custom cleaning to check a comment is given for TaggedTraits that require followup."""
        cleaned_data = super().clean()
        comment = cleaned_data.get('comment')
        status = cleaned_data.get('status')
        if status == models.DCCReview.STATUS_FOLLOWUP and not comment:
            error = forms.ValidationError('Comment cannot be blank for tagged variables that require followup.',
                                          code='followup_comment')
            self.add_error('comment', error)
        if status == models.DCCReview.STATUS_CONFIRMED and comment:
            error = forms.ValidationError('Comment must be blank for tagged variables that are confirmed.',
                                          code='confirmed_comment')
            self.add_error('comment', error)
        return cleaned_data

    class Meta:
        model = models.DCCReview
        fields = ('status', 'comment', )
        help_texts = {
            'comment': 'Only include a comment for tagged variables that require followup.'
        }
        widgets = {
            'status': forms.HiddenInput
        }


class DCCReviewByTagAndStudyForm(DCCReviewBaseForm):
    """Form for creating a single DCCReview object."""

    SUBMIT_SKIP = 'skip'

    def __init__(self, *args, **kwargs):
        """Add submit buttons."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            'comment',
            FormActions(
                Submit(self.SUBMIT_CONFIRM, 'Confirm'),
                SubmitCssClass(self.SUBMIT_FOLLOWUP, 'Require study followup', css_class='btn-warning'),
                SubmitCssClass(self.SUBMIT_SKIP, 'Skip', css_class='btn-default')
            )
        )

    class Meta(DCCReviewBaseForm.Meta):
        pass


class DCCReviewForm(DCCReviewBaseForm):

    def __init__(self, *args, **kwargs):
        """Add submit buttons."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            'comment',
            FormActions(
                Submit(self.SUBMIT_CONFIRM, 'Confirm'),
                SubmitCssClass(self.SUBMIT_FOLLOWUP, 'Require study followup', css_class='btn-warning')
            )
        )

    class Meta(DCCReviewBaseForm.Meta):
        pass


class DCCReviewAdminForm(DCCReviewBaseForm):

    class Meta:
        model = models.DCCReview
        fields = ('tagged_trait', 'status', 'comment', )


class DCCReviewTagAndStudySelectForm(forms.Form):

    ERROR_NO_TAGGED_TRAITS = 'No tagged variables for this tag and study!'

    tag = forms.ModelChoiceField(
        queryset=models.Tag.objects.all(),
        widget=autocomplete.ModelSelect2(url='tags:autocomplete',
                                         forward=('unreviewed_only', forward.Const(True, 'unreviewed_only'))),
        help_text="""First select a phenotype tag. Start typing the tag name to filter the list."""
    )
    study = forms.ModelChoiceField(
        queryset=Study.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='trait_browser:source:studies:autocomplete:by-name-or-phs',
            forward=(
                'tag',
                forward.Const(True, 'unreviewed_non_archived_tagged_traits_only'),
            )
        ),
        help_text=("Then select a study. Start typing the study name or phs to filter the list. Only studies with at "
                   "least one unreviewed study variable tagged with the selected tag will be shown.")
    )
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-8'
    helper.layout = Layout(
        'tag',
        'study',
        FormActions(
            Submit('submit', 'Submit'),
        )
    )

    def __init__(self, *args, **kwargs):
        """Set dynamic form properties."""
        # Call super here to set up all of the fields.
        super().__init__(*args, **kwargs)
        # Filter to the set of tags with unreviewed tagged traits.
        tags_to_review_pks = models.TaggedTrait.objects.unreviewed().values_list('tag__pk', flat=True).distinct()
        tags_to_review = models.Tag.objects.filter(pk__in=tags_to_review_pks)
        self.fields['tag'].queryset = tags_to_review

    class Media:
        js = ('js/taggedtrait_review_select_form.js', )

    def clean(self):
        cleaned_data = super().clean()
        tag = cleaned_data.get('tag')
        study = cleaned_data.get('study')
        if tag and study:
            # Check that some TaggedTraits exist.
            n = models.TaggedTrait.objects.non_archived().unreviewed().filter(
                tag=tag,
                trait__source_dataset__source_study_version__study=study
            ).count()
            if n == 0:
                raise forms.ValidationError(self.ERROR_NO_TAGGED_TRAITS)
        return cleaned_data


class StudyResponseDisagreeForm(forms.Form):
    """Form for phenotype taggers to provide a reason that they disagree with a DCC Review."""

    # Use a Form instead of a ModelForm, because the "comment" field is not required by
    # the model, but it is required when adding a "disagree" response. The object will
    # then be created in the view with the appropriate status and the given comment.
    comment = forms.CharField(
        label='Comment',
        help_text='Provide a reason why this variable is appropriately tagged.',
        widget=forms.Textarea
    )

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-8'
    helper.layout = Layout(
        'comment',
        FormActions(
            Submit('submit', 'Submit'),
        )
    )


class StudyResponseBaseForm(forms.ModelForm):

    def clean(self):
        """Custom cleaning to check a comment is given for StudyResponses that disagree."""
        cleaned_data = super().clean()
        comment = cleaned_data.get('comment')
        status = cleaned_data.get('status')
        if status == models.StudyResponse.STATUS_DISAGREE and not comment:
            error = forms.ValidationError('Comment cannot be blank if you disagree with the DCC review.',
                                          code='disagree_comment')
            self.add_error('comment', error)
        if status == models.StudyResponse.STATUS_AGREE and comment:
            error = forms.ValidationError('Comment must be blank if you agree with the DCC review.',
                                          code='agree_comment')
            self.add_error('comment', error)
        return cleaned_data

    class Meta:
        model = models.StudyResponse
        fields = ('status', 'comment', )
        help_texts = {
            'comment': 'Only include a comment when you disagree that this variable is tagged incorrectly.'
        }


class StudyResponseAdminForm(StudyResponseBaseForm):

    class Meta:
        model = models.StudyResponse
        fields = ('status', 'comment', )


class DCCDecisionBaseForm(forms.ModelForm):

    SUBMIT_CONFIRM = 'confirm'
    SUBMIT_REMOVE = 'remove'

    def clean(self):
        """Custom cleaning to require a comment."""
        # I tried implementing this by setting DCCDecision.comment(blank=False), but this led to an issue where modern
        # browsers prevent a POST request from being submitted if a "required" (html5 tag) field is empty:
        # https://stackoverflow.com/questions/5392882/why-is-chrome-showing-a-please-fill-out-this-field-tooltip-on-empty-fields
        # This prevented the SKIP button from working properly. So instead I set comment(blank=True) and am using
        # this clean method to make sure a non-blank comment is submitted.
        cleaned_data = super().clean()
        comment = cleaned_data.get('comment')
        if comment == '':
            error = forms.ValidationError('Comment cannot be blank.', code='comment_required')
            self.add_error('comment', error)
        return cleaned_data

    class Meta:
        model = models.DCCDecision
        fields = ('decision', 'comment', )
        help_texts = {
            'comment': 'Add a comment explaining why you decided to confirm or remove this tagged variable.'
        }
        widgets = {
            'decision': forms.HiddenInput
        }


class DCCDecisionByTagAndStudyForm(DCCDecisionBaseForm):
    """Form for creating a single DCCDecision object."""

    SUBMIT_SKIP = 'skip'

    def __init__(self, *args, **kwargs):
        """Add submit buttons."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'decision',
            'comment',
            FormActions(
                Submit(self.SUBMIT_CONFIRM, 'Confirm'),
                SubmitCssClass(self.SUBMIT_REMOVE, 'Remove', css_class='btn-danger'),
                SubmitCssClass(self.SUBMIT_SKIP, 'Skip', css_class='btn-default')
            )
        )

    class Meta(DCCDecisionBaseForm.Meta):
        pass


class DCCDecisionForm(DCCDecisionBaseForm):

    def __init__(self, *args, **kwargs):
        """Add submit buttons."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'status',
            'comment',
            FormActions(
                Submit(self.SUBMIT_CONFIRM, 'Confirm'),
                SubmitCssClass(self.SUBMIT_REMOVE, 'Remove', css_class='btn-danger')
            )
        )

    class Meta(DCCDecisionBaseForm.Meta):
        pass
