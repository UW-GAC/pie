"""View functions and classes for the trait_browser app."""

from django.shortcuts import render, get_object_or_404, HttpResponse
from django.db.models import Q    # Allows complex queries when searching.
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django_tables2   import RequestConfig

from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort
from .tables import SourceTraitTable, HarmonizedTraitTable, StudyTable
from .forms import SourceTraitCrispySearchForm, HarmonizedTraitCrispySearchForm, UnitRecipeForm, HarmonizationRecipeForm


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


@login_required
def new_recipe(request, recipe_type):
    """View for creating new UnitRecipe or HarmonizationRecipe objects."""  
    if recipe_type == 'unit':
        recipe_form = UnitRecipeForm
    elif recipe_type == 'harmonization':
        recipe_form = HarmonizationRecipeForm
    if request.method == 'POST':
        form = recipe_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.creator = request.user
            instance.last_modifier = request.user
            instance.save()
            form.save_m2m() # Have to save the m2m fields manually because of using commit=False above.
    else:
        form = recipe_form()
    return render(request, 'trait_browser/new_recipe_form.html', {'form': form})
