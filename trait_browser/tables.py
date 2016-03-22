"""Table classes for trait_browser app, using django-tables2."""

import django_tables2 as tables

from .models import SourceTrait, Study


# Define the table classes for displaying nice HTML tables with django-tables2
class SourceTraitTable(tables.Table):
    """Class for tables2 handling of SourceTrait objects for nice table display.
    
    Django-tables2 enables pretty display of tables of data on django pages with
    builtin sorting and table layout. This class extends the tables.Table class
    for use with SourceTrait objects.
    """

    # Set custom column values that need extra settings.
    name = tables.LinkColumn('trait_browser:source_trait_detail', args=[tables.utils.A('pk')], verbose_name='Phenotype name')
    description = tables.Column('Phenotype description', orderable=False)
    # Get the name from the Study linked to this trait.
    study_name = tables.Column('Study name', accessor='study.name')
    dbGaP_study = tables.TemplateColumn(orderable=False,
        template_code='<a target="_blank" href={{ record.dbgap_study_link }}>{{ record.study_accession }}</a>')
    dbGaP_variable = tables.TemplateColumn(orderable=False,
        template_code='<a target="_blank" href={{ record.dbgap_variable_link }}>{{ record.variable_accession }}</a>')
    
    class Meta:
        model = SourceTrait
        fields = ('name', 'description', 'study_name', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('name', 'study_name', )


class StudyTable(tables.Table):
    """Class for tables2 handling of Study objects for nice table display.
    
    This class extends the django_tables2.Table class for use with Study
    objects. It is used for the Browse by Study page.
    """
    
    name = tables.LinkColumn('trait_browser:study_source_trait_table', args=[tables.utils.A('pk')],
                             verbose_name='Study name', orderable=False)
    dbGaP_accession = tables.TemplateColumn(orderable=False,
        template_code='<a target="_blank" href={{record.dbgap_latest_version_link}}>phs{{ record.dbgap_accession }}</a>'
    )
    
    
    class Meta:
        model = Study
        fields = ('name', )
        attrs = {'class': 'table table-striped table-hover table-bordered', 'style': 'width: auto;'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('name', )