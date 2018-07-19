"""Table classes for tags app, using django-tables2."""

from django.urls import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from trait_browser.models import Study

from . import models


DETAIL_BUTTON_TEMPLATE = """
<a class="btn btn-xs btn-info" href="{% url 'tags:tagged-traits:pk:detail' record.pk %}" role="button">
  Details
</a>
"""
REVIEW_BUTTON_HTML = """
<a class="btn btn-xs {btn_class}" href="{url}" role="button">
  {btn_text}
</a>
"""


class TagTable(tables.Table):
    """Table for displaying all tags."""

    title = tables.LinkColumn('tags:tag:detail', args=[tables.utils.A('pk')], verbose_name='Tag')
    number_tagged_traits = tables.Column(
        accessor='traits.count', verbose_name='Number of tagged study variables', orderable=False)
    # TODO: Add column for the number of studies tagged.

    class Meta:
        model = models.Tag
        fields = ('title', 'description', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'django_tables2/bootstrap-responsive.html'
        order_by = ('title', )


class StudyTaggedTraitTable(tables.Table):
    """Table for displaying studies with tagged traits and totals."""

    i_study_name = tables.LinkColumn(
        'trait_browser:source:studies:pk:traits:tagged', args=[tables.utils.A('pk')], verbose_name='Study name',
        orderable=False)
    tag_count = tables.Column(verbose_name='Number of tags')
    taggedtrait_count = tables.Column(verbose_name='Number of tagged study variables')

    class Meta:
        model = Study
        fields = ('i_study_name', 'tag_count', 'taggedtrait_count', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'django_tables2/bootstrap-responsive.html'
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
        template = 'django_tables2/bootstrap-responsive.html'
        order_by = ('tag', )


class TaggedTraitDeleteButtonMixin(tables.Table):
    """Mixin to include a delete button in a TaggedTrait table."""

    delete_button = tables.Column(empty_values=(), verbose_name='', orderable=False)

    def render_delete_button(self, record):
        html_template = """
        <a class="{classes}" href="{url}" role="button">
            <span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Remove tag
        </a>
        """
        url = '#'
        classes = ['btn', 'btn-xs', 'btn-danger']
        if hasattr(record, 'dcc_review'):
            classes.append('disabled')
        else:
            url = reverse('tags:tagged-traits:pk:delete', args=[record.pk])
        html = html_template.format(classes=' '.join(classes), url=url)
        return mark_safe(html)


class TaggedTraitTableDCCReviewStatusMixin(tables.Table):
    """Mixin to show DCCReview status in a TaggedTrait table."""

    status = tables.Column('Status', accessor='dcc_review.status')


class TaggedTraitTableDCCReviewButtonMixin(TaggedTraitTableDCCReviewStatusMixin):
    """Mixin to show DCCReview status and a button to review a TaggedTrait."""

    # This column will display a button to either create a new review or update an existing review.
    review_button = tables.Column(verbose_name='', accessor='pk')

    def render_review_button(self, record):
        if not hasattr(record, 'dcc_review'):
            url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[record.pk])
            btn_text = "Add a DCC review"
            btn_class = 'btn-primary'
        else:
            url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[record.pk])
            btn_text = "Update DCC review"
            btn_class = 'btn-warning'
        html = REVIEW_BUTTON_HTML.format(url=url, btn_text=btn_text, btn_class=btn_class)
        return mark_safe(html)


class TaggedTraitTableWithDCCReviewStatus(TaggedTraitTableDCCReviewStatusMixin, TaggedTraitTable):
    """Table for displaying TaggedTraits with DCCReview information."""

    details = tables.TemplateColumn(verbose_name='', orderable=False,
                                    template_code=DETAIL_BUTTON_TEMPLATE)

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'status', 'details')


class TaggedTraitTableWithDCCReviewButton(TaggedTraitTableDCCReviewButtonMixin, TaggedTraitTable):
    """Table for displaying TaggedTraits with DCCReview information and review button."""

    details = tables.TemplateColumn(verbose_name='', orderable=False,
                                    template_code=DETAIL_BUTTON_TEMPLATE)

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'status', 'review_button', 'details')
