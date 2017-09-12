import django_tables2 as tables


class SourceSearchTable(tables.Table):

    remove_search = tables.TemplateColumn(
        orderable=False,
        template_code='<input type="checkbox" value={{ record.search_id }} name="search_id">'
    )
    source_search_text = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )
    filtered_studies = tables.TemplateColumn(
        orderable=False,
        template_code='<div data-toggle="popover" data-trigger="hover" data-html="true" data-content="{{ record.study_name_string }}">{{ record.search_studies }}</div>'  # noqa: E501
    )
    date_saved = tables.DateTimeColumn(orderable=False)

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}


class HarmonizedSearchTable(tables.Table):

    remove_search = tables.TemplateColumn(
        orderable=False,
        template_code='<input type="checkbox" value={{ record.search_id }} name="search_id">'
    )
    harmonized_search_text = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.search_url }}>{{ record.search_text }}</a>'
    )
    date_saved = tables.DateTimeColumn(orderable=False)

    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
