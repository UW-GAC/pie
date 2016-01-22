import django_tables2 as tables
from .models import SourceTrait

# Define the table classes for displaying nice HTML tables with django-tables2
class SourceTraitTable(tables.Table):
    trait_name = tables.LinkColumn('trait_browser_source_trait_detail', args=[tables.utils.A('pk')])
    
    class Meta:
        model = SourceTrait
        attrs = {'class': 'traitTable'}