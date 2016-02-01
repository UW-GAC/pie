from django.shortcuts import render, get_object_or_404, HttpResponse
from django.db.models import Q # allows complex queries when searching
from django_tables2   import RequestConfig
from .models          import SourceEncodedValue, SourceTrait
from .tables          import SourceTraitTable
from .forms           import SourceTraitCrispySearchForm

def index(request):
    return HttpResponse("Hello, world. You're looking at the trait_browser index page.")

def source_trait_detail(request, source_trait_id):
    source_trait = get_object_or_404(SourceTrait, dcc_trait_id=source_trait_id)
    return render(request, 'trait_browser/source_trait_detail.html',
                  {'source_trait' : source_trait})

def source_trait_table(request):
    trait_type = 'Source'
    trait_table = SourceTraitTable(SourceTrait.objects.all())
    # If you're going to change this later to some kind of filtered list (e.g. only the most
    # recent version of each trait), then you should wrap the SourceTrait.filter() in get_list_or_404
    RequestConfig(request, paginate={'per_page': 50}).configure(trait_table)
    return render(request, "trait_browser/trait_table.html", {'trait_table': trait_table,
                                                              'trait_type': trait_type})

def source_trait_search(request):
    # process form data
    if request.method == "POST":
        # create a form instance with data from the request
        form = SourceTraitCrispySearchForm(request.POST)
        # check validity of form
        if form.is_valid():
            
            # process data
            query = form.cleaned_data.get("text", None)
            studies = form.cleaned_data.get('studies', [])

            # search text
            traits = SourceTrait.objects.filter(Q(description__contains=query) | Q(name__contains=query))
            # then mountain ranges
            if (len(studies) > 0):
                traits = traits.filter(study__in=studies)
            
            trait_table = SourceTraitTable(traits)
            return render(request, "trait_browser/search.html", {'trait_table': trait_table, 'query': query, 'form': form, 'results': True})
    else:
        form = SourceTraitCrispySearchForm()

    return render(request, "trait_browser/search.html", {'form': form, 'results': False})