"""View functions and classes for the trait_browser app."""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import pluralize    # Use pluralize in the views.
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin

from braces.views import (FormMessagesMixin, LoginRequiredMixin, MessageMixin, PermissionRequiredMixin,
                          UserPassesTestMixin)
from dal import autocomplete
from django_tables2 import SingleTableMixin, SingleTableView

from tags.forms import TagSpecificTraitForm
from tags.models import TaggedTrait
from tags.views import TAGGING_ERROR_MESSAGE, TaggableStudiesRequiredMixin

from . import forms
from . import models
from . import searches
from . import tables


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.


class SearchFormMixin(FormMixin):
    """Mixin to run a django-watson search for a view."""

    def get_form_kwargs(self):
        """Override method such that form kwargs are obtained from the get request."""
        kwargs = {}
        if self.request.GET:
            kwargs.update({
                'data': self.request.GET
            })
        return kwargs

    def get(self, request, *args, **kwargs):
        """Override get method for form and search processing."""
        if 'reset' in self.request.GET:
            # Instantiate a blank form, ignoring any current GET parameters.
            form_class = self.get_form_class()
            return HttpResponseRedirect(request.path, {'form': form_class()})
        # Process the form.
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def search(self, **search_kwargs):
        """Define a search method to be implemented by Views using this Mixin."""
        # Ensure that View classes implement their own search method by raising an exception.
        raise NotImplementedError  # pragma: no cover

    def form_valid(self, form):
        """Override form_valid method to process form and add results to the search page."""
        self.table_data = self.search(**form.cleaned_data)
        context = self.get_context_data(form=form)
        context['has_results'] = True
        # Add WatsonSearchField warning messages.
        for field in form.fields:
            try:
                if form.fields[field].warning_message:
                    self.messages.warning(form.fields[field].warning_message, fail_silently=True)
            except AttributeError:
                # If the field doesn't have a warning_message, then no message should be displayed.
                pass
        # Add an informational message about the number of results found.
        msg = '{n} result{s} found.'.format(
            n=self.table_data.count(),
            s=pluralize(self.table_data.count()))
        self.messages.info(msg, fail_silently=True)
        return self.render_to_response(context)

    def form_invalid(self, form):
        """Override form_valid method to process form and redirect to the search page."""
        context = self.get_context_data(form=form)
        context['has_results'] = False
        return self.render_to_response(context)


class StudyDetail(LoginRequiredMixin, DetailView):

    model = models.Study
    context_object_name = 'study'

    def get_context_data(self, **kwargs):
        context = super(StudyDetail, self).get_context_data(**kwargs)
        traits = models.SourceTrait.objects.current().filter(source_dataset__source_study_version__study=self.object)
        trait_count = traits.count()
        dataset_count = models.SourceDataset.objects.current().filter(source_study_version__study=self.object).count()
        context['trait_count'] = '{:,}'.format(trait_count)
        context['dataset_count'] = '{:,}'.format(dataset_count)
        return context


class StudyList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Study
    table_class = tables.StudyTable
    context_table_name = 'study_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}


class StudyNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete studies in a form field by i_study_name."""

    def get_queryset(self):
        retrieved = models.Study.objects.all()
        if self.q:
            retrieved = retrieved.filter(i_study_name__icontains=r'{}'.format(self.q))
        return retrieved


class StudyPHSAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete studies in a form field by phs string."""

    def get_queryset(self):
        retrieved = models.Study.objects.all()
        if self.q:
            # User can input a phs in several ways, e.g. 'phs597', '597', '000597', or 'phs000597'.
            # Get rid of the phs.
            phs_digits = self.q.replace('phs', '')
            # Search against the phs string if user started the query with leading zeros.
            if phs_digits.startswith('0'):
                retrieved = retrieved.filter(phs__regex=r'^{}'.format('phs' + phs_digits))
            # Search against the phs digits if user started the query with non-zero digits.
            else:
                retrieved = retrieved.filter(i_accession__regex=r'^{}'.format(phs_digits))
        return retrieved


class StudyNameOrPHSAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete studies in a form field by phs string.

    Accepts two forwarded values: "tag_pk" (to filter to studies with at least
    one trait tagged with the given tag) and "unreviewed_non_archived_tagged_traits_only"
    (requires these tagged traits to be unreviewed and non-archived).
    """

    def get_queryset(self):
        retrieved = models.Study.objects.all()
        if self.q:
            q_no_phs = self.q.replace('phs', '')
            # Study name should always be queried.
            nameQ = Q(i_study_name__icontains=self.q)
            # Process query for pht string.
            phsQ = None
            if self.q.lower().startswith('phs') and q_no_phs.isdigit():
                if q_no_phs.startswith('0'):
                    phsQ = Q(phs__regex=r'^{}'.format('phs' + q_no_phs))
                else:
                    phsQ = Q(i_accession__regex=r'^{}'.format(q_no_phs))
            # Autocomplete using formatted phs if q is only digits.
            # None of the study names should be all digits.
            elif self.q.isdigit():
                # Search against the pht string if user started the query with leading zeros.
                if q_no_phs.startswith('0'):
                    phsQ = Q(phs__regex=r'^{}'.format('phs' + q_no_phs))
                # Search against the phs digits if user started the query with non-zero digits.
                else:
                    phsQ = Q(i_accession__regex=r'^{}'.format(q_no_phs))
            if phsQ:
                retrieved = retrieved.filter(nameQ | phsQ)
            else:
                retrieved = retrieved.filter(nameQ)
        # Add filtering for studies traits tagged with a specific tag, using data forwarded from a form.
        tag_pk = self.forwarded.get('tag', None)
        unreviewed_non_archived = self.forwarded.get('unreviewed_non_archived_tagged_traits_only', False)
        # tag_pk is a string, so "is not None" is not needed.
        if tag_pk:
            tagged_traits = TaggedTrait.objects.all()
            if unreviewed_non_archived:
                tagged_traits = tagged_traits.unreviewed().non_archived()
            studies_with_tag = tagged_traits.filter(
                tag__pk=tag_pk
            ).values_list('trait__source_dataset__source_study_version__study', flat=True).distinct()
            retrieved = retrieved.filter(pk__in=studies_with_tag)
        return retrieved


class SourceDatasetDetail(LoginRequiredMixin, SingleTableMixin, DetailView):
    """Detail view class for SourceDatasets. Displays the dataset's source traits in a table."""

    model = models.SourceDataset
    context_object_name = 'source_dataset'
    context_table_name = 'trait_table'
    table_class = tables.SourceTraitDatasetTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return self.object.sourcetrait_set.all().order_by('i_dbgap_variable_accession')

    def get_context_data(self, **kwargs):
        context = super(SourceDatasetDetail, self).get_context_data(**kwargs)
        trait = self.object.sourcetrait_set.first()
        is_deprecated = self.object.source_study_version.i_is_deprecated
        context['trait_count'] = '{:,}'.format(self.object.sourcetrait_set.count())
        context['show_deprecated_message'] = is_deprecated
        if is_deprecated:
            current_version = self.object.get_current_version()
            if current_version is not None:
                msg = """There is a newer version of this study dataset available:
                         <a class="alert-link" href="{}">{}</a>.""".format(
                    current_version.get_absolute_url(),
                    current_version.dataset_name
                )
                context['deprecation_message'] = mark_safe(msg)
            else:
                msg = """This dataset was removed from the most recent study version."""
                context['deprecation_message'] = msg
        return context


class SourceDatasetList(LoginRequiredMixin, SingleTableView):
    """List view class for SourceDatasets (unfiltered)."""

    model = models.SourceDataset
    context_table_name = 'source_dataset_table'
    table_class = tables.SourceDatasetTableFull
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceDataset.objects.current().select_related(
            'source_study_version__study'
        )


class StudySourceDatasetList(SingleTableMixin, StudyDetail):
    """."""

    template_name = 'trait_browser/study_sourcedataset_list.html'
    context_table_name = 'source_dataset_table'
    table_class = tables.SourceDatasetTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceDataset.objects.current().filter(
            source_study_version__study=self.object)


class SourceDatasetSearch(LoginRequiredMixin, SearchFormMixin, SingleTableMixin, MessageMixin, TemplateView):
    """Class for searching source datasets."""

    template_name = 'trait_browser/sourcedataset_search.html'
    form_class = forms.SourceDatasetSearchMultipleStudiesForm
    table_class = tables.SourceDatasetTableFull
    context_table_name = 'results_table'
    table_data = models.SourceDataset.objects.none()

    def search(self, name='', description='', match_exact_name=True, studies=[]):
        return searches.search_source_datasets(
            name=name,
            description=description,
            match_exact_name=match_exact_name,
            studies=studies
        ).select_related(
            'source_study_version__study'
        )


class StudySourceDatasetSearch(LoginRequiredMixin, SearchFormMixin, SingleObjectMixin, SingleTableMixin, MessageMixin,
                               TemplateView):
    """Class for searching source datasets within a specific study."""

    template_name = 'trait_browser/study_sourcedataset_search.html'
    form_class = forms.SourceDatasetSearchForm
    table_class = tables.SourceDatasetTableFull
    context_table_name = 'results_table'
    table_data = models.SourceDataset.objects.none()
    context_object_name = 'study'
    model = models.Study

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(StudySourceDatasetSearch, self).get(request, *args, **kwargs)

    def search(self, name='', description='', match_exact_name=True):
        return searches.search_source_datasets(
            name=name,
            description=description,
            match_exact_name=match_exact_name,
            studies=[self.object.pk]
        ).select_related(
            'source_study_version',
            'source_study_version__study'
        )


class SourceDatasetNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete datasets in a form field by dataset_name."""

    def get_queryset(self):
        retrieved = models.SourceDataset.objects.current()
        if self.q:
            retrieved = retrieved.filter(dataset_name__icontains=r'{}'.format(self.q))
        return retrieved


class StudySourceDatasetNameAutocomplete(SourceDatasetNameAutocomplete):
    """Auto-complete datasets begloning to a specific study in a form field by dataset_name."""

    def get_queryset(self):
        retrieved = super(StudySourceDatasetNameAutocomplete, self).get_queryset()
        retrieved = retrieved.filter(
            source_study_version__study=self.kwargs['pk']
        )
        return retrieved


class SourceDatasetPHTAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete datasets in a form field by dataset pht string."""

    def get_queryset(self):
        retrieved = models.SourceDataset.objects.current()
        if self.q:
            # User can input a pht in several ways, e.g. 'pht597', '597', '000597', or 'pht000597'.
            # Get rid of the pht.
            pht_digits = self.q.replace('pht', '')
            # Search against the phv string if user started the query with leading zeros.
            if pht_digits.startswith('0'):
                retrieved = retrieved.filter(full_accession__regex=r'^{}'.format('pht' + pht_digits))
            # Search against the pht digits if user started the query with non-zero digits.
            else:
                retrieved = retrieved.filter(i_accession__regex=r'^{}'.format(pht_digits))
        return retrieved


class StudySourceDatasetPHTAutocomplete(SourceDatasetPHTAutocomplete):
    """Auto-complete datasets belonging to a specific study in a form field by dataset pht string."""

    def get_queryset(self):
        retrieved = super(StudySourceDatasetPHTAutocomplete, self).get_queryset()
        retrieved = retrieved.filter(
            source_study_version__study=self.kwargs['pk']
        )
        return retrieved


class SourceDatasetNameOrPHTAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete datasets in a form field by dataset name OR pht string."""

    def get_queryset(self):
        retrieved = models.SourceDataset.objects.current()
        if self.q:
            q_no_pht = self.q.replace('pht', '')
            # Dataset name should always be queried.
            nameQ = Q(dataset_name__icontains=self.q)
            # Process query for pht string.
            phtQ = None
            if self.q.lower().startswith('pht') and q_no_pht.isdigit():
                if q_no_pht.startswith('0'):
                    phtQ = Q(full_accession__regex=r'^{}'.format('pht' + q_no_pht))
                else:
                    phtQ = Q(i_accession__regex=r'^{}'.format(q_no_pht))
            # Autocomplete using formatted pht if q is only digits.
            # Checked that none of the dataset names are all digits (as of 03/21/2018).
            elif self.q.isdigit():
                # Search against the pht string if user started the query with leading zeros.
                if q_no_pht.startswith('0'):
                    phtQ = Q(full_accession__regex=r'^{}'.format('pht' + q_no_pht))
                # Search against the pht digits if user started the query with non-zero digits.
                else:
                    phtQ = Q(i_accession__regex=r'^{}'.format(q_no_pht))
            if phtQ:
                retrieved = retrieved.filter(nameQ | phtQ)
            else:
                retrieved = retrieved.filter(nameQ)
        return retrieved


class StudySourceDatasetNameOrPHTAutocomplete(SourceDatasetNameOrPHTAutocomplete):
    """Auto-complete datasets belonging to a specific study in a form field by dataset name OR pht string."""

    def get_queryset(self):
        retrieved = super(StudySourceDatasetNameOrPHTAutocomplete, self).get_queryset()
        retrieved = retrieved.filter(
            source_study_version__study=self.kwargs['pk']
        )
        return retrieved


class SourceTraitDetail(LoginRequiredMixin, DetailView):
    """Detail view class for SourceTraits. Inherits from django.views.generic.DetailView."""

    model = models.SourceTrait
    context_object_name = 'source_trait'

    def get_context_data(self, **kwargs):
        is_deprecated = self.object.source_dataset.source_study_version.i_is_deprecated
        context = super(SourceTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        context['user_is_study_tagger'] = self.object.source_dataset.source_study_version.study in user_studies
        context['show_tag_button'] = (context['user_is_study_tagger'] or self.request.user.is_staff) and \
            not is_deprecated
        tagged_traits = self.object.all_taggedtraits.non_archived().order_by('tag__lower_title')
        # If tagging is allowed, check on whether to show the delete button for each tag.
        if context['show_tag_button']:
            show_delete_buttons = []
            for tt in tagged_traits:
                try:
                    tt.dcc_review
                    show_delete_buttons.append(False)
                except ObjectDoesNotExist:
                    show_delete_buttons.append(True)
        # Don't show the delete button to anyone if tagging is not allowed.
        else:
            show_delete_buttons = [False] * len(tagged_traits)
        context['tagged_traits_with_xs'] = list(zip(tagged_traits, show_delete_buttons))
        context['show_deprecated_message'] = is_deprecated
        if is_deprecated:
            current_version = self.object.get_current_version()
            if current_version is not None:
                msg = """There is a newer version of this study variable available:
                         <a class="alert-link" href="{}">{}</a>.""".format(
                    current_version.get_absolute_url(),
                    current_version.i_trait_name
                )
                context['deprecation_message'] = mark_safe(msg)
            else:
                msg = """This variable was removed from the most recent study version."""
                context['deprecation_message'] = msg
        return context


class SourceTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.SourceTrait
    table_class = tables.SourceTraitTableFull
    context_table_name = 'source_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.current().select_related(
            'source_dataset',
            'source_dataset__source_study_version',
            'source_dataset__source_study_version__study'
        )


class StudySourceTraitList(SingleTableMixin, StudyDetail):
    """."""

    template_name = 'trait_browser/study_sourcetrait_list.html'
    context_table_name = 'source_trait_table'
    table_class = tables.SourceTraitStudyTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study=self.object
        ).select_related(
            'source_dataset',
            'source_dataset__source_study_version',
            'source_dataset__source_study_version__study'
        )


class StudyTaggedTraitList(StudyDetail):

    template_name = 'trait_browser/study_taggedtrait_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(StudyTaggedTraitList, self).get_context_data(*args, **kwargs)
        tag_counts = TaggedTrait.objects.non_archived().filter(
            trait__source_dataset__source_study_version__study=self.object
        ).values(
            tag_name=F('tag__title'),
            tag_pk=F('tag__pk')
        ).annotate(
            tt_count=Count('pk')
        ).values(
            'tag_name', 'tt_count', 'tag_pk').order_by('tag_name')
        context['tag_counts'] = tag_counts
        return context


class SourceTraitTagging(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, FormMessagesMixin,
                         FormView):
    """Form view class for tagging a specific source trait."""

    form_class = TagSpecificTraitForm
    form_invalid_message = TAGGING_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'
    permission_required = 'tags.add_taggedtrait'
    raise_exception = True
    redirect_unauthenticated_users = True

    def dispatch(self, request, *args, **kwargs):
        self.trait = get_object_or_404(models.SourceTrait, pk=kwargs.get('pk'))
        return super(SourceTraitTagging, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SourceTraitTagging, self).get_context_data(**kwargs)
        context['trait'] = self.trait
        return context

    def get_form_kwargs(self):
        kwargs = super(SourceTraitTagging, self).get_form_kwargs()
        kwargs['trait_pk'] = self.kwargs['pk']
        get_object_or_404(models.SourceTrait, pk=kwargs['trait_pk'])
        return kwargs

    def form_valid(self, form):
        """Create a TaggedTrait object for the trait and tag specified."""
        tagged_trait = TaggedTrait(tag=form.cleaned_data['tag'], trait=self.trait, creator=self.request.user)
        tagged_trait.full_clean()
        tagged_trait.save()
        # Save the tag for use in the success url.
        self.tag = form.cleaned_data['tag']
        return super(SourceTraitTagging, self).form_valid(form)

    def test_func(self, user):
        if user.is_staff:
            return True
        else:
            user_studies = list(user.profile.taggable_studies.all())
            return self.trait.source_dataset.source_study_version.study in user_studies

    def _get_deprecated_response(self, *args, **kwargs):
        self.trait = get_object_or_404(models.SourceTrait, pk=kwargs['pk'])
        if self.trait.source_dataset.source_study_version.i_is_deprecated:
            msg = 'Oops! Cannot tag this study variable, because it is not from the most recent study version.'
            self.messages.warning(msg)
            return HttpResponseRedirect(self.trait.get_absolute_url())

    def get(self, request, *args, **kwargs):
        check_response = self._get_deprecated_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        check_response = self._get_deprecated_response(*args, **kwargs)
        if check_response is not None:
            return check_response
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return self.trait.get_absolute_url()

    def get_form_valid_message(self):
        msg = 'Phenotype {} tagged as <a href="{}">{}</a>'.format(
            self.trait.i_trait_name, self.tag.get_absolute_url(), self.tag.title)
        return mark_safe(msg)


class SourceTraitSearch(LoginRequiredMixin, SearchFormMixin, SingleTableMixin, MessageMixin, TemplateView):
    """Form view class for searching for source traits."""

    template_name = 'trait_browser/sourcetrait_search.html'
    form_class = forms.SourceTraitSearchMultipleStudiesForm
    table_class = tables.SourceTraitTableFull
    context_table_name = 'results_table'
    table_data = models.SourceTrait.objects.none()

    def search(self, name='', description='', match_exact_name=False, dataset_name='', dataset_description='',
               dataset_match_exact_name=False, studies=[]):
        extra_kwargs = {}
        if dataset_name or dataset_description or studies:
            extra_kwargs['datasets'] = searches.search_source_datasets(
                name=dataset_name,
                description=dataset_description,
                match_exact_name=dataset_match_exact_name,
                studies=studies
            )
        results = searches.search_source_traits(
            name=name,
            description=description,
            match_exact_name=match_exact_name,
            **extra_kwargs
        ).select_related(
            'source_dataset',
            'source_dataset__source_study_version',
            'source_dataset__source_study_version__study'
        )
        return results


class StudySourceTraitSearch(LoginRequiredMixin, SearchFormMixin, SingleObjectMixin, SingleTableMixin, MessageMixin,
                             TemplateView):
    """Form view class for searching for source traits within a specific study."""

    template_name = 'trait_browser/study_sourcetrait_search.html'
    form_class = forms.SourceTraitSearchOneStudyForm
    table_class = tables.SourceTraitTableFull
    context_table_name = 'results_table'
    table_data = models.SourceTrait.objects.none()
    context_object_name = 'study'
    model = models.Study

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.object, **self.get_form_kwargs())

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'reset' in self.request.GET:
            # Instantiate a blank form, ignoring any current GET parameters.
            form_class = self.get_form_class()
            return HttpResponseRedirect(request.path, {'form': form_class(self.object)})
        return super(StudySourceTraitSearch, self).get(request, *args, **kwargs)

    def search(self, **search_kwargs):
        datasets = search_kwargs.pop('datasets')
        if len(datasets) == 0:
            datasets = searches.search_source_datasets(studies=[self.object.pk])
        results = searches.search_source_traits(datasets=datasets, **search_kwargs).select_related(
            'source_dataset',
            'source_dataset__source_study_version',
            'source_dataset__source_study_version__study'
        )
        return results


class SourceTraitPHVAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete source traits in a form field by i_trait_name."""

    def get_queryset(self):
        retrieved = models.SourceTrait.objects.current()
        if self.q:
            # User can input a phv in several ways, e.g. 'phv597', '597', '00000597', or 'phv00000597'.
            # Get rid of the phv.
            phv_digits = self.q.replace('phv', '')
            # Search against the phv string if user started the query with leading zeros.
            if phv_digits.startswith('0'):
                retrieved = retrieved.filter(full_accession__regex=r'^{}'.format('phv' + phv_digits))
            # Search against the phv digits if user started the query with non-zero digits.
            else:
                retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(phv_digits))
        return retrieved


class TaggableStudyFilteredSourceTraitPHVAutocomplete(LoginRequiredMixin, TaggableStudiesRequiredMixin,
                                                      autocomplete.Select2QuerySetView):
    """Auto-complete source traits in a form field by i_trait_name, with tagging restrictions."""

    raise_exception = True
    redirect_unauthenticated_users = True

    def get_queryset(self):
        if self.request.user.is_staff:
            retrieved = models.SourceTrait.objects.current()
        else:
            studies = self.request.user.profile.taggable_studies.all()
            retrieved = models.SourceTrait.objects.current().filter(
                source_dataset__source_study_version__study__in=list(studies)
            )
        if self.q:
            # User can input a phv in several ways, e.g. 'phv597', '597', '00000597', or 'phv00000597'.
            # Get rid of the phv.
            phv_digits = self.q.replace('phv', '')
            # Search against the phv string if user started the query with leading zeros.
            if phv_digits.startswith('0'):
                retrieved = retrieved.filter(full_accession__regex=r'^{}'.format('phv' + phv_digits))
            # Search against the phv digits if user started the query with non-zero digits.
            else:
                retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(phv_digits))
        return retrieved


class SourceTraitNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete source traits in a form field by i_trait_name."""

    def get_queryset(self):
        retrieved = models.SourceTrait.objects.current()
        if self.q:
            retrieved = retrieved.filter(i_trait_name__iregex=r'^{}'.format(self.q))
        return retrieved


class TaggableStudyFilteredSourceTraitNameAutocomplete(LoginRequiredMixin, TaggableStudiesRequiredMixin,
                                                       autocomplete.Select2QuerySetView):
    """Auto-complete source traits in a form field by i_trait_name, with tagging restrictions."""

    raise_exception = True
    redirect_unauthenticated_users = True

    def get_queryset(self):
        if self.request.user.is_staff:
            retrieved = models.SourceTrait.objects.current()
        else:
            studies = self.request.user.profile.taggable_studies.all()
            retrieved = models.SourceTrait.objects.current().filter(
                source_dataset__source_study_version__study__in=list(studies)
            )
        if self.q:
            retrieved = retrieved.filter(i_trait_name__iregex=r'^{}'.format(self.q))
        return retrieved


class SourceTraitNameOrPHVAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete source traits in a form field by i_trait_name OR phv (with leading zeros or not).

    User can input a phv in several ways, e.g. 'phv597', '597', '00000597', or 'phv00000597'. User can
    also input the trait name. Either one will work.
    """

    def get_queryset(self):
        retrieved = models.SourceTrait.objects.current()
        if self.q:
            q_no_phv = self.q.replace('phv', '')
            # Autocomplete using name AND phv if q fits "phv\d+".
            if self.q.lower().startswith('phv') and q_no_phv.isdigit():
                if q_no_phv.startswith('0'):
                    phvQ = Q(full_accession__regex=r'^{}'.format('phv' + q_no_phv))
                else:
                    phvQ = Q(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
                retrieved = retrieved.filter(phvQ | Q(i_trait_name__iregex=r'^{}'.format(self.q)))
            # Autocomplete using formatted phv if q is only digits.
            # I checked that none of the source trait names are all digits (as of 2/5/2018).
            elif self.q.isdigit():
                # Search against the phv string if user started the query with leading zeros.
                if q_no_phv.startswith('0'):
                    retrieved = retrieved.filter(full_accession__regex=r'^{}'.format('phv' + q_no_phv))
                # Search against the phv digits if user started the query with non-zero digits.
                else:
                    retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
            # Autocomplete using the source trait name in all other cases.
            else:
                retrieved = retrieved.filter(i_trait_name__iregex=r'^{}'.format(self.q))
        return retrieved


class TaggableStudyFilteredSourceTraitNameOrPHVAutocomplete(LoginRequiredMixin, TaggableStudiesRequiredMixin,
                                                            autocomplete.Select2QuerySetView):
    """Autocomplete source traits in form by i_trait_name OR phv (with leading zeros or not) with tag restrictions."""

    raise_exception = True
    redirect_unauthenticated_users = True

    def get_queryset(self):
        if self.request.user.is_staff:
            retrieved = models.SourceTrait.objects.current()
        else:
            studies = self.request.user.profile.taggable_studies.all()
            retrieved = models.SourceTrait.objects.current().filter(
                source_dataset__source_study_version__study__in=list(studies)
            )
        if self.q:
            q_no_phv = self.q.replace('phv', '')
            # Autocomplete using name AND phv if q fits "phv\d+".
            if self.q.lower().startswith('phv') and q_no_phv.isdigit():
                if q_no_phv.startswith('0'):
                    phvQ = Q(full_accession__regex=r'^{}'.format('phv' + q_no_phv))
                else:
                    phvQ = Q(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
                retrieved = retrieved.filter(phvQ | Q(i_trait_name__iregex=r'^{}'.format(self.q)))
            # Autocomplete using formatted phv if q is only digits.
            # I checked that none of the source trait names are all digits (as of 2/5/2018).
            elif self.q.isdigit():
                # Search against the phv string if user started the query with leading zeros.
                if q_no_phv.startswith('0'):
                    retrieved = retrieved.filter(full_accession__regex=r'^{}'.format('phv' + q_no_phv))
                # Search against the phv digits if user started the query with non-zero digits.
                else:
                    retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
            # Autocomplete using the source trait name in all other cases.
            else:
                retrieved = retrieved.filter(i_trait_name__iregex=r'^{}'.format(self.q))
        return retrieved


class SourceObjectLookup(LoginRequiredMixin, FormView):
    """View to allow the user to select the type of object to look up by accession."""

    template_name = 'trait_browser/object_lookup_select.html'
    form_class = forms.SourceObjectLookupForm

    def form_valid(self, form):
        self.form = form
        return super(SourceObjectLookup, self).form_valid(form)

    def get_success_url(self):
        type = self.form.cleaned_data['object_type']
        # Account for pluralization
        if type == 'study':
            type = 'studies'
        else:
            type = type + 's'
        url_string = 'trait_browser:source:{type}:lookup'.format(type=type)
        return reverse(url_string)


class StudyLookup(LoginRequiredMixin, FormView):
    """View to look up a study by dbGaP accession."""

    template_name = 'trait_browser/object_lookup.html'
    form_class = forms.StudyLookupForm

    def get_context_data(self, **kwargs):
        context = super(StudyLookup, self).get_context_data(**kwargs)
        if 'object_type' not in context:
            context['object_type'] = 'study'
        if 'text' not in context:
            context['text'] = mark_safe(('<p>Each study on dbGaP is assigned a unique numeric identifier prefixed by '
                                         'phs. The version of the study is indicated both by a .v# suffix and by a '
                                         '.p# suffix describing the study participant set. An example of a study '
                                         'accession is phs000001.v1.p1.</p>'))
        return context

    def form_valid(self, form, **kwargs):
        self.object = form.cleaned_data['object']
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, **kwargs):
        url = reverse('trait_browser:source:studies:pk:detail', args=[self.object.pk])
        return url


class SourceDatasetLookup(LoginRequiredMixin, FormView):
    """View to look up a dataset by dbGaP accession."""

    template_name = 'trait_browser/object_lookup.html'
    form_class = forms.SourceDatasetLookupForm

    def get_context_data(self, **kwargs):
        context = super(SourceDatasetLookup, self).get_context_data(**kwargs)
        if 'object_type' not in context:
            context['object_type'] = 'dataset'
        if 'text' not in context:
            context['text'] = mark_safe(('<p>Each dataset on dbGaP is assigned a unique numeric identifier prefixed '
                                         'by pht. The version of the dataset is indicated by a .v# suffix. An example '
                                         'of a dataset accession is pht000001.v1.</p>'))
        return context

    def form_valid(self, form, **kwargs):
        self.object = form.cleaned_data['object']
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, **kwargs):
        url = reverse('trait_browser:source:datasets:detail', args=[self.object.pk])
        return url


class SourceTraitLookup(LoginRequiredMixin, FormView):
    """View to look up a trait by dbGaP accession."""

    template_name = 'trait_browser/object_lookup.html'
    form_class = forms.SourceTraitLookupForm

    def get_context_data(self, **kwargs):
        context = super(SourceTraitLookup, self).get_context_data(**kwargs)
        if 'object_type' not in context:
            context['object_type'] = 'variable'
        if 'text' not in context:
            context['text'] = mark_safe(('<p>Each variable on dbGaP is assigned a unique numeric identifier prefixed '
                                         'by phv. The version of the variable is indicated by a .v# suffix. An '
                                         'example of a variable accession is phv00000001.v1.</p>'))
        return context

    def form_valid(self, form, **kwargs):
        self.object = form.cleaned_data['object']
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, **kwargs):
        url = reverse('trait_browser:source:traits:detail', args=[self.object.pk])
        return url


class HarmonizedTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.HarmonizedTrait
    table_class = tables.HarmonizedTraitTable
    context_table_name = 'harmonized_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.HarmonizedTrait.objects.current().non_unique_keys().select_related(
            'harmonized_trait_set_version'
        )


class HarmonizedTraitFlavorNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing HarmonizedTrait form fields with trait_flavor_name.

    Used with django-autocomplete-light package. Autocomplete by trait_flavor_name.
    Only include latest version.
    """

    def get_queryset(self):
        retrieved = models.HarmonizedTrait.objects.current()
        if self.q:
            retrieved = retrieved.filter(trait_flavor_name__iregex=r'^{}'.format(self.q))
        return retrieved


class HarmonizedTraitSearch(LoginRequiredMixin, SearchFormMixin, SingleTableMixin, MessageMixin, TemplateView):
    """Form view class for searching for source traits."""

    template_name = 'trait_browser/harmonizedtrait_search.html'
    form_class = forms.HarmonizedTraitSearchForm
    table_class = tables.HarmonizedTraitTable
    context_table_name = 'results_table'
    table_data = models.HarmonizedTrait.objects.none()

    def search(self, **search_kwargs):
        return searches.search_harmonized_traits(**search_kwargs).select_related(
            'harmonized_trait_set_version'
        )


class HarmonizedTraitSetVersionDetail(LoginRequiredMixin, FormMessagesMixin, DetailView):
    """Detail view class for HarmonizedTraitSetVersions. Inherits from django.views.generic.DetailView."""

    model = models.HarmonizedTraitSetVersion
    context_object_name = 'harmonized_trait_set_version'

    def get_context_data(self, **kwargs):
        context = super(HarmonizedTraitSetVersionDetail, self).get_context_data(**kwargs)
        harmonized_traits = self.object.harmonizedtrait_set.all()
        context['harmonized_trait'] = harmonized_traits.get(i_is_unique_key=False)
        context['unique_keys'] = harmonized_traits.filter(i_is_unique_key=True)
        context['unique_key_names'] = ', '.join(context['unique_keys'].values_list('trait_flavor_name', flat=True))
        return context
