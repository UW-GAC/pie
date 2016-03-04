"""View functions and classes for the trait_browser app."""

from django.shortcuts import render, get_object_or_404, HttpResponse
from django.db.models import Q    # Allows complex queries when searching.
from django_tables2   import RequestConfig

from .models import SourceEncodedValue, SourceTrait
from .tables import SourceTraitTable
from .forms import SourceTraitCrispySearchForm


TABLE_PER_PAGE = 50    # Setting for per_page rows for all table views.  


def source_trait_detail(request, source_trait_id):
    """Detail view for SourceTrait objects."""
    source_trait = get_object_or_404(SourceTrait, dcc_trait_id=source_trait_id)
    return render(
        request,
        'trait_browser/source_trait_detail.html',
        {'source_trait' : source_trait}
    )


def source_trait_table(request):
    """Table view for SourceTrait objects.
    
    This view uses Django-tables2 to display a pretty table of the SourceTraits
    in the database for browsing.
    """
    trait_type = 'Source'
    trait_table = SourceTraitTable(SourceTrait.objects.all())
    # If you're going to change this later to some kind of filtered list (e.g. only the most
    # recent version of each trait), then you should wrap the SourceTrait.filter() in get_list_or_404
    # RequestConfig seems to be necessary for sorting to work.
    RequestConfig(request, paginate={'per_page': TABLE_PER_PAGE}).configure(trait_table)
    return render(
        request,
        'trait_browser/trait_table.html',
        {'trait_table': trait_table, 'trait_type': trait_type}
    )


def search(text_query, trait_type, studies=[]):
    """Search either source or (eventually) harmonized traits for a given query.
    
    Function to search the trait name and trait description for the given query
    text, and possibly filtering to the list of studies specified. The search is
    case-insensitive. Do not include quotes. This is a very simple search.
    
    Arguments:
        text_query -- string; text to search for within descriptions and names
        trait_type -- string; "source" or "harmonized"
        studies -- list of (primary_key, study_name) tuples
    
    Returns:
        queryset of SourceTrait or HarmonizedTrait objects
    """
    # TODO: add try/except to catch invalid trait_type values.
    if trait_type == 'source':
        traits = SourceTrait.objects.all()
    elif trait_type == 'harmonized':
        # TODO: search through harmonized trait model objects. 
        pass
    # Filter by study first.
    if (len(studies) > 0):
        traits = traits.filter(study__in=studies)
    # Then search text.
    traits = traits.filter(Q(description__contains=text_query) | Q(name__contains=text_query))
    return(traits)


# To make this eventually work for harmonized traits, we could add a trait_type
# argument to the function definition plus some if statements to select proper
# forms/models.
def source_trait_search(request):
    """SourceTrait search form view.
    
    Displays the SourceTraitCrispySearchForm and any search results as a
    django-tables2 table view.
    """
    # If search text has been entered into the form...
    if request.GET.get('text', None) is not None:
        # ...create a form instance with data from the request.
        form = SourceTraitCrispySearchForm(request.GET)
        # If the form data is valid...
        if form.is_valid():
            # ...process form data.
            query = form.cleaned_data.get('text', None)
            studies = form.cleaned_data.get('study', [])
            # Search text.
            traits = search(query, 'source', studies)
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
        form = SourceTraitCrispySearchForm()

        page_data = {
            'form': form,
            'results': False,
            'trait_type': 'source'
        }
        return render(request, 'trait_browser/search.html', page_data)