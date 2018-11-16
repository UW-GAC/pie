"""View functions and classes for the tags app."""

from itertools import groupby

from django.db.models import Case, Count, F, IntegerField, Q, Sum, When
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views.generic import (CreateView, DetailView, DeleteView, FormView, ListView, RedirectView, TemplateView,
                                  UpdateView, View)
from django.views.generic.edit import ProcessFormView

from braces.views import (FormMessagesMixin, FormValidMessageMixin, GroupRequiredMixin, LoginRequiredMixin,
                          MessageMixin, PermissionRequiredMixin, UserFormKwargsMixin, UserPassesTestMixin)
from dal import autocomplete
from django_tables2 import SingleTableMixin

from core.utils import SessionVariableMixin, ValidateObjectMixin
from trait_browser.models import Study

from . import forms
from . import models
from . import tables


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.
TAGGING_ERROR_MESSAGE = 'Oops! Applying the tag to a study variable failed.'
TAGGING_MULTIPLE_ERROR_MESSAGE = 'Oops! Applying the tag to study variables failed.'
CONFIRMED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE = (
    "Oops! Tagged study variables that have been reviewed and confirmed by the DCC can't be removed."
)


class TaggableStudiesRequiredMixin(UserPassesTestMixin):
    """Mixin requiring that the user have 1 or more taggable studies designated, or be staff."""

    def test_func(self, user):
        return user.profile.taggable_studies.count() > 0 or user.is_staff


class SpecificTaggableStudyRequiredMixin(UserPassesTestMixin):
    """Mixin to check if a study is in a user's list of taggable studies or (optionally) if the user is staff."""

    allow_staff = False

    def dispatch(self, request, *args, **kwargs):
        self.set_study()
        return super().dispatch(request, *args, **kwargs)

    def set_study(self):
        raise ImproperlyConfigured(
            "SpecificTaggableStudyRequiredMixin requires a definition for 'set_study()'"
        )

    def test_func(self, user):
        if self.allow_staff and user.is_staff:
            return True
        else:
            return self.study in user.profile.taggable_studies.all()


class TagDetail(LoginRequiredMixin, DetailView):
    """Detail view class for Tag."""

    model = models.Tag
    context_object_name = 'tag'

    def get_context_data(self, **kwargs):
        context = super(TagDetail, self).get_context_data(**kwargs)
        study_counts = models.TaggedTrait.objects.non_archived().filter(tag=self.object).values(
            study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('trait__source_dataset__source_study_version__study__pk')
        ).annotate(
            tt_count=Count('pk')
        ).values(
            'study_name', 'study_pk', 'tt_count').order_by('study_name')
        context['study_counts'] = study_counts
        return context


class TagAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for autocompleting tag model choice fields by title in a form. Case-insensitive."""

    def get_queryset(self):
        retrieved = models.Tag.objects.all()
        if self.q:
            retrieved = retrieved.filter(lower_title__iregex=r'^{}'.format(self.q))
        return retrieved


class TagList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Tag
    table_class = tables.TagTable
    context_table_name = 'tag_table'
    table_pagination = {'per_page': TABLE_PER_PAGE * 2}


class TaggedTraitDetail(LoginRequiredMixin, PermissionRequiredMixin, SpecificTaggableStudyRequiredMixin, DetailView):

    model = models.TaggedTrait
    context_object_name = 'tagged_trait'
    template_name = 'tags/taggedtrait_detail.html'
    redirect_unauthenticated_users = True
    raise_exception = True
    allow_staff = True
    permission_required = 'tags.add_taggedtrait'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        user_is_study_tagger = self.object.trait.source_dataset.source_study_version.study in user_studies
        user_is_staff = self.request.user.is_staff
        user_has_study_access = user_is_staff or user_is_study_tagger
        is_non_archived = not self.object.archived
        dccreview_exists = hasattr(self.object, 'dcc_review')
        dccreview_confirmed = dccreview_exists and (self.object.dcc_review.status == models.DCCReview.STATUS_CONFIRMED)
        needs_followup = dccreview_exists and self.object.dcc_review.status == models.DCCReview.STATUS_FOLLOWUP
        user_has_dccreview_add_perms = self.request.user.has_perm('tags.add_dccreview')
        user_has_dccreview_change_perms = self.request.user.has_perm('tags.change_dccreview')
        user_has_dccdecision_add_perms = self.request.user.has_perm('tags.add_dccdecision')
        user_has_dccdecision_change_perms = self.request.user.has_perm('tags.change_dccdecision')
        studyresponse_exists = dccreview_exists and hasattr(self.object.dcc_review, 'study_response')
        studyresponse_agree = studyresponse_exists and \
            (self.object.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE)
        studyresponse_disagree = studyresponse_exists and \
            (self.object.dcc_review.study_response.status == models.StudyResponse.STATUS_DISAGREE)
        dccdecision_exists = dccreview_exists and hasattr(self.object.dcc_review, 'dcc_decision')
        dccdecision_remove = dccdecision_exists and \
            (self.object.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_REMOVE)
        dccdecision_confirm = dccdecision_exists and \
            (self.object.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_CONFIRM)
        if dccreview_confirmed:
            color = 'bg-success'
        elif dccdecision_confirm:
            color = 'bg-success'
        elif not is_non_archived:
            color = 'bg-danger'
        else:
            color = ''
        # Set context variables for controlling view options.
        context['show_quality_review_panel'] = user_has_study_access
        context['show_dcc_review_add_button'] = (not dccreview_exists) and user_has_dccreview_add_perms \
            and is_non_archived
        context['show_dcc_review_update_button'] = dccreview_exists and user_has_dccreview_change_perms \
            and not studyresponse_exists and is_non_archived and not dccdecision_exists
        context['show_dcc_review_confirmed'] = user_has_study_access and dccreview_confirmed
        context['show_dcc_review_needs_followup'] = user_has_study_access and needs_followup
        context['show_study_response_status'] = user_has_study_access and studyresponse_exists
        context['show_study_agrees'] = user_has_study_access and studyresponse_exists and studyresponse_agree
        context['show_study_disagrees'] = user_has_study_access and studyresponse_exists and studyresponse_disagree
        context['show_dcc_decision'] = user_has_study_access and dccdecision_exists
        context['show_dcc_decision_add_button'] = user_has_study_access and user_has_dccdecision_add_perms \
            and dccreview_exists and studyresponse_disagree and not dccdecision_exists
        context['show_dcc_decision_update_button'] = user_has_study_access and user_has_dccdecision_change_perms \
            and dccreview_exists and dccdecision_exists
        context['show_decision_remove'] = user_has_study_access and dccdecision_exists and dccdecision_remove
        context['show_decision_confirm'] = user_has_study_access and dccdecision_exists and dccdecision_confirm
        context['show_decision_comment'] = user_is_staff and dccdecision_exists
        context['show_delete_button'] = user_has_study_access and (not dccreview_exists) and is_non_archived
        context['show_archived'] = not is_non_archived
        context['quality_review_panel_color'] = color
        return context

    def set_study(self):
        self.study = self.get_object().trait.source_dataset.source_study_version.study


class TaggedTraitTagCountsByStudy(LoginRequiredMixin, TemplateView):

    template_name = 'tags/taggedtrait_tagcounts_bystudy.html'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitTagCountsByStudy, self).get_context_data(**kwargs)
        annotated_studies = models.TaggedTrait.objects.non_archived().values(
            study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('trait__source_dataset__source_study_version__study__pk'),
            tag_name=F('tag__title'),
            tag_pk=F('tag__pk')).annotate(
                tt_count=Count('pk')).values(
                    'study_name', 'study_pk', 'tag_name', 'tt_count', 'tag_pk').order_by(
                        'study_name', 'tag_name')
        grouped_annotated_studies = groupby(annotated_studies,
                                            lambda x: {'study_name': x['study_name'], 'study_pk': x['study_pk']})
        grouped_annotated_studies = [(key, list(group)) for key, group in grouped_annotated_studies]
        context['taggedtrait_tag_counts_by_study'] = grouped_annotated_studies
        return context


class TaggedTraitStudyCountsByTag(LoginRequiredMixin, TemplateView):

    template_name = 'tags/taggedtrait_studycounts_bytag.html'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitStudyCountsByTag, self).get_context_data(**kwargs)
        annotated_tags = models.TaggedTrait.objects.non_archived().values(
            study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('trait__source_dataset__source_study_version__study__pk'),
            tag_name=F('tag__title'),
            tag_pk=F('tag__pk')).annotate(
                tt_count=Count('pk')).values(
                    'study_name', 'study_pk', 'tag_name', 'tt_count', 'tag_pk').order_by(
                        'tag_name', 'study_name')
        grouped_annotated_tags = groupby(annotated_tags, lambda x: {'tag_name': x['tag_name'], 'tag_pk': x['tag_pk']})
        grouped_annotated_tags = [(key, list(group)) for key, group in grouped_annotated_tags]
        context['taggedtrait_study_counts_by_tag'] = grouped_annotated_tags
        return context


class TaggedTraitByTagAndStudyList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.TaggedTrait
    context_table_name = 'tagged_trait_table'
    template_name = 'tags/taggedtrait_tag_study_list.html'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get(self, request, *args, **kwargs):
        self.tag = get_object_or_404(models.Tag, pk=self.kwargs['pk'])
        self.study = get_object_or_404(Study, pk=self.kwargs['pk_study'])
        return super(TaggedTraitByTagAndStudyList, self).get(self, request, *args, **kwargs)

    def get_table_data(self):
        if self.request.user.is_staff:
            return self.study.get_all_tagged_traits().filter(tag=self.tag).select_related(
                'tag',
                'trait',
                'trait__source_dataset',
                'trait__source_dataset__source_study_version',
                'dcc_review'
            )
        else:
            return self.study.get_non_archived_tagged_traits().filter(tag=self.tag).select_related(
                'tag',
                'trait',
                'trait__source_dataset',
                'trait__source_dataset__source_study_version',
                'dcc_review'
            )

    def get_table_class(self):
        """Determine whether to use tagged trait table with delete buttons or not."""
        if self.request.user.is_staff:
            return tables.TaggedTraitTableForDCCStaff
        elif (self.request.user.groups.filter(name='phenotype_taggers').exists() and
              self.study in self.request.user.profile.taggable_studies.all()):
            return tables.TaggedTraitTableForStudyTaggers
        else:
            return tables.TaggedTraitTable

    def get_context_data(self, *args, **kwargs):
        context = super(TaggedTraitByTagAndStudyList, self).get_context_data(*args, **kwargs)
        context['study'] = self.study
        context['tag'] = self.tag
        context['show_review_button'] = self.request.user.is_staff
        return context


class TaggedTraitDelete(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin,
                        ValidateObjectMixin, FormMessagesMixin, DeleteView):
    """Delete view class for TaggedTrait objects."""

    model = models.TaggedTrait
    context_object_name = 'tagged_trait'
    permission_required = 'tags.delete_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def get_context_data(self, *args, **kwargs):
        context = super(TaggedTraitDelete, self).get_context_data(*args, **kwargs)
        # Get the url from the "next" parameter, so you can return the user to the page they came from.
        context['next_url'] = self.request.GET.get('next')
        return context

    def get_success_url(self):
        """Redirect the user back to wherever they came from."""
        next_url = self.request.GET.get('next')
        # The next_url can't be the absolute url because that page will give a 404 after the TaggedTrait is deleted.
        if next_url is not None and next_url != self.object.get_absolute_url():
            return next_url
        else:
            return reverse('tags:tag:study:list',
                           kwargs={'pk_study': self.object.trait.source_dataset.source_study_version.study.pk,
                                   'pk': self.object.tag.pk})

    def get_form_valid_message(self):
        msg = 'Tag <a href="{}">{}</a> has been removed from study variable <a href="{}">{}</a>'.format(
            self.object.tag.get_absolute_url(), self.object.tag.title,
            self.object.trait.get_absolute_url(), self.object.trait.i_trait_name)
        return mark_safe(msg)

    def get_validation_failure_url(self):
        return self.get_success_url()

    def validate_object(self):
        """Redirect to the failure url if the taggedtrait is reviewed and confirmed.

        Otherwise, will delete or archive as appropriate, using the custom delete method.
        """
        if hasattr(self.object, 'dcc_review'):
            if self.object.dcc_review.status == self.object.dcc_review.STATUS_CONFIRMED:
                self.messages.error(CONFIRMED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE)
                return False
        return True


class TaggedTraitCreate(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin, UserFormKwargsMixin,
                        FormMessagesMixin, CreateView):
    """Create view class for TaggedTrait objects."""

    model = models.TaggedTrait
    form_class = forms.TaggedTraitForm
    form_invalid_message = TAGGING_ERROR_MESSAGE
    permission_required = 'tags.add_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        """Override form processing to set current user as the TaggedTrait's creator."""
        form.instance.creator = self.request.user
        return super(TaggedTraitCreate, self).form_valid(form)

    def get_success_url(self):
        return self.object.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = 'Tag {} has been applied to study variable <a href="{}">{}</a>'.format(
            self.object.tag.title, self.object.trait.get_absolute_url(), self.object.trait.i_trait_name)
        return mark_safe(msg)


class TaggedTraitCreateByTag(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin,
                             UserFormKwargsMixin, FormMessagesMixin, FormView):
    """Form view class for tagging a trait with a specific tag."""

    form_class = forms.TaggedTraitByTagForm
    form_invalid_message = TAGGING_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'
    permission_required = 'tags.add_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(models.Tag, pk=kwargs.get('pk'))
        return super(TaggedTraitCreateByTag, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Create a TaggedTrait object for the trait given, with a specific tag."""
        tagged_trait = models.TaggedTrait(tag=self.tag, trait=form.cleaned_data['trait'], creator=self.request.user)
        tagged_trait.full_clean()
        tagged_trait.save()
        # Save the traits so you can use them in the form valid message.
        self.trait = form.cleaned_data['trait']
        return super(TaggedTraitCreateByTag, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitCreateByTag, self).get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

    def get_form_kwargs(self):
        kwargs = super(TaggedTraitCreateByTag, self).get_form_kwargs()
        kwargs['tag_pk'] = self.kwargs['pk']
        get_object_or_404(models.Tag, pk=kwargs['tag_pk'])
        return kwargs

    def get_success_url(self):
        return self.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = 'Tag {} has been applied to study variable <a href="{}">{}</a>'.format(
            self.tag.title, self.trait.get_absolute_url(), self.trait.i_trait_name)
        return mark_safe(msg)


class ManyTaggedTraitsCreate(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin,
                             UserFormKwargsMixin, FormMessagesMixin, FormView):
    """Form view class for tagging multiple traits with one tag."""

    form_class = forms.ManyTaggedTraitsForm
    form_invalid_message = TAGGING_MULTIPLE_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'
    permission_required = 'tags.add_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        """Create a TaggedTrait object for each trait given."""
        for trait in form.cleaned_data['traits']:
            tagged_trait = models.TaggedTrait(tag=form.cleaned_data['tag'], trait=trait, creator=self.request.user)
            tagged_trait.full_clean()
            tagged_trait.save()
        # Save the tag object so that you can use it in get_success_url.
        self.tag = form.cleaned_data['tag']
        # Save the traits so you can use them in the form valid message.
        self.traits = list(form.cleaned_data['traits'])
        return super(ManyTaggedTraitsCreate, self).form_valid(form)

    def get_success_url(self):
        return self.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = ''
        for trait in self.traits:
            msg += 'Tag {} has been applied to study variable <a href="{}">{}</a> <br>'.format(
                self.tag.title, trait.get_absolute_url(), trait.i_trait_name)
        return mark_safe(msg)


class ManyTaggedTraitsCreateByTag(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin,
                                  UserFormKwargsMixin, FormMessagesMixin, FormView):
    """Form view class for tagging multiple traits with a specific tag."""

    form_class = forms.ManyTaggedTraitsByTagForm
    form_invalid_message = TAGGING_MULTIPLE_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'
    permission_required = 'tags.add_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(models.Tag, pk=kwargs.get('pk'))
        return super(ManyTaggedTraitsCreateByTag, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Create a TaggedTrait object for each trait given."""
        for trait in form.cleaned_data['traits']:
            tagged_trait = models.TaggedTrait(tag=self.tag, trait=trait, creator=self.request.user)
            tagged_trait.full_clean()
            tagged_trait.save()
        # Save the traits so you can use them in the form valid message.
        self.traits = list(form.cleaned_data['traits'])
        return super(ManyTaggedTraitsCreateByTag, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ManyTaggedTraitsCreateByTag, self).get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

    def get_form_kwargs(self):
        kwargs = super(ManyTaggedTraitsCreateByTag, self).get_form_kwargs()
        kwargs['tag_pk'] = self.kwargs['pk']
        get_object_or_404(models.Tag, pk=kwargs['tag_pk'])
        return kwargs

    def get_success_url(self):
        return self.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = ''
        for trait in self.traits:
            msg += 'Tag {} has been applied to study variable <a href="{}">{}</a> <br>'.format(
                self.tag.title, trait.get_absolute_url(), trait.i_trait_name)
        return mark_safe(msg)


class DCCReviewMixin(object):
    """Mixin to review TaggedTraits and add or update DCCReviews. Must be used with CreateView or UpdateView."""

    model = models.DCCReview

    def get_context_data(self, **kwargs):
        if 'tagged_trait' not in kwargs:
            kwargs['tagged_trait'] = self.tagged_trait
        context = super(DCCReviewMixin, self).get_context_data(**kwargs)
        # Add context variables to control display of tags in _taggedtrait_info panel.
        context['show_other_tags'] = True
        context['other_tags'] = self.tagged_trait.trait.non_archived_tags.all().exclude(pk=self.tagged_trait.tag.pk)
        context['archived_other_tags'] = self.tagged_trait.trait.archived_tags.all()  # Views don't work for archived.
        return context

    def get_review_status(self):
        """Return the DCCReview status based on which submit button was clicked."""
        if self.request.POST:
            if self.form_class.SUBMIT_CONFIRM in self.request.POST:
                return self.model.STATUS_CONFIRMED
            elif self.form_class.SUBMIT_FOLLOWUP in self.request.POST:
                return self.model.STATUS_FOLLOWUP

    def get_form_kwargs(self):
        kwargs = super(DCCReviewMixin, self).get_form_kwargs()
        if 'data' in kwargs:
            tmp = kwargs['data'].copy()
            tmp.update({'status': self.get_review_status()})
            kwargs['data'] = tmp
        return kwargs

    def form_valid(self, form):
        """Create a DCCReview object linked to the given TaggedTrait."""
        form.instance.tagged_trait = self.tagged_trait
        form.instance.creator = self.request.user
        form.instance.status = self.get_review_status()
        return super(DCCReviewMixin, self).form_valid(form)


class DCCReviewByTagAndStudySelect(LoginRequiredMixin, PermissionRequiredMixin, MessageMixin, FormView):
    """Sets session variables from study + tag selection form, then sends to reviewing loop."""

    template_name = 'tags/dccreview_tag_and_study_select.html'
    form_class = forms.DCCReviewTagAndStudySelectForm
    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        # Set session variables for use in the next view.
        study = form.cleaned_data.get('study')
        tag = form.cleaned_data.get('tag')
        qs = models.TaggedTrait.objects.non_archived().unreviewed().filter(
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        review_info = {
            'study_pk': study.pk,
            'tag_pk': tag.pk,
            'tagged_trait_pks': list(qs.values_list('pk', flat=True)),
        }
        # Set a session variable for use in the next view.
        self.request.session['tagged_trait_review_by_tag_and_study_info'] = review_info
        return(super(DCCReviewByTagAndStudySelect, self).form_valid(form))

    def get_success_url(self):
        return reverse('tags:tagged-traits:dcc-review:next')


class DCCReviewByTagAndStudySelectFromURL(LoginRequiredMixin, PermissionRequiredMixin, MessageMixin, RedirectView):
    """View to begin the DCC Reviewing loop using url parameters."""

    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True

    def get(self, request, *args, **kwargs):
        tag = get_object_or_404(models.Tag, pk=self.kwargs['pk'])
        study = get_object_or_404(Study, pk=self.kwargs['pk_study'])
        qs = models.TaggedTrait.objects.non_archived().unreviewed().filter(
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        review_info = {
            'study_pk': study.pk,
            'tag_pk': tag.pk,
            'tagged_trait_pks': list(qs.values_list('pk', flat=True)),
        }
        if qs.count() == 0:
            self.messages.warning('No tagged variables to review for this tag and study.')
        # Set a session variable for use in the next view.
        self.request.session['tagged_trait_review_by_tag_and_study_info'] = review_info
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('tags:tagged-traits:dcc-review:next')


class DCCReviewByTagAndStudyNext(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin, MessageMixin,
                                 RedirectView):
    """Determine the next tagged trait to review and redirect to review page."""

    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True

    def handle_session_variables(self):
        # Check that expected session variables are set.
        if 'tagged_trait_review_by_tag_and_study_info' not in self.request.session:
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:select'))
        # check for required variables.
        required_keys = ('tag_pk', 'study_pk', 'tagged_trait_pks')
        session_info = self.request.session['tagged_trait_review_by_tag_and_study_info']
        for key in required_keys:
            if key not in session_info:
                del self.request.session['tagged_trait_review_by_tag_and_study_info']
                return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:select'))
        # All variables exist; set view attributes.
        self.tag = get_object_or_404(models.Tag, pk=session_info['tag_pk'])
        self.study = get_object_or_404(Study, pk=session_info['study_pk'])
        self.pks = session_info['tagged_trait_pks']

    def _skip_next_tagged_trait(self):
        info = self.request.session['tagged_trait_review_by_tag_and_study_info']
        info['tagged_trait_pks'] = info['tagged_trait_pks'][1:]
        self.request.session['tagged_trait_review_by_tag_and_study_info'] = info

    def get_redirect_url(self, *args, **kwargs):
        """Get the URL to review the next available tagged trait.

        Skip tagged traits that have been archived or deleted since beginning the loop.
        Return the tag-study table URL if all pks have been reviewed.
        """
        info = self.request.session.get('tagged_trait_review_by_tag_and_study_info')
        if info is None:
            # The expected session variable has not been set by the previous
            # view, so redirect to that view.
            return reverse('tags:tagged-traits:dcc-review:select')
        if len(self.pks) > 0:
            # Set the session variable expected by the review view, then redirect.
            pk = self.pks[0]
            # Check to see if the tagged trait has been deleted since starting the loop.
            try:
                tt = models.TaggedTrait.objects.get(pk=pk)
            except ObjectDoesNotExist:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-review:next')
            # Check to see if the tagged trait has been archived since starting the loop.
            if tt.archived:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-review:next')
            # Check to see if the tagged trait has been reviewed since starting the loop.
            elif hasattr(tt, 'dcc_review'):
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-review:next')
            # If you make it this far, set the chosen pk as a session variable to reviewed next.
            info['pk'] = pk
            self.request.session['tagged_trait_review_by_tag_and_study_info'] = info
            # Add a status message.
            msg = ("""You are reviewing variables tagged with <a href="{tag_url}">{tag}</a> """
                   """from study <a href="{study_url}">{study_name}</a>. You have {n_pks} """
                   """tagged variable{s} left to review.""")
            msg = msg.format(
                tag_url=self.tag.get_absolute_url(),
                tag=self.tag.title,
                study_url=self.study.get_absolute_url(),
                study_name=self.study.i_study_name,
                n_pks=len(self.pks),
                s='s' if len(self.pks) > 1 else ''
            )
            self.messages.info(mark_safe(msg))
            return reverse('tags:tagged-traits:dcc-review:review')
        else:
            # All TaggedTraits have been reviewed! Redirect to the tag-study table.
            # Remove session variables related to this group of views.
            tag_pk = info.get('tag_pk')
            study_pk = info.get('study_pk')
            url = reverse('tags:tag:study:list', args=[tag_pk, study_pk])
            del self.request.session['tagged_trait_review_by_tag_and_study_info']
            return url


class DCCReviewByTagAndStudy(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin, DCCReviewMixin,
                             FormValidMessageMixin, CreateView):
    """Create a DCCReview for a tagged trait specified by the pk in a session variable."""

    template_name = 'tags/dccreview_form.html'
    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCReviewByTagAndStudyForm

    def handle_session_variables(self):
        # Check that expected session variables are set.
        if 'tagged_trait_review_by_tag_and_study_info' not in self.request.session:
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:select'))
        # check for required variables.
        required_keys = ('tag_pk', 'study_pk', 'tagged_trait_pks')
        session_info = self.request.session['tagged_trait_review_by_tag_and_study_info']
        for key in required_keys:
            if key not in session_info:
                del self.request.session['tagged_trait_review_by_tag_and_study_info']
                return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:select'))
        # Check for pk
        if 'pk' not in session_info:
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:next'))
        pk = session_info.get('pk')
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=pk)

    def _update_session_variables(self):
        """Update session variables used in this series of views."""
        info = self.request.session['tagged_trait_review_by_tag_and_study_info']
        info['tagged_trait_pks'] = info['tagged_trait_pks'][1:]
        del info['pk']
        self.request.session['tagged_trait_review_by_tag_and_study_info'] = info

    def get_context_data(self, **kwargs):
        context = super(DCCReviewByTagAndStudy, self).get_context_data(**kwargs)
        if 'tag' not in context:
            context['tag'] = self.tagged_trait.tag
        if 'study' not in context:
            context['study'] = self.tagged_trait.trait.source_dataset.source_study_version.study
        if 'n_tagged_traits_remaining' not in context:
            n_remaining = len(self.request.session['tagged_trait_review_by_tag_and_study_info']['tagged_trait_pks'])
            context['n_tagged_traits_remaining'] = n_remaining
        return context

    def post(self, request, *args, **kwargs):
        """Handle skipping, or check for archived or already-reviewed tagged traits before proceeding."""
        if self.form_class.SUBMIT_SKIP in request.POST:
            # Remove the reviewed tagged trait from the list of pks.
            self._update_session_variables()
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:next'))
        # Check if this tagged trait has already been archived.
        if self.tagged_trait.archived:
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it has been archived.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:next'))
        # Check if this tagged trait has already been reviewed.
        elif hasattr(self.tagged_trait, 'dcc_review'):
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it has already been reviewed.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:next'))
        return super(DCCReviewByTagAndStudy, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # Remove the reviewed tagged trait from the list of pks.
        self._update_session_variables()
        return super(DCCReviewByTagAndStudy, self).form_valid(form)

    def get_form_valid_message(self):
        msg = 'Successfully reviewed {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return reverse('tags:tagged-traits:dcc-review:next')


class DCCReviewCreate(LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin, DCCReviewMixin, CreateView):

    template_name = 'tags/dccreview_form.html'
    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCReviewForm

    def _get_already_reviewed_warning_message(self):
        return 'Switched to updating review for {}, because it has already been reviewed.'.format(self.tagged_trait)

    def _get_archived_warning_message(self):
        return 'Oops! Cannot create review for {}, because it has been archived.'.format(self.tagged_trait)

    def _get_warning_response(self, *args, **kwargs):
        """Get the appropriate response for deleted, archived, or already-reviewed tagged traits."""
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=kwargs['pk'])
        # Redirect if the tagged trait has already been archived.
        if self.tagged_trait.archived:
            self.messages.warning(self._get_archived_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Switch to updating the existing review if the tagged trait has already been reviewed.
        elif hasattr(self.tagged_trait, 'dcc_review'):
            self.messages.warning(self._get_already_reviewed_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:update',
                                                args=[self.tagged_trait.pk]))

    def get(self, request, *args, **kwargs):
        check_response = self._get_warning_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        check_response = self._get_warning_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().post(request, *args, **kwargs)

    def get_form_valid_message(self):
        msg = 'Successfully reviewed {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return self.tagged_trait.get_absolute_url()


class DCCReviewUpdate(LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin, DCCReviewMixin, UpdateView):

    template_name = 'tags/dccreview_form.html'
    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCReviewForm

    def _get_dcc_decision_exists_warning_message(self):
        msg = 'Oops! The DCC review for {} cannot be changed because it already has a DCC decision.'.format(
            self.tagged_trait)
        return msg

    def _get_study_response_exists_warning_message(self):
        msg = 'Oops! The DCC review for {} cannot be changed because it already has a study response.'.format(
            self.tagged_trait)
        return msg

    def _get_not_reviewed_warning_message(self):
        return 'Switching to creating a new review for {}, because it has not been reviewed yet.'.format(
            self.tagged_trait)

    def _get_archived_warning_message(self):
        return 'Oops! Cannot update review for {}, because it has been archived.'.format(self.tagged_trait)

    def _get_warning_response(self):
        """Get the appropriate response for archived tagged trait, missing DCCReview, or existing StudyResponse."""
        if self.tagged_trait.archived:
            self.messages.warning(self._get_archived_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        if self.object is None:
            self.messages.warning(self._get_not_reviewed_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))
        if hasattr(self.object, 'study_response'):
            self.messages.error(self._get_study_response_exists_warning_message())
            return HttpResponseRedirect(self.tagged_trait.get_absolute_url())
        if hasattr(self.object, 'dcc_decision'):
            self.messages.error(self._get_dcc_decision_exists_warning_message())
            return HttpResponseRedirect(self.tagged_trait.get_absolute_url())

    def get(self, request, *args, **kwargs):
        """Run get_object, check for archived or deleted tagged trait, and finally run the usual get."""
        # This doesn't use super() directly because the work on check_response needs to happen in the middle of
        # what's done in super().get().
        self.object = self.get_object()
        check_response = self._get_warning_response()
        if check_response is not None:
            return check_response
        # ProcessFormView is the super of the super.
        return ProcessFormView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Run get_object, check for archived or deleted tagged trait, and finally run the usual post."""
        # This doesn't use super() directly because the work on check_response needs to happen in the middle of
        # what's done in super().post().
        self.object = self.get_object()
        check_response = self._get_warning_response()
        if check_response is not None:
            return check_response
        # ProcessFormView is the super of the super.
        return ProcessFormView.post(self, request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get both the tagged trait and its DCC review."""
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=self.kwargs['pk'])
        try:
            obj = self.tagged_trait.dcc_review
            return obj
        except ObjectDoesNotExist:
            return None

    def get_form_valid_message(self):
        msg = 'Successfully updated DCC review for {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return self.tagged_trait.get_absolute_url()


class DCCReviewNeedFollowupCounts(LoginRequiredMixin, TemplateView):
    """View to show counts of DCCReviews that need followup by study and tag for phenotype taggers."""

    template_name = 'tags/taggedtrait_needfollowup_counts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        studies = self.request.user.profile.taggable_studies.all()
        # Note that the Django docs caution against using annotate to add more than one column:
        # https://docs.djangoproject.com/en/1.11/topics/db/aggregation/#combining-multiple-aggregations
        # https://code.djangoproject.com/ticket/10060
        # The problem occurs when a join produces duplicated rows. In the queries below, none of the
        # joins should result in any duplicated TaggedTraits, so multiple annotations should be ok.
        study_tag_counts = models.TaggedTrait.objects.need_followup().exclude(
            # Exclude tagged traits missing a study response but with a dcc decision.
            Q(dcc_review__study_response__isnull=True) & Q(dcc_review__dcc_decision__isnull=False)
        ).filter(
            trait__source_dataset__source_study_version__study__in=studies
        ).values(
            study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('trait__source_dataset__source_study_version__study__i_accession'),
            tag_name=F('tag__title'),
            tag_pk=F('tag__pk')
        ).annotate(
            tt_remaining_count=Sum(Case(
                When(Q(dcc_review__study_response__isnull=True) & Q(dcc_review__tagged_trait__archived=False), then=1),
                When(Q(dcc_review__study_response__isnull=False) | Q(dcc_review__tagged_trait__archived=True), then=0),
                default_value=0,
                output_field=IntegerField()
            ))
        ).annotate(
            tt_completed_count=Sum(Case(
                When(Q(dcc_review__study_response__isnull=False) | Q(dcc_review__tagged_trait__archived=True), then=1),
                When(Q(dcc_review__study_response__isnull=True) & Q(dcc_review__tagged_trait__archived=False), then=0),
                default_value=0,
                output_field=IntegerField()
            ))
        ).values(
            'study_name', 'study_pk', 'tag_name', 'tt_remaining_count', 'tt_completed_count', 'tag_pk'
        ).order_by(
            'study_name', 'tag_name'
        )
        grouped_study_tag_counts = groupby(study_tag_counts,
                                           lambda x: {'study_name': x['study_name'], 'study_pk': x['study_pk']})
        grouped_study_tag_counts = [(key, list(group)) for key, group in grouped_study_tag_counts]
        context['grouped_study_tag_counts'] = grouped_study_tag_counts
        return context

    def get(self, request, *args, **kwargs):
        # Make sure the user is a phenotype tagger and has at least one taggable study.
        n_studies = self.request.user.profile.taggable_studies.count()
        if (self.request.user.groups.filter(name='phenotype_taggers').exists() and n_studies > 0):
            return super().get(request, *args, **kwargs)
        return HttpResponseForbidden()


class DCCReviewNeedFollowupList(LoginRequiredMixin, SpecificTaggableStudyRequiredMixin, SingleTableMixin, ListView):
    """List view of DCCReviews that need study followup."""

    redirect_unauthenticated_users = True
    raise_exception = True
    allow_staff = True
    template_name = 'tags/dccreview_list.html'
    model = models.TaggedTrait
    context_table_name = 'tagged_trait_table'
    context_table_name = 'tagged_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE * 2}

    def get_table_class(self):
        if self.study in self.request.user.profile.taggable_studies.all():
            return tables.DCCReviewTableWithStudyResponseButtons
        else:
            return tables.DCCReviewTable

    def set_study(self):
        self.study = get_object_or_404(Study, pk=self.kwargs['pk_study'])

    def get(self, request, *args, **kwargs):
        self.tag = get_object_or_404(models.Tag, pk=self.kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['study'] = self.study
        context['tag'] = self.tag
        context['show_review_button'] = self.request.user.is_staff
        return context

    def get_table_data(self):
        data = self.study.get_all_tagged_traits().need_followup().exclude(
            # Exclude tagged traits missing a study response but with a dcc decision.
            Q(dcc_review__study_response__isnull=True) & Q(dcc_review__dcc_decision__isnull=False)
        ).filter(
            tag=self.tag
        ).select_related(
            'dcc_review',
            'dcc_review__study_response',
            'tag',
            'trait',
            'trait__source_dataset'
        ).order_by(
            'dcc_review__study_response'
        )
        return data


class StudyResponseCheckMixin(SpecificTaggableStudyRequiredMixin, MessageMixin):
    """Mixin to handle checking that it's appropriate to create or update a StudyResponse."""

    def set_study(self):
        self.study = self.tagged_trait.trait.source_dataset.source_study_version.study

    def get_failure_url(self):
        raise NotImplementedError('Implement get_failure_url when using this mixin.')  # pragma: no cover

    def dispatch(self, request, *args, **kwargs):
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=kwargs['pk'])
        try:
            dcc_review = self.tagged_trait.dcc_review
        except AttributeError:
            self.messages.warning('Oops! {} has not been reviewed by the DCC.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        if self.tagged_trait.archived:
            self.messages.warning('Oops! {} has been removed by the DCC.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        if self.tagged_trait.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            self.messages.warning('Oops! {} has been confirmed by the DCC.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        if hasattr(self.tagged_trait.dcc_review, 'dcc_decision'):
            already_decided_message = """Oops! {} already has a dcc decision so a study response cannot
                                         be created or modified"""
            self.messages.warning(already_decided_message.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        return super().dispatch(request, *args, **kwargs)


class StudyResponseCreateAgree(LoginRequiredMixin, PermissionRequiredMixin, StudyResponseCheckMixin, View):

    http_method_names = ['post', 'put', ]

    permission_required = 'tags.add_studyresponse'
    raise_exception = True
    redirect_unauthenticated_users = True

    def get_failure_url(self):
        study = self.tagged_trait.trait.source_dataset.source_study_version.study
        tag = self.tagged_trait.tag
        return reverse('tags:tag:study:quality-review', args=[tag.pk, study.pk])

    def _create_study_response(self):
        """Create a DCCReview object linked to the given TaggedTrait."""
        study_response = models.StudyResponse(dcc_review=self.tagged_trait.dcc_review, creator=self.request.user,
                                              status=models.StudyResponse.STATUS_AGREE)
        study_response.full_clean()
        study_response.save()
        msg = 'Agreed that {} should be removed.'.format(self.tagged_trait)
        self.messages.success(msg)

    def get_redirect_url(self, *args, **kwargs):
        tag = self.tagged_trait.tag
        study = self.tagged_trait.trait.source_dataset.source_study_version.study
        return reverse('tags:tag:study:quality-review', args=[tag.pk, study.pk])

    def get(self, request, *args, **kwargs):
        if hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self.messages.warning('Oops! {} already has a study response.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Create a StudyResponse with status agree and archive the tagged trait."""
        if hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self.messages.warning('Oops! {} already has a study response.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        self._create_study_response()
        self.tagged_trait.archive()
        return HttpResponseRedirect(self.get_redirect_url())


class StudyResponseCreateDisagree(LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin,
                                  StudyResponseCheckMixin, FormView):

    permission_required = 'tags.add_studyresponse'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.StudyResponseDisagreeForm
    template_name = 'tags/studyresponse_disagree_form.html'
    context_object_name = 'tagged_trait'
    model = models.TaggedTrait

    def get_failure_url(self):
        tag = self.tagged_trait.tag
        study = self.tagged_trait.trait.source_dataset.source_study_version.study
        return reverse('tags:tag:study:quality-review', args=[tag.pk, study.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tagged_trait'] = self.tagged_trait
        return context

    def form_valid(self, form):
        study_response = models.StudyResponse(
            dcc_review=self.tagged_trait.dcc_review,
            creator=self.request.user,
            status=models.StudyResponse.STATUS_DISAGREE,
            comment=form.cleaned_data['comment']
        )
        study_response.full_clean()
        study_response.save()
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self.messages.warning('Oops! {} already has a study response.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self.messages.warning('Oops! {} already has a study response.'.format(self.tagged_trait))
            return HttpResponseRedirect(self.get_failure_url())
        return super().post(request, *args, **kwargs)

    def get_form_valid_message(self):
        msg = 'Explained why {} should not be removed'.format(self.tagged_trait)
        return(msg)

    def get_success_url(self):
        tag = self.tagged_trait.dcc_review.tagged_trait.tag
        study = self.tagged_trait.dcc_review.tagged_trait.trait.source_dataset.source_study_version.study
        return reverse('tags:tag:study:quality-review', args=[tag.pk, study.pk])


class TaggedTraitsNeedDCCDecisionSummary(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """View to show counts of StudyResponses with status disagree by study and tag for DCC staff."""

    template_name = 'tags/taggedtrait_need_dccdecision_summary.html'
    group_required = [u'dcc_analysts', u'dcc_developers', ]
    raise_exception = True
    redirect_unauthenticated_users = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This view only considers tagged traits with study responses of "disagree".
        # Tagged traits without study responses are not included.
        disagree_responses = models.StudyResponse.objects.filter(status=models.StudyResponse.STATUS_DISAGREE).values(
            study_name=F('dcc_review__tagged_trait__trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('dcc_review__tagged_trait__trait__source_dataset__source_study_version__study__i_accession'),
            tag_name=F('dcc_review__tagged_trait__tag__title'),
            tag_pk=F('dcc_review__tagged_trait__tag__pk'),
        ).annotate(
            tt_total=Count('pk'),
            tt_decision_required_count=Sum(Case(
                When(dcc_review__dcc_decision__isnull=True, then=1),
                When(dcc_review__dcc_decision__isnull=False, then=0),
                default_value=0,
                output_field=IntegerField()
            ))
        ).order_by('study_name', 'tag_name')
        grouped_study_tag_counts = groupby(disagree_responses,
                                           lambda x: {'study_name': x['study_name'], 'study_pk': x['study_pk']})
        grouped_study_tag_counts = [(key, list(group)) for key, group in grouped_study_tag_counts]
        context['grouped_study_tag_counts'] = grouped_study_tag_counts
        return context


class TaggedTraitsNeedDCCDecisionByTagAndStudyList(LoginRequiredMixin, GroupRequiredMixin, SingleTableMixin, ListView):
    """View to show list of TaggedTraits that need a DCCDecision, with buttons for deciding."""

    template_name = 'tags/taggedtrait_need_dccdecision_bytagandstudy_list.html'
    group_required = [u'dcc_analysts', u'dcc_developers', ]
    redirect_unauthenticated_users = True
    raise_exception = True
    model = models.TaggedTrait
    context_table_name = 'tagged_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE * 2}
    table_class = tables.TaggedTraitDCCDecisionTable

    def get(self, request, *args, **kwargs):
        self.study = get_object_or_404(Study, pk=self.kwargs['pk_study'])
        self.tag = get_object_or_404(models.Tag, pk=self.kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_table_data(self):
        data = models.TaggedTrait.objects.need_decision().filter(
            dcc_review__tagged_trait__tag=self.tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=self.study).select_related(
                'dcc_review', 'dcc_review__study_response', 'dcc_review__dcc_decision', 'tag', 'trait',
                'trait__source_dataset').order_by(
                    'dcc_review__dcc_decision')
        return data

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['study'] = self.study
        context['tag'] = self.tag
        return context


class DCCDecisionMixin(object):
    """Mixin to create or update DCCDecisions. Must be used with CreateView or UpdateView."""

    model = models.DCCDecision

    def get_context_data(self, **kwargs):
        if 'tagged_trait' not in kwargs:
            kwargs['tagged_trait'] = self.tagged_trait
        context = super(DCCDecisionMixin, self).get_context_data(**kwargs)
        # Add context variables to control display of tags in _taggedtrait_info panel.
        context['show_other_tags'] = True
        context['other_tags'] = self.tagged_trait.trait.non_archived_tags.all().exclude(pk=self.tagged_trait.tag.pk)
        context['archived_other_tags'] = self.tagged_trait.trait.archived_tags.all()  # Views don't work for archived.
        # Set context variables for the quality review panel.
        context['show_dcc_review_add_button'] = False
        context['show_dcc_review_update_button'] = False
        context['show_dcc_review_confirmed'] = False
        context['show_dcc_review_needs_followup'] = True
        context['show_study_response_status'] = hasattr(self.tagged_trait.dcc_review, 'study_response')
        context['show_study_agrees'] = context['show_study_response_status'] and \
            (self.tagged_trait.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE)
        context['show_study_disagrees'] = context['show_study_response_status'] and \
            (self.tagged_trait.dcc_review.study_response.status == models.StudyResponse.STATUS_DISAGREE)
        context['show_dcc_decision'] = hasattr(self.tagged_trait.dcc_review, 'dcc_decision')
        context['show_dcc_decision_add_button'] = False
        context['show_dcc_decision_update_button'] = False
        context['show_decision_remove'] = context['show_dcc_decision'] and \
            (self.tagged_trait.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_REMOVE)
        context['show_decision_confirm'] = context['show_dcc_decision'] and \
            (self.tagged_trait.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_CONFIRM)
        context['show_decision_comment'] = context['show_dcc_decision']
        context['show_delete_button'] = False
        context['show_archived'] = self.tagged_trait.archived
        if context['show_decision_confirm']:
            color = 'bg-success'
        elif context['show_archived']:
            color = 'bg-danger'
        else:
            color = ''
        context['quality_review_panel_color'] = color
        return context

    def get_decision(self):
        """Return the DCCDecision decision based on which submit button was clicked."""
        if self.request.POST:
            if self.form_class.SUBMIT_CONFIRM in self.request.POST:
                return self.model.DECISION_CONFIRM
            elif self.form_class.SUBMIT_REMOVE in self.request.POST:
                return self.model.DECISION_REMOVE

    def get_form_kwargs(self):
        kwargs = super(DCCDecisionMixin, self).get_form_kwargs()
        if 'data' in kwargs:
            tmp = kwargs['data'].copy()
            tmp.update({'decision': self.get_decision()})
            kwargs['data'] = tmp
        return kwargs

    def form_valid(self, form):
        """Create a DCCDecision object linked to the given TaggedTrait."""
        form.instance.dcc_review = self.tagged_trait.dcc_review
        form.instance.creator = self.request.user
        form.instance.decision = self.get_decision()
        response = super().form_valid(form)
        # Archive if necessary.
        if (self.object.decision == models.DCCDecision.DECISION_REMOVE) and (not self.tagged_trait.archived):
            self.tagged_trait.archive()
        # Unarchive if necessary.
        if (self.object.decision == models.DCCDecision.DECISION_CONFIRM) and (self.tagged_trait.archived):
            self.tagged_trait.unarchive()
        return response


class DCCDecisionByTagAndStudySelectFromURL(LoginRequiredMixin, PermissionRequiredMixin, MessageMixin, RedirectView):
    """View to begin the DCC decision loop using url parameters."""

    permission_required = 'tags.add_dccdecision'
    raise_exception = True
    redirect_unauthenticated_users = True

    def get(self, request, *args, **kwargs):
        tag = get_object_or_404(models.Tag, pk=self.kwargs['pk'])
        study = get_object_or_404(Study, pk=self.kwargs['pk_study'])
        disagree_study_responses = models.StudyResponse.objects.filter(
            status=models.StudyResponse.STATUS_DISAGREE,
            dcc_review__tagged_trait__archived=False,
            dcc_review__dcc_decision__isnull=True,
            dcc_review__tagged_trait__tag=tag,
            dcc_review__tagged_trait__trait__source_dataset__source_study_version__study=study
        )
        session_data = {
            'study_pk': study.pk,
            'tag_pk': tag.pk,
            'tagged_trait_pks': list(disagree_study_responses.values_list('dcc_review__tagged_trait__pk', flat=True)),
        }
        if disagree_study_responses.count() == 0:
            self.messages.warning('No tagged variables to decide on for this tag and study.')
        # Set a session variable for use in the next view.
        self.request.session['tagged_trait_decision_by_tag_and_study_info'] = session_data
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('tags:tagged-traits:dcc-decision:next')


class DCCDecisionByTagAndStudyNext(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin, MessageMixin,
                                   RedirectView):
    """Determine the next tagged trait to decide on and redirect to decision-making page."""

    permission_required = 'tags.add_dccdecision'
    raise_exception = True
    redirect_unauthenticated_users = True

    def handle_session_variables(self):
        # Check that expected session variables are set.
        if 'tagged_trait_decision_by_tag_and_study_info' not in self.request.session:
            return HttpResponseRedirect(reverse('tags:tagged-traits:need-decision'))
        # Check for required variables.
        required_keys = ('tag_pk', 'study_pk', 'tagged_trait_pks')
        session_data = self.request.session['tagged_trait_decision_by_tag_and_study_info']
        for key in required_keys:
            if key not in session_data:
                del self.request.session['tagged_trait_decision_by_tag_and_study_info']
                return HttpResponseRedirect(reverse('tags:tagged-traits:need-decision'))
        # All variables exist; set view attributes.
        self.tag = get_object_or_404(models.Tag, pk=session_data['tag_pk'])
        self.study = get_object_or_404(Study, pk=session_data['study_pk'])
        self.pks = session_data['tagged_trait_pks']

    def _skip_next_tagged_trait(self):
        session_data = self.request.session['tagged_trait_decision_by_tag_and_study_info']
        session_data['tagged_trait_pks'] = session_data['tagged_trait_pks'][1:]
        self.request.session['tagged_trait_decision_by_tag_and_study_info'] = session_data

    def get_redirect_url(self, *args, **kwargs):
        """Get the URL to decide on the next available tagged trait.

        Skip tagged traits that have been archived or deleted since beginning the loop.
        Return the tag-study table URL if all pks have been decided on.
        """
        session_data = self.request.session.get('tagged_trait_decision_by_tag_and_study_info')
        if session_data is None:
            # The expected session variable has not been set so redirect to the need decision summary view.
            return reverse('tags:tagged-traits:need-decision')
        if len(self.pks) > 0:
            # Set the session variable expected by the decision view, then redirect.
            pk = self.pks[0]
            # Skip the tagged trait if it has been deleted since starting the loop.
            try:
                tt = models.TaggedTrait.objects.get(pk=pk)
            except ObjectDoesNotExist:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it has been archived since starting the loop.
            if tt.archived:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it has no dcc review.
            elif not hasattr(tt, 'dcc_review'):
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it has a confirmed dcc review.
            elif tt.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it has no study response.
            elif not hasattr(tt.dcc_review, 'study_response'):
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it has an agree study response.
            elif tt.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # Skip the tagged trait if it already has a decision.
            elif hasattr(tt.dcc_review, 'dcc_decision'):
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-decision:next')
            # If you make it past all of the checks, set the chosen pk as a session variable to decide on next.
            session_data['pk'] = pk
            self.request.session['tagged_trait_decision_by_tag_and_study_info'] = session_data
            # Add a status message.
            msg = ("""You are making final decisions for variables tagged with <a href="{tag_url}">{tag}</a> """
                   """from study <a href="{study_url}">{study_name}</a>. You have {n_pks} """
                   """tagged variable{s} left to decide on.""")
            msg = msg.format(
                tag_url=self.tag.get_absolute_url(),
                tag=self.tag.title,
                study_url=self.study.get_absolute_url(),
                study_name=self.study.i_study_name,
                n_pks=len(self.pks),
                s='s' if len(self.pks) > 1 else ''
            )
            self.messages.info(mark_safe(msg))
            return reverse('tags:tagged-traits:dcc-decision:decide')
        else:
            # All TaggedTraits have decisions! Redirect to the tag-study table.
            # Remove session variables related to this group of views.
            tag_pk = session_data.get('tag_pk')
            study_pk = session_data.get('study_pk')
            url = reverse('tags:tag:study:need-decision', args=[tag_pk, study_pk])
            del self.request.session['tagged_trait_decision_by_tag_and_study_info']
            return url


class DCCDecisionByTagAndStudy(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin, DCCDecisionMixin,
                               FormValidMessageMixin, CreateView):
    """Create a DCCDecision for a tagged trait specified by the pk in a session variable."""

    template_name = 'tags/dccdecision_form.html'
    permission_required = 'tags.add_dccdecision'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCDecisionByTagAndStudyForm

    def handle_session_variables(self):
        # Check that expected session variables are set.
        if 'tagged_trait_decision_by_tag_and_study_info' not in self.request.session:
            return HttpResponseRedirect(reverse('tags:tagged-traits:need-decision'))
        # Check for required variables.
        required_keys = ('tag_pk', 'study_pk', 'tagged_trait_pks')
        session_data = self.request.session['tagged_trait_decision_by_tag_and_study_info']
        for key in required_keys:
            if key not in session_data:
                del self.request.session['tagged_trait_decision_by_tag_and_study_info']
                return HttpResponseRedirect(reverse('tags:tagged-traits:need-decision'))
        # Check for pk
        if 'pk' not in session_data:
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        pk = session_data.get('pk')
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=pk)

    def _update_session_variables(self):
        """Update session variables used in this series of views."""
        session_data = self.request.session['tagged_trait_decision_by_tag_and_study_info']
        session_data['tagged_trait_pks'] = session_data['tagged_trait_pks'][1:]
        del session_data['pk']
        self.request.session['tagged_trait_decision_by_tag_and_study_info'] = session_data

    def get_context_data(self, **kwargs):
        context = super(DCCDecisionByTagAndStudy, self).get_context_data(**kwargs)
        if 'tag' not in context:
            context['tag'] = self.tagged_trait.tag
        if 'study' not in context:
            context['study'] = self.tagged_trait.trait.source_dataset.source_study_version.study
        if 'n_tagged_traits_remaining' not in context:
            n_remaining = len(self.request.session['tagged_trait_decision_by_tag_and_study_info']['tagged_trait_pks'])
            context['n_tagged_traits_remaining'] = n_remaining
        return context

    def post(self, request, *args, **kwargs):
        """Handle skipping, or check for archived or already-decided tagged traits before proceeding."""
        if self.form_class.SUBMIT_SKIP in request.POST:
            # Remove the tagged trait from the list of pks.
            self._update_session_variables()
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one is archived.
        if self.tagged_trait.archived:
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it has been archived.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one is missing a dcc review.
        elif not hasattr(self.tagged_trait, 'dcc_review'):
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it is missing a dcc review.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one has a confirmed dcc review.
        elif self.tagged_trait.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because its dcc review status is "confirmed".'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one is missing a study response.
        elif not hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it is missing a study response.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one has an agree study response.
        elif self.tagged_trait.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because its study response status is "agree".'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        # Go to next tagged trait if this one already has a decision.
        elif hasattr(self.tagged_trait.dcc_review, 'dcc_decision'):
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('Skipped {} because it already has a decision made.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-decision:next'))
        return super(DCCDecisionByTagAndStudy, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # Remove the decided tagged trait from the list of pks.
        self._update_session_variables()
        return super().form_valid(form)

    def get_form_valid_message(self):
        msg = 'Successfully made a final decision for {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return reverse('tags:tagged-traits:dcc-decision:next')


class DCCDecisionCreate(LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin, DCCDecisionMixin,
                        CreateView):

    template_name = 'tags/dccdecision_form.html'
    permission_required = 'tags.add_dccdecision'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCDecisionForm

    def _get_archived_warning_message(self):
        return 'Oops! Cannot create decision for {}, because it has been archived.'.format(self.tagged_trait)

    def _get_missing_dcc_review_warning_message(self):
        return 'Oops! Cannot create decision for {}, because it is missing a dcc review.'.format(self.tagged_trait)

    def _get_review_confirmed_warning_message(self):
        return 'Oops! Cannot create decision for {}, because it has a confirmed dcc review.'.format(self.tagged_trait)

    def _get_missing_study_response_warning_message(self):
        return 'Oops! Cannot create decision for {}, because it is missing a study response.'.format(self.tagged_trait)

    def _get_response_agree_warning_message(self):
        return 'Oops! Cannot create decision for {}, because it has an agree study response.'.format(self.tagged_trait)

    def _get_already_decided_warning_message(self):
        return 'Switched to updating decision for {}, because it already has a decision.'.format(self.tagged_trait)

    def _get_warning_response(self, *args, **kwargs):
        """Get the appropriate response for deleted, archived, or already-decisioned tagged traits."""
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=kwargs['pk'])
        # Redirect if the tagged trait has already been archived.
        if self.tagged_trait.archived:
            self.messages.warning(self._get_archived_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait is missing a dcc review.
        elif not hasattr(self.tagged_trait, 'dcc_review'):
            self.messages.warning(self._get_missing_dcc_review_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait has dcc review status confirmed.
        elif self.tagged_trait.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            self.messages.warning(self._get_review_confirmed_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait is missing a study response.
        elif not hasattr(self.tagged_trait.dcc_review, 'study_response'):
            self.messages.warning(self._get_missing_study_response_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait is has study response agree.
        elif self.tagged_trait.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
            self.messages.warning(self._get_response_agree_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Switch to updating the existing decision if the tagged trait already has a decision.
        elif hasattr(self.tagged_trait.dcc_review, 'dcc_decision'):
            self.messages.warning(self._get_already_decided_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-decision:update',
                                                args=[self.tagged_trait.pk]))

    def get(self, request, *args, **kwargs):
        check_response = self._get_warning_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        check_response = self._get_warning_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().post(request, *args, **kwargs)

    def get_form_valid_message(self):
        msg = 'Successfully made final decision for {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return reverse('tags:tag:study:need-decision',
                       args=[self.tagged_trait.tag.pk,
                             self.tagged_trait.trait.source_dataset.source_study_version.study.pk])


class DCCDecisionUpdate(LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin, DCCDecisionMixin,
                        UpdateView):

    template_name = 'tags/dccdecision_form.html'
    permission_required = 'tags.add_dccdecision'
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = forms.DCCDecisionForm

    def _get_missing_decision_warning_message(self):
        return 'Switched to creating a new decision for {}, because it does not have a decision yet.'.format(
            self.tagged_trait)

    def _get_archived_warning_message(self):
        return 'Oops! Cannot update decision for {}, because it has been archived.'.format(self.tagged_trait)

    def _get_missing_dcc_review_warning_message(self):
        return 'Oops! Cannot update decision for {}, because it is missing a dcc review.'.format(self.tagged_trait)

    def _get_review_confirmed_warning_message(self):
        return 'Oops! Cannot update decision for {}, because it has a confirmed dcc review.'.format(self.tagged_trait)

    def _get_response_agree_warning_message(self):
        return 'Oops! Cannot update decision for {}, because it has an agree study response.'.format(self.tagged_trait)

    def _get_warning_response(self):
        """Get the appropriate response unexpected error cases."""
        # Switch to creating a new decision if the tagged trait does not have a decision.
        # This also handles the case where a tagged trait is archived, but has no dcc decision.
        # It will switch to the create view, which will check for archived status.
        if self.object is None:
            self.messages.warning(self._get_missing_decision_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-decision:new', args=[self.tagged_trait.pk]))
        # Redirect if the tagged trait is missing a dcc review.
        elif not hasattr(self.tagged_trait, 'dcc_review'):
            self.messages.warning(self._get_missing_dcc_review_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait has dcc review status confirmed.
        elif self.tagged_trait.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            self.messages.warning(self._get_review_confirmed_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Redirect if the tagged trait has study response agree.
        elif hasattr(self.tagged_trait.dcc_review, 'study_response') and (
                self.tagged_trait.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE):
            self.messages.warning(self._get_response_agree_warning_message())
            return HttpResponseRedirect(self.get_success_url())
        # Omit checks for missing study response. The only important part is that the dcc
        # decision exists to be updated.

    def get(self, request, *args, **kwargs):
        """Run get_object, check for unexpected error cases, and finally run the usual get."""
        # This doesn't use super() directly because the work on check_response needs to happen in the middle of
        # what's done in super().get().
        self.object = self.get_object()
        check_response = self._get_warning_response()
        if check_response is not None:
            return check_response
        # ProcessFormView is the super of the super.
        return ProcessFormView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Run get_object, check for unexpected error cases, and finally run the usual post."""
        # This doesn't use super() directly because the work on check_response needs to happen in the middle of
        # what's done in super().post().
        self.object = self.get_object()
        check_response = self._get_warning_response()
        if check_response is not None:
            return check_response
        # ProcessFormView is the super of the super.
        return ProcessFormView.post(self, request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get both the tagged trait and its DCC decision."""
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=self.kwargs['pk'])
        try:
            obj = self.tagged_trait.dcc_review.dcc_decision
            return obj
        except ObjectDoesNotExist:
            return None

    def get_form_valid_message(self):
        msg = 'Successfully updated final decision for {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return reverse('tags:tag:study:need-decision',
                       args=[self.tagged_trait.tag.pk,
                             self.tagged_trait.trait.source_dataset.source_study_version.study.pk])
