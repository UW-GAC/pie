"""View functions and classes for the trait_browser app."""

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q    # Allows complex queries when searching.
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, FormView, ListView

from braces.views import FormMessagesMixin, LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from dal import autocomplete
from django_tables2 import RequestConfig, SingleTableMixin, SingleTableView
from urllib.parse import parse_qs

import profiles.models
from tags.forms import TagSpecificTraitForm
from tags.models import Tag, TaggedTrait
from tags.views import TAGGING_ERROR_MESSAGE, TaggableStudiesRequiredMixin
from . import models
from . import tables
from . import forms


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.


class SourceDatasetDetail(LoginRequiredMixin, SingleTableMixin, DetailView):
    """Detail view class for SourceDatasets. Displays the dataset's source traits in a table."""

    template_name = 'trait_browser/source_dataset_detail.html'
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
    table_class = tables.SourceDatasetTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceDataset.objects.exclude(source_study_version__i_is_deprecated=True)


class SourceTraitDetail(LoginRequiredMixin, DetailView):
    """Detail view class for SourceTraits. Inherits from django.views.generic.DetailView."""

    model = models.SourceTrait
    context_object_name = 'source_trait'
    template_name = 'trait_browser/source_trait_detail.html'

    def get_context_data(self, **kwargs):
        context = super(SourceTraitDetail, self).get_context_data(**kwargs)
        user_studies = list(self.request.user.profile.taggable_studies.all())
        context['user_is_study_tagger'] = self.object.source_dataset.source_study_version.study in user_studies
        context['tags'] = list(Tag.objects.filter(traits=self.object))
        return context


class HarmonizedTraitSetVersionDetail(LoginRequiredMixin, FormMessagesMixin, DetailView):
    """Detail view class for HarmonizedTraitSetVersions. Inherits from django.views.generic.DetailView."""

    model = models.HarmonizedTraitSetVersion
    context_object_name = 'harmonized_trait_set_version'
    template_name = 'trait_browser/harmonized_trait_set_version_detail.html'


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


class SourceTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.SourceTrait
    table_class = tables.SourceTraitTableFull
    context_table_name = 'source_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.exclude(source_dataset__source_study_version__i_is_deprecated=True)


class HarmonizedTraitList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.HarmonizedTrait
    table_class = tables.HarmonizedTraitTable
    context_table_name = 'harmonized_trait_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.HarmonizedTrait.objects.exclude(harmonized_trait_set_version__i_is_deprecated=True)


class StudyDetail(LoginRequiredMixin, DetailView):

    model = models.Study
    context_object_name = 'study'

    def get_context_data(self, **kwargs):
        context = super(StudyDetail, self).get_context_data(**kwargs)
        traits = models.SourceTrait.objects.exclude(
            source_dataset__source_study_version__i_is_deprecated=True).filter(
            source_dataset__source_study_version__study=self.object)
        trait_count = traits.count()
        dataset_count = models.SourceDataset.objects.exclude(
            source_study_version__i_is_deprecated=True).filter(
            source_study_version__study=self.object).count()
        context['trait_count'] = '{:,}'.format(trait_count)
        context['dataset_count'] = '{:,}'.format(dataset_count)
        context['phs_link'] = traits[0].dbgap_study_link
        context['phs'] = traits[0].study_accession
        return context


class StudySourceTraitList(LoginRequiredMixin, SingleTableMixin, DetailView):
    """."""

    template_name = 'trait_browser/study_sourcetrait_list.html'
    model = models.Study
    context_object_name = 'study'
    context_table_name = 'source_trait_table'
    table_class = tables.SourceTraitStudyTable
    table_pagination = {'per_page': TABLE_PER_PAGE}

    def get_table_data(self):
        return models.SourceTrait.objects.exclude(
            source_dataset__source_study_version__i_is_deprecated=True).filter(
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
        return models.SourceDataset.objects.exclude(
            source_study_version__i_is_deprecated=True).filter(
            source_study_version__study=self.object)

    def get_context_data(self, **kwargs):
        context = super(StudySourceDatasetList, self).get_context_data(**kwargs)
        datasets = context['source_dataset_table'].data
        context['dataset_count'] = '{:,}'.format(len(datasets))
        context['phs_link'] = datasets[0].sourcetrait_set.first().dbgap_study_link
        context['phs'] = datasets[0].sourcetrait_set.first().study_accession
        return context


class StudyList(LoginRequiredMixin, SingleTableMixin, ListView):

    model = models.Study
    table_class = tables.StudyTable
    context_table_name = 'study_table'
    table_pagination = {'per_page': TABLE_PER_PAGE}


class SourceTraitPHVAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing SourceTrait-based form fields.

    Used with django-autocomplete-light package. Autocomplete by dbGaP accession.
    Only include latest version.
    """

    def get_queryset(self):
        retrieved = models.SourceTrait.objects.filter(source_dataset__source_study_version__i_is_deprecated=False)
        if self.q:
            retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(self.q))
        return retrieved


class TaggableStudyFilteredSourceTraitPHVAutocomplete(LoginRequiredMixin, TaggableStudiesRequiredMixin,
                                                      autocomplete.Select2QuerySetView):
    """View for auto-completing SourceTraits by phv in a specific study.

    Used with django-autocomplete-light package. Autocomplete by dbGaP accession.
    Only include latest version.
    """

    raise_exception = True
    redirect_unauthenticated_users = True

    def get_queryset(self):
        if self.request.user.is_staff:
            retrieved = models.SourceTrait.objects.filter(
                source_dataset__source_study_version__i_is_deprecated=False
            )
        else:
            studies = self.request.user.profile.taggable_studies.all()
            retrieved = models.SourceTrait.objects.filter(
                source_dataset__source_study_version__study__in=list(studies),
                source_dataset__source_study_version__i_is_deprecated=False
            )
        if self.q:
            retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(self.q))
        return retrieved


class HarmonizedTraitFlavorNameAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing HarmonizedTrait form fields with trait_flavor_name.

    Used with django-autocomplete-light package. Autocomplete by trait_flavor_name.
    Only include latest version.
    """

    def get_queryset(self):
        # TODO: Will need to filter to the latest version, once this is implemented.
        retrieved = models.HarmonizedTrait.objects.all()
        if self.q:
            retrieved = retrieved.filter(trait_flavor_name__regex=r'^{}'.format(self.q))
        return retrieved


def search(text_query, trait_type, study_pks=[]):
    """profiles.models.Search either source or (eventually) harmonized traits for a given query.

    Function to search the trait name and trait description for the given query
    text, and possibly filtering to the list of studies specified. The search is
    case-insensitive. Do not include quotes. This is a very simple search.

    Arguments:
        text_query -- string; text to search for within descriptions and names
        trait_type -- string; "source" or "harmonized"
        study_pks -- list of (primary_key, study_name) tuples

    Returns:
        queryset of SourceTrait or HarmonizedTrait objects
    """
    # TODO: add try/except to catch invalid trait_type values.
    if trait_type == 'source':
        if (len(study_pks) == 0):
            traits = models.SourceTrait.objects.all()
        # Filter by study.
        else:
            traits = models.SourceTrait.objects.filter(source_dataset__source_study_version__study__pk__in=study_pks)
        # Then exclude deprecated study versions and search text.
        traits = traits.exclude(source_dataset__source_study_version__i_is_deprecated=True).filter(
            Q(i_description__contains=text_query) | Q(i_trait_name__contains=text_query))
    elif trait_type == 'harmonized':
        traits = models.HarmonizedTrait.objects.filter(
            Q(i_description__contains=text_query) | Q(i_trait_name__contains=text_query))
    return(traits)


@login_required
def trait_search(request, trait_type):
    """Trait search form view.

    Displays the SourceTraitCrispySearchForm or HarmonizedTraitCrispySearchForm
    and any search results as a django-tables2 table view.
    """
    # Create a form instance with data from the request.
    FormClass = forms.SourceTraitCrispySearchForm if trait_type == 'source' else forms.HarmonizedTraitCrispySearchForm
    form = FormClass(request.GET)
    if trait_type == 'source':
        trait_type_name = 'study'
    else:
        trait_type_name = trait_type
    page_data = {'form': form, 'trait_type': trait_type, 'trait_type_name': trait_type_name, }
    # If there was no data entered, show the empty form.
    if request.GET.get('text', None) is None:
        form = FormClass()
        if trait_type == 'source':
            if request.GET.get('study', None) is not None:
                form = FormClass(initial=request.GET)
        page_data['form'] = form
        page_data['results'] = False
        return render(request, 'trait_browser/search.html', page_data)
    # If the form data is valid...
    if form.is_valid():
        # ...process form data.
        query = form.cleaned_data.get('text', None)
        study_pks = form.cleaned_data.get('study', []) if 'study' in form.cleaned_data else []
        # Search text.
        traits = search(query, trait_type, study_pks)
        TraitTableClass = tables.SourceTraitTableFull if trait_type == 'source' else tables.HarmonizedTraitTable
        trait_table = TraitTableClass(traits)
        RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
        # Show the search results.
        page_data['trait_table'] = trait_table
        page_data['query'] = query
        page_data['study_pks'] = study_pks
        page_data['results'] = True
        # Find search if available
        search_record = check_search_existence(query, trait_type, studies=study_pks)
        # Update the count of the search, if it exists.
        if search_record:
            search_record.search_count += 1
            search_record.save()
        # Otherwise, create a record of the search.
        else:
            search_record = profiles.models.Search(param_text=query, search_type=trait_type)
            # Create the record before trying to add the many-to-many relationship.
            search_record.save()
            for study in study_pks:
                search_record.param_studies.add(study)
        # Check to see if user has this saved already.
        if profiles.models.Profile.objects.all().filter(user=request.user.id,
                                                        saved_searches=search_record.id).exists():
            savedSearchCheck = True
        else:
            savedSearchCheck = False
        page_data['alreadySaved'] = savedSearchCheck
    # If the form data isn't valid, show the data to modify.
    else:
        page_data['results'] = False
    return render(request, 'trait_browser/search.html', page_data)


@login_required
def save_search_to_profile(request):
    """Saves the user's search to their profile."""
    if request.method == "POST":
        # Parse search parameters from provided url.
        trait_type = request.POST.get('trait_type')
        query_string = request.POST.get('search_params')
        params = parse_qs(query_string)
        # Should be a list of one element.
        text = params['text'][0]
        # Studies from the requested search.
        # Studies are stored as a list of strings, sorted by applying int on each element.
        studies = params['study'] if 'study' in params else []
        search_record = check_search_existence(text, trait_type, studies=studies)
        profile_record, new_record = profiles.models.Profile.objects.get_or_create(user_id=request.user.id)
        # Save the user search.
        # user_id can be the actual value, saved_search_id has to be the model instance for some reason.
        profile, new_record = profiles.models.SavedSearchMeta.objects.get_or_create(
            profile_id=profile_record.id, search_id=search_record.id)
        profile.save()
        search_url = '?'.join([reverse(':'.join(['trait_browser', trait_type, 'traits', 'search'])), query_string])
        return redirect(search_url)


def check_search_existence(query, search_type, studies=[]):
    """Returns the search record, otherwise None."""
    searches = profiles.models.Search.objects.all().select_related()
    searches = searches.filter(param_text=query, search_type=search_type)
    for study in studies:
        searches = searches.filter(param_studies=study)
    search = searches[0] if searches.exists() else None
    return search
