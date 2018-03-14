"""View functions and classes for the trait_browser app."""

from django.db.models import Q  # Allows complex queries when searching.
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import pluralize    # Use pluralize in the views.
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from django.views.generic.base import TemplateView
from django.template.defaultfilters import pluralize    # Use pluralize in the views.

from braces.views import (FormMessagesMixin, LoginRequiredMixin, MessageMixin, PermissionRequiredMixin,
                          UserPassesTestMixin)
from dal import autocomplete
from django_tables2 import SingleTableMixin, SingleTableView

from tags.forms import TagSpecificTraitForm
from tags.models import Tag, TaggedTrait
from tags.views import TAGGING_ERROR_MESSAGE, TaggableStudiesRequiredMixin
from . import models
from . import tables
from . import forms
from . import searches


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
        raise NotImplementedError

    def form_valid(self, form):
        """Override form_valid method to process form and add results to the search page."""
        self.table_data = self.search(**form.cleaned_data)
        context = self.get_context_data(form=form)
        context['has_results'] = True
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
        traits = models.SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study=self.object)
        trait_count = traits.count()
        dataset_count = models.SourceDataset.objects.current().filter(
            source_study_version__study=self.object).count()
        context['trait_count'] = '{:,}'.format(trait_count)
        context['dataset_count'] = '{:,}'.format(dataset_count)
        context['phs_link'] = traits[0].dbgap_study_link
        context['phs'] = traits[0].study_accession
        return context


class StudyList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Study
    table_class = tables.StudyTable
    context_table_name = 'study_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}


class StudySourceTraitList(LoginRequiredMixin, SingleTableMixin, DetailView):
    """."""

    template_name = 'trait_browser/study_sourcetrait_list.html'
    model = models.Study
    context_object_name = 'study'
    context_table_name = 'source_trait_table'
    table_class = tables.SourceTraitStudyTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study=self.object)

    def get_context_data(self, **kwargs):
        context = super(StudySourceTraitList, self).get_context_data(**kwargs)
        traits = context['source_trait_table'].data
        context['trait_count'] = '{:,}'.format(len(traits))
        context['phs_link'] = traits[0].dbgap_study_link
        context['phs'] = traits[0].study_accession
        return context


class StudySourceDatasetList(LoginRequiredMixin, SingleTableMixin, DetailView):
    """."""

    template_name = 'trait_browser/study_sourcedataset_list.html'
    model = models.Study
    context_object_name = 'study'
    context_table_name = 'source_dataset_table'
    table_class = tables.SourceDatasetTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceDataset.objects.current().filter(
            source_study_version__study=self.object)

    def get_context_data(self, **kwargs):
        context = super(StudySourceDatasetList, self).get_context_data(**kwargs)
        datasets = context['source_dataset_table'].data
        context['dataset_count'] = '{:,}'.format(len(datasets))
        context['phs_link'] = datasets[0].sourcetrait_set.first().dbgap_study_link
        context['phs'] = datasets[0].sourcetrait_set.first().study_accession
        return context


class StudyNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Auto-complete studies in a form field by i_study_name."""

    def get_queryset(self):
        retrieved = models.Study.objects.all()
        if self.q:
            retrieved = retrieved.filter(i_study_name__icontains=r'{}'.format(self.q))
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
        context['phs'] = trait.study_accession
        context['phs_link'] = trait.dbgap_study_link
        context['pht_link'] = trait.dbgap_dataset_link
        context['trait_count'] = '{:,}'.format(self.object.sourcetrait_set.count())
        return context


class SourceDatasetList(LoginRequiredMixin, SingleTableView):
    """List view class for SourceDatasets (unfiltered)."""

    model = models.SourceDataset
    context_table_name = 'source_dataset_table'
    table_class = tables.SourceDatasetTableFull
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceDataset.objects.current()


class HarmonizedTraitSetVersionDetail(LoginRequiredMixin, FormMessagesMixin, DetailView):
    """Detail view class for HarmonizedTraitSetVersions. Inherits from django.views.generic.DetailView."""

    model = models.HarmonizedTraitSetVersion
    context_object_name = 'harmonized_trait_set_version'


class SourceTraitDetail(LoginRequiredMixin, DetailView):
    """Detail view class for SourceTraits. Inherits from django.views.generic.DetailView."""

    model = models.SourceTrait
    context_object_name = 'source_trait'

    def get_context_data(self, **kwargs):
        context = super(SourceTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        context['user_is_study_tagger'] = self.object.source_dataset.source_study_version.study in user_studies
        context['tags'] = list(Tag.objects.filter(traits=self.object))
        return context


class SourceTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.SourceTrait
    table_class = tables.SourceTraitTableFull
    context_table_name = 'source_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.current()


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

    def search(self, **search_kwargs):
        return searches.search_source_traits(**search_kwargs)


class SourceTraitSearchByStudy(LoginRequiredMixin, SearchFormMixin, SingleObjectMixin, SingleTableMixin, MessageMixin, TemplateView):
    """Form view class for searching for source traits within a specific study."""

    template_name = 'trait_browser/study_sourcetrait_search.html'
    form_class = forms.SourceTraitSearchForm
    table_class = tables.SourceTraitTableFull
    context_table_name = 'results_table'
    table_data = models.SourceTrait.objects.none()
    context_object_name = 'study'
    model = models.Study

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(SourceTraitSearchByStudy, self).get(request, *args, **kwargs)

    def search(self, **search_kwargs):
        new_search_kwargs = search_kwargs.copy()
        new_search_kwargs.update({'studies': [self.object.pk]})
        return searches.search_source_traits(**new_search_kwargs)


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
                retrieved = retrieved.filter(variable_accession__regex=r'^{}'.format('phv' + phv_digits))
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
                retrieved = retrieved.filter(variable_accession__regex=r'^{}'.format('phv' + phv_digits))
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
                    phvQ = Q(variable_accession__regex=r'^{}'.format('phv' + q_no_phv))
                else:
                    phvQ = Q(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
                retrieved = retrieved.filter(phvQ | Q(i_trait_name__iregex=r'^{}'.format(self.q)))
            # Autocomplete using formatted phv if q is only digits.
            # I checked that none of the source trait names are all digits (as of 2/5/2018).
            elif self.q.isdigit():
                # Search against the phv string if user started the query with leading zeros.
                if q_no_phv.startswith('0'):
                    retrieved = retrieved.filter(variable_accession__regex=r'^{}'.format('phv' + q_no_phv))
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
                    phvQ = Q(variable_accession__regex=r'^{}'.format('phv' + q_no_phv))
                else:
                    phvQ = Q(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
                retrieved = retrieved.filter(phvQ | Q(i_trait_name__iregex=r'^{}'.format(self.q)))
            # Autocomplete using formatted phv if q is only digits.
            # I checked that none of the source trait names are all digits (as of 2/5/2018).
            elif self.q.isdigit():
                # Search against the phv string if user started the query with leading zeros.
                if q_no_phv.startswith('0'):
                    retrieved = retrieved.filter(variable_accession__regex=r'^{}'.format('phv' + q_no_phv))
                # Search against the phv digits if user started the query with non-zero digits.
                else:
                    retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(q_no_phv))
            # Autocomplete using the source trait name in all other cases.
            else:
                retrieved = retrieved.filter(i_trait_name__iregex=r'^{}'.format(self.q))
        return retrieved


class HarmonizedTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.HarmonizedTrait
    table_class = tables.HarmonizedTraitTable
    context_table_name = 'harmonized_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.HarmonizedTrait.objects.current()


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
        """Override form_valid method to process form and add results to the search page."""
        return searches.search_harmonized_traits(**search_kwargs)
