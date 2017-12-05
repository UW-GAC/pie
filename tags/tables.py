"""Table classes for tags app, using django-tables2."""

import django_tables2 as tables

from trait_browser.models import Study
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


class StudyTaggedTraitTable(tables.Table):
    """Table for displaying studies with tagged traits and totals."""

    i_study_name = tables.LinkColumn(
        'trait_browser:source:study:detail', args=[tables.utils.A('pk')], verbose_name='Study name', orderable=False)
    number_tags = tables.Column(
        accessor='get_tag_count', verbose_name='Number of tags', orderable=False)
    number_traits = tables.Column(
        accessor='get_tagged_trait_count', verbose_name='Number of traits tagged', orderable=False)

    class Meta:
        model = Study
        fields = ('i_study_name', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'bootstrap_tables2.html'
        order_by = ('i_study_name', )

