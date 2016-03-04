"""Table classes for trait_browser app, using django-tables2."""

import django_tables2 as tables

from .models import SourceTrait


# Define the table classes for displaying nice HTML tables with django-tables2
class SourceTraitTable(tables.Table):
    """Class for tables2 handling of SourceTrait objects for nice table display.
    
    Django-tables2 enables pretty display of tables of data on django pages with
    builtin sorting and table layout. This class extends the tables.Table class
    for use with SourceTrait objects.
    """

    # Set custom column values that need extra settings.
    name = tables.LinkColumn('trait_browser_source_trait_detail', args=[tables.utils.A('pk')], verbose_name='Trait name')
    description = tables.Column('Trait description', orderable=False)
    # Get the name from the Study linked to this trait.
    study_name = tables.Column('Study name', accessor='study.name')
    
    class Meta:
        model = SourceTrait
        fields = ('name', 'description', 'study_name')
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('name', 'study_name', )