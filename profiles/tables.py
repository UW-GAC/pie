import django_tables2 as tables

from .models import Search

class SourceSearchTable(tables.Table):

    remove_search = tables.TemplateColumn(
        template_code='<input type="checkbox" value="{{ record.search_id }}"></td>',
        orderable=False
    )
    search_text = tables.TemplateColumn(
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )
    search_studies = tables.Column()

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}

class HarmonizedSearchTable(tables.Table):

    remove_search = tables.TemplateColumn(
        template_code='<input type="checkbox" value="{{ record.search_id }}"></td>',
        orderable=False
    )
    search_text = tables.TemplateColumn(
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
