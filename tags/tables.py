"""Table classes for tags app, using django-tables2."""

import django_tables2 as tables

from . import models


class TagTable(tables.Table):
    """Table for displaying all tags."""

    title = tables.LinkColumn('tags:tag:detail', args=[tables.utils.A('pk')], verbose_name='Tag')
    number_tagged_traits = tables.Column(
        accessor='traits.count', verbose_name='Number of phenotypes tagged', orderable=False)
    # TODO: Add column for the number of studies tagged.

    class Meta:
        model = models.Tag
        fields = ('title', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'bootstrap_tables2.html'
        order_by = ('title', )
