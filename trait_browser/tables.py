import django_tables2 as tables
from .models import SourceTrait

# Define the table classes for displaying nice HTML tables with django-tables2
class SourceTraitTable(tables.Table):
    name = tables.LinkColumn('trait_browser_source_trait_detail', args=[tables.utils.A('pk')])
    # 
    
    class Meta:
        model = SourceTrait
        fields = ('name', 'description', 'study_name', )
        attrs = {'class': 'table table-striped table-bordered table-hover', 'template': 'django_tables2/bootstrap.html'}
        order_by = ('name', 'study_name', )