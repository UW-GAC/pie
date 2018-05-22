"""View functions and classes for the tags app."""

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, DeleteView, FormView, ListView, RedirectView, TemplateView

from braces.views import (FormMessagesMixin, FormValidMessageMixin, LoginRequiredMixin, PermissionRequiredMixin,
                          UserFormKwargsMixin, UserPassesTestMixin)
from dal import autocomplete
from django_tables2 import SingleTableMixin

from trait_browser.models import Study
from trait_browser.tables import SourceTraitTableFull
from . import forms
from . import models
from . import tables


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.
TAGGING_ERROR_MESSAGE = 'Oops! Applying the tag to a dbGaP phenotype variable failed.'
TAGGING_MULTIPLE_ERROR_MESSAGE = 'Oops! Applying the tag to dbGaP phenotype variables failed.'


class TagDetail(LoginRequiredMixin, SingleTableMixin, DetailView):
    """Detail view class for Tag."""

    model = models.Tag
    context_object_name = 'tag'
    template_name = 'tags/tag_detail.html'
    table_class = SourceTraitTableFull
    context_table_name = 'tagged_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}


    def get_table_data(self):
        return self.object.traits.all()

    def get_context_data(self, **kwargs):
        context = super(TagDetail, self).get_context_data(**kwargs)
        # study_counts = self.object.traits.values(
        #     'source_dataset__source_study_version__study').annotate(
        #     total=Count('source_dataset__source_study_version__study')).order_by()
        # study_names = [get_object_or_404(Study, pk=d['source_dataset__source_study_version__study']).i_study_name
        #                for d in study_counts]
        # totals = [d['total'] for d in study_counts]
        # context['study_counts'] = zip(study_names, totals)
        return context


class TagList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Tag
    table_class = tables.TagTable
    context_table_name = 'tag_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}


class StudyTaggedTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = Study
    table_class = tables.StudyTaggedTraitTable
    context_table_name = 'study_table'
    template_name = 'tags/studytaggedtrait_list.html'
    table_pagination = {'per_page': TABLE_PER_PAGE}


class TaggedTraitDetail(LoginRequiredMixin, DetailView):

    model = models.TaggedTrait
    context_object_name = 'tagged_trait'
    template_name = 'tags/taggedtrait_detail.html'

    def get_context_data(self, **kwargs):
        context = super(TaggedTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        context['user_is_study_tagger'] = self.object.trait.source_dataset.source_study_version.study in user_studies
        return context


class TaggedTraitByStudyList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.TaggedTrait
    context_table_name = 'tagged_trait_table'
    template_name = 'tags/taggedtrait_list.html'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_class(self):
        """Determine whether to use tagged trait table with delete buttons or not."""
        self.study = get_object_or_404(Study, pk=self.kwargs['pk'])
        if self.request.user.is_staff or (self.request.user.groups.filter(name='phenotype_taggers').exists() and (
                                          self.study in self.request.user.profile.taggable_studies.all())):
            return tables.TaggedTraitTableWithDelete
        else:
            return tables.TaggedTraitTable

    def get_table_data(self):
        return self.study.get_tagged_traits()

    def get_context_data(self, *args, **kwargs):
        context = super(TaggedTraitByStudyList, self).get_context_data(*args, **kwargs)
        context['study'] = self.study
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
        if self.request.user.is_staff or (self.request.user.groups.filter(name='phenotype_taggers').exists() and (
                                          self.study in self.request.user.profile.taggable_studies.all())):
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


class TaggedTraitDelete(LoginRequiredMixin, PermissionRequiredMixin, TaggableStudiesRequiredMixin, FormMessagesMixin,
                        DeleteView):
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
        msg = 'Tag <a href="{}">{}</a> has been removed from dbGaP phenotype variable <a href="{}">{}</a>'.format(
            self.object.tag.get_absolute_url(), self.object.tag.title,
            self.object.trait.get_absolute_url(), self.object.trait.i_trait_name)
        return mark_safe(msg)


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
        msg = 'Tag {} has been applied to dbGaP phenotype variable <a href="{}">{}</a>'.format(
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
        msg = 'Tag {} has been applied to dbGaP phenotype variable <a href="{}">{}</a>'.format(
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
            msg += 'Tag {} has been applied to dbGaP phenotype variable <a href="{}">{}</a> <br>'.format(
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
            msg += 'Tag {} has been applied to dbGaP phenotype variable <a href="{}">{}</a> <br>'.format(
                self.tag.title, trait.get_absolute_url(), trait.i_trait_name)
        return mark_safe(msg)


class TaggedTraitReviewMixin(object):
    """Mixin to review TaggedTraits and add or update DCCReviews. Must be used with CreateView or UpdateView."""

    model = models.DCCReview
    form_class = forms.DCCReviewForm

    def get_context_data(self, **kwargs):
        if 'tagged_trait' not in kwargs:
            kwargs['tagged_trait'] = self.tagged_trait
        return super(TaggedTraitReviewMixin, self).get_context_data(**kwargs)

    def get_review_status(self):
        """Return the DCCReview status based on which submit button was clicked."""
        if self.request.POST:
            if 'confirm' in self.request.POST:
                return models.DCCReview.STATUS_CONFIRMED
            elif 'require-followup' in self.request.POST:
                return models.DCCReview.STATUS_FOLLOWUP

    def get_form_kwargs(self):
        kwargs = super(TaggedTraitReviewMixin, self).get_form_kwargs()
        if 'data' in kwargs:
            tmp = kwargs['data'].copy()
            tmp.update({'status': self.get_review_status()})
            kwargs['data'] = tmp
        return kwargs

    def form_valid(self, form):
        """Create a DCCReview object linked to the given TaggedTrait."""
        dcc_review = models.DCCReview(tagged_trait=self.tagged_trait)
        form.instance.tagged_trait = self.tagged_trait
        form.instance.creator = self.request.user
        form.instance.status = self.get_review_status()
        return super(TaggedTraitReviewMixin, self).form_valid(form)


class TaggedTraitReviewByTagAndStudySelect(LoginRequiredMixin, FormView):

    template_name = 'tags/taggedtrait_review_select.html'
    form_class = forms.TaggedTraitReviewSelectForm

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
        return(super(TaggedTraitReviewByTagAndStudySelect, self).form_valid(form))

    def get_success_url(self):
        return reverse('tags:tagged-traits:review:next')


class TaggedTraitReviewByTagAndStudyNext(LoginRequiredMixin, RedirectView):
    """Determine the next tagged trait to review and redirect to review page."""

    def get_redirect_url(self, *args, **kwargs):
        info = self.request.session.get('tagged_trait_review_by_tag_and_study_info')
        if info is None:
            # The expected session variable has not been set by the previous
            # view, so redirect to that view.
            return reverse('tags:tagged-traits:review:select')
        pks = info.get('tagged_trait_pks')
        if len(pks) > 0:
            # Set the session variable expected by the review view, then redirect.
            info['pk'] = pks[0]
            self.request.session['tagged_trait_review_by_tag_and_study_info'] = info
            return reverse('tags:tagged-traits:review:review')
        else:
            # All TaggedTraits have been reviewed! Redirect to the tag-study table.
            # Remove session variables related to this group of views.
            tag_pk = info.get('tag_pk')
            study_pk = info.get('study_pk')
            url = reverse('tags:tag:study:list', args=[tag_pk, study_pk])
            del self.request.session['tagged_trait_review_by_tag_and_study_info']
            return url


class TaggedTraitReviewByTagAndStudy(LoginRequiredMixin, TaggedTraitReviewMixin, FormValidMessageMixin, CreateView):

    template_name = 'tags/dccreview_form.html'

    def dispatch(self, request, *args, **kwargs):
        info = request.session.get('tagged_trait_review_by_tag_and_study_info')
        pk = info.get('pk')
        self.tagged_trait = get_object_or_404(models.TaggedTrait, pk=pk)
        return super(TaggedTraitReviewByTagAndStudy, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if forms.DCCReviewForm.SUBMIT_SKIP in request.POST:
            # Remove the reviewed tagged trait from the list of pks.
            info = request.session['tagged_trait_review_by_tag_and_study_info']
            info['tagged_trait_pks'] = info['tagged_trait_pks'][1:]
            # The view no longer needs the pk, since the form was valid.
            del info['pk']
            request.session['tagged_trait_review_by_tag_and_study_info'] = info
            return HttpResponseRedirect(reverse('tags:tagged-traits:review:next'))
        return super(TaggedTraitReviewByTagAndStudy, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # Remove the reviewed tagged trait from the list of pks.
        info = self.request.session['tagged_trait_review_by_tag_and_study_info']
        info['tagged_trait_pks'] = info['tagged_trait_pks'][1:]
        # The view no longer needs the pk, since the form was valid.
        del info['pk']
        self.request.session['tagged_trait_review_by_tag_and_study_info'] = info
        return super(TaggedTraitReviewByTagAndStudy, self).form_valid(form)

    def get_form_valid_message(self):
        msg = 'Successfully reviewed {}.'.format(self.tagged_trait)
        return msg

    def get_success_url(self):
        return reverse('tags:tagged-traits:review:next')


class TagAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for autocompleting tag model choice fields by title in a form. Case-insensitive."""

    def get_queryset(self):
        retrieved = models.Tag.objects.all()
        if self.q:
            retrieved = retrieved.filter(lower_title__iregex=r'^{}'.format(self.q))
        return retrieved
