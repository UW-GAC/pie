from django.shortcuts import render, get_object_or_404, HttpResponse
from django_tables2   import RequestConfig
from .models          import SourceEncodedValue, SourceTrait
from .tables          import SourceTraitTable

def index(request):
    return HttpResponse("Hello, world. You're looking at the trait_browser index page.")

def source_trait_detail(request, source_trait_id):
    source_trait = get_object_or_404(SourceTrait, trait_id=source_trait_id)
    show_fields = ('trait_id', 'trait_name', 'short_description', 'data_type',
                   'dbgap_study_id', 'dbgap_study_version', 'dbgap_variable_id',
                   'dbgap_comment', 'dbgap_unit', 'dataset_description', 'web_date_added')
    field_tups = tuple([(el, getattr(source_trait, el, None)) for el in show_fields])
        
    return render(request, 'trait_browser/source_trait_detail.html',
                  {'source_trait' : source_trait, 'field_tups': field_tups})

def source_trait_table(request):
    trait_type = 'Source'
    trait_table = SourceTraitTable(SourceTrait.objects.all())
    # If you're going to change this later to some kind of filtered list (e.g. only the most
    # recent version of each trait), then you should wrap the SourceTrait.filter() in get_list_or_404
    RequestConfig(request, paginate={'per_page': 100}).configure(trait_table)
    return render(request, "trait_browser/trait_table.html", {'trait_table': trait_table,
                                                              'trait_type': trait_type})

