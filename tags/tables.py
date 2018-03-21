"""Table classes for tags app, using django-tables2."""

from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2.utils import AttributeDict

from trait_browser.models import Study
from . import models


DELETE_BUTTON_TEMPLATE = """
<a class="btn btn-xs btn-danger" href="{% url 'tags:tagged-traits:delete' record.pk %}" role="button">
    <span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Remove tag
</a>
"""


class BootstrapBooleanColumn(tables.BooleanColumn):
    """django-tables2 column class for nice display of boolean values with glyphicons.

    Copied from phenotype_visit_recorder's visit_tracker.tables.
    """

    def render(self, value):
        """Define a column using Bootstrap styling to display boolean data."""
        value = bool(value)
        html = "<span %s></span>"
        class_name = ""
        if value:
            class_name = "glyphicon glyphicon-ok"
        attrs = {'class': class_name}
        attrs.update(self.attrs.get('span', {}))
        return mark_safe(html % (AttributeDict(attrs).as_html()))


class TagTable(tables.Table):
    """Table for displaying all tags."""

    title = tables.LinkColumn('tags:tag:detail', args=[tables.utils.A('pk')], verbose_name='Tag')
    number_tagged_traits = tables.Column(
        accessor='traits.count', verbose_name='Number of study variables tagged', orderable=False)
    # TODO: Add column for the number of studies tagged.

    class Meta:
        model = models.Tag
        fields = ('title', 'description', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'bootstrap_tables2.html'
        order_by = ('title', )


class StudyTaggedTraitTable(tables.Table):
    """Table for displaying studies with tagged traits and totals."""

    i_study_name = tables.LinkColumn(
        'trait_browser:source:studies:detail:tagged', args=[tables.utils.A('pk')], verbose_name='Study name',
        orderable=False)
    number_tags = tables.Column(
        accessor='get_tag_count', verbose_name='Number of tags', orderable=False)
    number_traits = tables.Column(
        accessor='get_tagged_trait_count', orderable=False,
        verbose_name='Number of tagged study variables')

    class Meta:
        model = Study
        fields = ('i_study_name', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'bootstrap_tables2.html'
        order_by = ('i_study_name', )


class TaggedTraitTable(tables.Table):
    """Table for displaying TaggedTraits."""

    trait = tables.LinkColumn(
        'trait_browser:source:traits:detail', args=[tables.utils.A('trait.pk')], verbose_name='Study variable',
        text=lambda record: record.trait.i_trait_name, orderable=True)
    description = tables.Column('Variable description', accessor='trait.i_description', orderable=False)
    dataset = tables.LinkColumn(
        'trait_browser:source:datasets:detail', args=[tables.utils.A('trait.source_dataset.pk')],
        verbose_name='Dataset',
        text=lambda record: record.trait.source_dataset.dataset_name, orderable=False)
    tag = tables.LinkColumn(
        'tags:tag:detail', args=[tables.utils.A('tag.pk')], verbose_name='Tag',
        text=lambda record: record.tag.title, orderable=True)

    class Meta:
        model = models.TaggedTrait
        fields = ('tag', 'trait', 'description', 'dataset', )
        attrs = {'class': 'table table-striped table-bordered table-hover', 'style': 'width: auto;'}
        template = 'bootstrap_tables2.html'
        order_by = ('tag', )


class TaggedTraitTableWithDelete(TaggedTraitTable):
    """Table for displaying TaggedTraits with delete buttons."""

    delete = tables.TemplateColumn(verbose_name='', orderable=False,
                                   template_code=DELETE_BUTTON_TEMPLATE)
    creator = tables.Column('Tagged by', accessor='creator.name')

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'creator', 'delete',)


class UserTaggedTraitTable(TaggedTraitTable):
    """Table for displaying TaggedTraits on a user's profile page.

    Displays user information that is not displayed in the plain old TaggedTraitTable.
    """

    delete = tables.TemplateColumn(verbose_name='', orderable=False,
                                   template_code=DELETE_BUTTON_TEMPLATE)

    class Meta(TaggedTraitTableWithDelete.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'delete',)
