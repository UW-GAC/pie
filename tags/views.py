"""View functions and classes for the tags app."""

from itertools import groupby

from django.db.models import Count, F
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views.generic import CreateView, DetailView, DeleteView, FormView, ListView, TemplateView, UpdateView, RedirectView

from braces.views import (FormMessagesMixin, FormValidMessageMixin, LoginRequiredMixin, MessageMixin,
                          PermissionRequiredMixin, UserFormKwargsMixin, UserPassesTestMixin)
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
REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE = (
    "Oops! Tagged study variables that have been reviewed by the DCC can't be deleted."
)


class TagDetail(LoginRequiredMixin, DetailView):
    """Detail view class for Tag."""

    model = models.Tag
    context_object_name = 'tag'

    def get_table_data(self):
        return self.object.traits.all()

    def get_context_data(self, **kwargs):
        context = super(TagDetail, self).get_context_data(**kwargs)
        study_counts = models.TaggedTrait.objects.filter(tag=self.object).values(
            study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
            study_pk=F('trait__source_dataset__source_study_version__study__pk')
        ).annotate(
            tt_count=Count('pk')
        ).values(
            'study_name', 'study_pk', 'tt_count').order_by('study_name')
        context['study_counts'] = study_counts
        return context


class TagList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Tag
    table_class = tables.TagTable
    context_table_name = 'tag_table'
    table_pagination = {'per_page': TABLE_PER_PAGE * 2}


class TaggedTraitDetail(LoginRequiredMixin, DetailView):

    model = models.TaggedTrait
    context_object_name = 'tagged_trait'
    template_name = 'tags/taggedtrait_detail.html'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        context['user_is_study_tagger'] = self.object.trait.source_dataset.source_study_version.study in user_studies
        # Check if DCCReview info should be shown.
        context['show_dcc_review_info'] = self.request.user.is_staff
        # Check if the review add or update buttons should be shown.
        context['show_dcc_review_add_button'] = (not hasattr(self.object, 'dcc_review')) and \
            self.request.user.has_perm('tags.add_dccreview')
        context['show_dcc_review_update_button'] = hasattr(self.object, 'dcc_review') and \
            self.request.user.has_perm('tags.change_dccreview')
        return context


class TaggedTraitTagCountsByStudy(LoginRequiredMixin, TemplateView):

    template_name = 'tags/taggedtrait_tagcounts_bystudy.html'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitTagCountsByStudy, self).get_context_data(**kwargs)
        annotated_studies = models.TaggedTrait.objects.values(
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
        annotated_tags = models.TaggedTrait.objects.values(
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
        return self.study.get_tagged_traits().filter(tag=self.tag)

    def get_table_class(self):
        """Determine whether to use tagged trait table with delete buttons or not."""
        if self.request.user.is_staff:
            return tables.TaggedTraitTableWithDCCReview
        elif (self.request.user.groups.filter(name='phenotype_taggers').exists() and
              self.study in self.request.user.profile.taggable_studies.all()):
            return tables.TaggedTraitTableWithDelete
        else:
            return tables.TaggedTraitTable

    def get_context_data(self, *args, **kwargs):
        context = super(TaggedTraitByTagAndStudyList, self).get_context_data(*args, **kwargs)
        context['study'] = self.study
        context['tag'] = self.tag
        return context


class TaggableStudiesRequiredMixin(UserPassesTestMixin):
    """Mixin requiring that the user have 1 or more taggable studies designated, or be staff."""

    def test_func(self, user):
        return user.profile.taggable_studies.count() > 0 or user.is_staff


class TaggedTraitDelete(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin,
                        ValidateObjectMixin, FormMessagesMixin, DeleteView):
    """Delete view class for TaggedTrait objects."""

    model = models.TaggedTrait
    context_object_name = 'tagged_trait'
    permission_required = 'tags.delete_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def get_success_url(self):
        return reverse('trait_browser:source:studies:pk:traits:tagged',
                       args=[self.object.trait.source_dataset.source_study_version.study.pk])

    def get_form_valid_message(self):
        msg = 'Tag <a href="{}">{}</a> has been removed from study variable <a href="{}">{}</a>'.format(
            self.object.tag.get_absolute_url(), self.object.tag.title,
            self.object.trait.get_absolute_url(), self.object.trait.i_trait_name)
        return mark_safe(msg)

    def get_validation_failure_url(self):
        return self.get_success_url()

    def validate_object(self):
        if hasattr(self.object, 'dcc_review'):
            self.messages.error(REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE)
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
        return super(DCCReviewMixin, self).get_context_data(**kwargs)

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

    template_name = 'tags/dccreview_tag_and_study_select.html'
    form_class = forms.DCCReviewTagAndStudySelectForm
    permission_required = 'tags.add_dccreview'
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        # Set session variables for use in the next view.
        study = form.cleaned_data.get('study')
        tag = form.cleaned_data.get('tag')
        qs = models.TaggedTrait.objects.unreviewed().filter(
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


class DCCReviewByTagAndStudyNext(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin,
                                         MessageMixin, RedirectView):
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
        info = self.request.session.get('tagged_trait_review_by_tag_and_study_info')
        if info is None:
            # The expected session variable has not been set by the previous
            # view, so redirect to that view.
            return reverse('tags:tagged-traits:dcc-review:select')
        if len(self.pks) > 0:
            # Set the session variable expected by the review view, then redirect.
            pk = self.pks[0]
            try:
                tt = models.TaggedTrait.objects.get(pk=pk)
            except ObjectDoesNotExist:
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-review:next')
            if hasattr(tt, 'dcc_review'):
                self._skip_next_tagged_trait()
                return reverse('tags:tagged-traits:dcc-review:next')
            info['pk'] = pk
            self.request.session['tagged_trait_review_by_tag_and_study_info'] = info
            # Add a message.
            msg = ("""You are reviewing variables tagged with <a href="{tag_url}">{tag}</a> """
                   """from study <a href="{study_url}">{study_name}</a>. You have {n_pks} """
                   """tagged variable{s} left to review.""")
            msg = msg.format(
                tag_url=self.tag.get_absolute_url(),
                tag=self.tag.lower_title,
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


class DCCReviewByTagAndStudy(LoginRequiredMixin, PermissionRequiredMixin, SessionVariableMixin,
                                     DCCReviewMixin, FormValidMessageMixin, CreateView):

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
        if self.form_class.SUBMIT_SKIP in request.POST:
            # Remove the reviewed tagged trait from the list of pks.
            self._update_session_variables()
            return HttpResponseRedirect(reverse('tags:tagged-traits:dcc-review:next'))
        # Check if this trait has already been reviewed.
        if hasattr(self.tagged_trait, 'dcc_review'):
            self._update_session_variables()
            # Add an informational message.
            self.messages.warning('{} has already been reviewed.'.format(self.tagged_trait))
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

    def get(self, request, *args, **kwargs):
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=kwargs['pk'])
        if hasattr(self.tagged_trait, 'dcc_review'):
            self.messages.warning('{} has already been reviewed.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=kwargs['pk'])
        if hasattr(self.tagged_trait, 'dcc_review'):
            self.messages.warning('{} has already been reviewed.'.format(self.tagged_trait))
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:update', args=[self.tagged_trait.pk]))
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

    def _get_already_reviewed_warning_message(self):
        return '{} has not been reviewed yet.'.format(self.tagged_trait)

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except ObjectDoesNotExist:
            self.messages.warning(self._get_already_reviewed_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ObjectDoesNotExist:
            self.messages.warning(self._get_already_reviewed_warning_message())
            return HttpResponseRedirect(reverse('tags:tagged-traits:pk:dcc-review:new', args=[self.tagged_trait.pk]))

    def get_object(self, queryset=None):
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=self.kwargs['pk'])
        obj = self.tagged_trait.dcc_review
        return obj

    def get_form_valid_message(self):
        msg = 'Successfully updated {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return self.tagged_trait.get_absolute_url()


class TagAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for autocompleting tag model choice fields by title in a form. Case-insensitive."""

    def get_queryset(self):
        retrieved = models.Tag.objects.all()
        if self.q:
            retrieved = retrieved.filter(lower_title__iregex=r'^{}'.format(self.q))
        return retrieved
