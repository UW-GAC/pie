"""View functions and classes for the trait_browser app."""

from django.shortcuts import render, get_object_or_404, HttpResponse
from django.db.models import Q    # Allows complex queries when searching.
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

from dal import autocomplete
from django_tables2 import RequestConfig

from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort, Searches
from .tables import SourceTraitTable, HarmonizedTraitTable, StudyTable
from .forms import SourceTraitCrispySearchForm, HarmonizedTraitCrispySearchForm

from profiles.models import UserSearches

from urllib.parse import unquote, urlparse, parse_qs

TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.  


class SourceTraitDetail(DetailView):
    """Detail view class for SourceTraits. Inherits from django.views.generic.DetailView."""    
    
    model = SourceTrait
    context_object_name = 'source_trait'
    template_name = 'trait_browser/source_trait_detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SourceTraitDetail, self).dispatch(*args, **kwargs)


class HarmonizedTraitDetail(DetailView):
    """Detail view class for HarmonizedTraits. Inherits from django.views.generic.DetailView."""    
    
    model = HarmonizedTrait
    context_object_name = 'harmonized_trait'
    template_name = 'trait_browser/harmonized_trait_detail.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HarmonizedTraitDetail, self).dispatch(*args, **kwargs)


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
        {'trait_table': trait_table, 'table_title': table_title, 'page_title': page_title}
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
        {'trait_table': trait_table, 'table_title': table_title, 'page_title': page_title}
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
    # If search text has been entered into the form...
    if request.GET.get('text', None) is not None:
        if trait_type == 'source': 
            # ...create a form instance with data from the request.
            form = SourceTraitCrispySearchForm(request.GET)
            # If the form data is valid...
            if form.is_valid():
                # ...process form data.
                query = form.cleaned_data.get('text', None)
                study_pks = form.cleaned_data.get('study', [])
                # Search text.
                traits = search(query, 'source', study_pks)
                trait_table = SourceTraitTable(traits)
                RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
                # Show the search results.
                page_data = {
                    'trait_table': trait_table,
                    'query': query,
                    'form': form,
                    'results': True,
                    'trait_type': 'source'
                }

                searchText = request.GET.get('text')
                if 'study' in request.GET:
                    # list must be sorted numerically
                    studyString = sorted(request.GET.getlist('study'), key=int)
                else:
                    # use null value for absence of studies selected, otherwise you get an empty list
                    studyString = None
                print(searchText, studyString)

                # save a valid search
                try:
                    # check if search exists in table
                    searchRecord = Searches.objects.get(
                        search_string=searchText,selected_studies=studyString
                    )
                    searchRecord.times_saved += 1
                except ObjectDoesNotExist:
                    # insert record for new search
                    searchRecord = Searches(
                        search_string=searchText, selected_studies=studyString
                    )
                finally:
                    searchRecord.save()

                return render(request, 'trait_browser/search.html', page_data)
            # If the form data isn't valid, show the data to modify.
            else:
                page_data = {
                    'form': form,
                    'results': False,
                    'trait_type': 'source'
                }
                return render(request, 'trait_browser/search.html', page_data)
        if trait_type == 'harmonized': 
            # ...create a form instance with data from the request.
            form = HarmonizedTraitCrispySearchForm(request.GET)
            # If the form data is valid...
            if form.is_valid():
                # ...process form data.
                query = form.cleaned_data.get('text', None)
                # Search text.
                traits = search(query, 'harmonized')
                trait_table = HarmonizedTraitTable(traits)
                RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
                # Show the search results.
                page_data = {
                    'trait_table': trait_table,
                    'query': query,
                    'form': form,
                    'results': True,
                    'trait_type': 'harmonized'
                }
                return render(request, 'trait_browser/search.html', page_data)
            # If the form data isn't valid, show the data to modify.
            else:
                page_data = {
                    'form': form,
                    'results': False,
                    'trait_type': 'source'
                }
                return render(request, 'trait_browser/search.html', page_data)
    # If there was no data entered, show the empty form.
    else:
        if trait_type == 'source':
            form = SourceTraitCrispySearchForm()
        elif trait_type == 'harmonized':
            form = HarmonizedTraitCrispySearchForm()

        page_data = {
            'form': form,
            'results': False,
            'trait_type': trait_type
        }
        return render(request, 'trait_browser/search.html', page_data)


class SourceTraitIDAutocomplete(autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing SourceTrait-based form fields.
    
    Used with django-autocomplete-light package.
    """    
    
    def get_queryset(self):
        retrieved = SourceTrait.objects.all()
        if self.q:
            retrieved = retrieved.filter(i_trait_id__regex=r'^{}'.format(self.q))
        return retrieved

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SourceTraitIDAutocomplete, self).dispatch(*args, **kwargs)

@login_required
def saveSearchToProfile(request):
    """Saves the user's search to their profile"""

    # parse search parameters from provided url
    decodedUrl = unquote(request.GET.get('searchParams'))
    params = parse_qs(urlparse(decodedUrl).query)

    # should be list of one element
    searchText = params['text'][0]
    # studies from the requested search
    # studies are stored as a list of strings, sort by applying int on each element
    studyString = sorted(params['study'], key=int) if 'study' in params else None

    # id value of search
    searchRecord = Searches.objects.get(search_string=searchText,selected_studies=studyString)
    searchId = searchRecord.id

    # save user search
    # user_id can be the actual value, saved_search_id has to be the model instance for some reason
    userSearchRecord = UserSearches(saved_search_id=searchRecord, user_id=request.user.id)
    userSearchRecord.save()

    return HttpResponse()
