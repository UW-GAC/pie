import django_tables2 as tables

from .models import Search

class SourceSearchTable(tables.Table):

    source_search_text = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )
    filtered_studies = tables.TemplateColumn(
        orderable=False,
        template_code='<div data-toggle="tooltip" data-placement="bottom" title="{{ record.study_name_string }}">{{ record.search_studies }}</div>'
    )

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}

class HarmonizedSearchTable(tables.Table):

    harmonized_search_text = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
