"""View functions and classes for the trait_browser app."""

from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from django.core.urlresolvers import reverse
from django.db.models import Q    # Allows complex queries when searching.
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from braces.views import LoginRequiredMixin
from dal import autocomplete
from django_tables2 import RequestConfig
from urllib.parse import unquote, urlparse, parse_qs

from profiles.models import *
from .models import *
from .tables import *
from .forms import *


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.  


class SourceTraitDetail(LoginRequiredMixin, DetailView):
    """Detail view class for SourceTraits. Inherits from django.views.generic.DetailView."""    
    
    model = SourceTrait
    context_object_name = 'source_trait'
    template_name = 'trait_browser/source_trait_detail.html'


class HarmonizedTraitSetDetail(LoginRequiredMixin, DetailView):
    """Detail view class for HarmonizedTraitSets. Inherits from django.views.generic.DetailView."""    
    
    model = HarmonizedTraitSet
    context_object_name = 'harmonized_trait_set'
    template_name = 'trait_browser/harmonized_trait_set_detail.html'


@login_required
def trait_table(request, trait_type):
    """Table view for SourceTrait and HarmonizedTrait objects.
    
    This view uses Django-tables2 to display a pretty table of the traits
    in the database for browsing.
    """
    if trait_type == 'harmonized':
        table_title = 'DCC-harmonized phenotypes currently available'
        page_title = 'Harmonized phenotypes'
        trait_table = HarmonizedTraitTable(HarmonizedTrait.objects.all())
    elif trait_type == 'source':
        table_title = 'Source phenotypes currently available'
        page_title = 'Source phenotypes'
        trait_table = SourceTraitTable(SourceTrait.objects.exclude(source_dataset__source_study_version__i_is_deprecated=True))
    # If you're going to change this later to some kind of filtered list (e.g. only the most
    # recent version of each trait), then you should wrap the SourceTrait.filter() in get_list_or_404
    
    # RequestConfig seems to be necessary for sorting to work.
    RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
    return render(request, 'trait_browser/trait_table.html',
        {'trait_table': trait_table, 'table_title': table_title, 'page_title': page_title, 'trait_type': trait_type}
    )


@login_required
def source_study_detail(request, pk):
    """Table view for a table of SourceTraits for a single study.
    
    This view uses Django-tables2 to display a pretty table of the SourceTraits
    in the database for browsing, within a single study.
    """
    this_study = get_object_or_404(Study, i_accession=pk)
    table_title = 'Source phenotypes currently available in {}'.format(this_study.i_study_name)
    page_title = 'phs{:6} source phenotypes'.format(this_study.phs)
    trait_table = SourceTraitTable(SourceTrait.objects.exclude(source_dataset__source_study_version__i_is_deprecated=True).filter(source_dataset__source_study_version__study__i_accession=pk))
    # If you're going to change this later to some kind of filtered list (e.g. only the most
    # recent version of each trait), then you should wrap the SourceTrait.filter() in get_list_or_404
    # RequestConfig seems to be necessary for sorting to work.
    RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
    return render( request, 'trait_browser/trait_table.html',
        {'trait_table': trait_table, 'table_title': table_title, 'page_title': page_title, 'trait_type': 'source', 'search_url': this_study.get_search_url()}
    )


@login_required
def source_study_list(request):
    """Table view for a table listing each of the studies, with links.
    
    This view uses Django-tables2 to display a pretty table of the Study
    objects in the database for browsing. Study name links will take you
    to a view of the source traits in a single study and dbGaP links will
    take you to the latest dbGaP study information page.
    """
    table_title = 'Studies with available source phenotypes'
    page_title = 'Browse source by study'
    study_table = StudyTable(Study.objects.all())
    RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(study_table)
    return render(request, 'trait_browser/study_table.html',
        {'study_table': study_table, 'table_title': table_title, 'page_title': page_title}
    )


def search(text_query, trait_type, study_pks=[]):
    """Search either source or (eventually) harmonized traits for a given query.
    
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
            traits = SourceTrait.objects.all()
        # Filter by study.
        else:
            traits = SourceTrait.objects.filter(source_dataset__source_study_version__study__pk__in=study_pks)
        # Then exclude deprecated study versions and search text.
        traits = traits.exclude(source_dataset__source_study_version__i_is_deprecated=True).filter(Q(i_description__contains=text_query) | Q(i_trait_name__contains=text_query))
    elif trait_type == 'harmonized':
        traits = HarmonizedTrait.objects.filter(Q(i_description__contains=text_query) | Q(i_trait_name__contains=text_query))
    return(traits)


@login_required
def trait_search(request, trait_type):
    """Trait search form view.
    
    Displays the SourceTraitCrispySearchForm or HarmonizedTraitCrispySearchForm
    and any search results as a django-tables2 table view.
    """
    # ...create a form instance with data from the request.
    FormClass = SourceTraitCrispySearchForm if trait_type == 'source' else HarmonizedTraitCrispySearchForm
    form = FormClass(request.GET)

    page_data = {
        'form': form,
        'trait_type': trait_type,
    }

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
        TraitTableClass = SourceTraitTable if trait_type == 'source' else HarmonizedTraitTable
        trait_table = TraitTableClass(traits)
        RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
        # Show the search results.
        page_data['trait_table'] = trait_table
        page_data['query'] = query
        page_data['study_pks'] = study_pks
        page_data['results'] = True

        # find search if available
        search_record = check_search_existence(query, trait_type, studies=study_pks)

        # update the count of the search, if it exists
        if search_record:
            search_record.search_count += 1
            search_record.save()
        # otherwise, create a record of the search
        else:
            search_record = Search(param_text=query, search_type=trait_type)
            # create the record before trying to add the many-to-many relationship
            search_record.save()
            for study in study_pks:
                search_record.param_studies.add(study)

        # Check to see if user has this saved already
        if UserData.objects.all().filter(user=request.user.id, saved_searches=search_record.id).exists():
            savedSearchCheck = True
        else:
            savedSearchCheck = False

        page_data['alreadySaved'] = savedSearchCheck
    # If the form data isn't valid, show the data to modify.
    else:
        page_data['results'] = False

    return render(request, 'trait_browser/search.html', page_data)


class SourceTraitPHVAutocomplete(autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing SourceTrait-based form fields.
    
    Used with django-autocomplete-light package. Autocomplete by dbGaP accession. 
    Only include latest version.
    """    
    
    def get_queryset(self):
        retrieved = SourceTrait.objects.filter(source_dataset__source_study_version__i_is_deprecated=False)
        if self.q:
            retrieved = retrieved.filter(i_dbgap_variable_accession__regex=r'^{}'.format(self.q))
        return retrieved

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SourceTraitPHVAutocomplete, self).dispatch(*args, **kwargs)

@login_required
def save_search_to_profile(request):
    """Saves the user's search to their profile"""

    if request.method == "POST":
        # parse search parameters from provided url
        trait_type = request.POST.get('trait_type')
        query_string = request.POST.get('search_params')
        params = parse_qs(query_string)
        # should be list of one element
        text = params['text'][0]
        # studies from the requested search
        # studies are stored as a list of strings, sort by applying int on each element
        studies = params['study'] if 'study' in params else []

        # id value of search
        search_record = check_search_existence(text, trait_type, studies=studies)

        user_data_record, new_record = UserData.objects.get_or_create(user_id=request.user.id)

        # save user search
        # user_id can be the actual value, saved_search_id has to be the model instance for some reason

        user_data, new_record = SavedSearchMeta.objects.get_or_create(
            user_data_id=user_data_record.id,
            search_id=search_record.id
        )
        user_data.save()

        search_url = '?'.join([
            reverse(
                ':'.join(['trait_browser', trait_type, 'search'])
                ),
            query_string
        ])
        return redirect(search_url)

def check_search_existence(query, search_type, studies=[]):
    """ Returns the search record otherwise None """
    searches = Search.objects.all().select_related()
    searches = searches.filter(param_text=query, search_type=search_type)
    for study in studies:
        searches = searches.filter(param_studies=study)

    search = searches[0] if searches.exists() else None
    return search
