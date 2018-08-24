"""Table classes for tags app, using django-tables2."""

from django.template.loader import get_template
from django.urls import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

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
    details = tables.TemplateColumn(verbose_name='', orderable=False,
                                    template_code=DETAIL_BUTTON_TEMPLATE)

    class Meta:
        model = models.TaggedTrait
        fields = ('tag', 'trait', 'description', 'dataset', 'details', )
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


class TaggedTraitTableReviewStatusMixin(tables.Table):
    """Mixin to show DCCReview status in a TaggedTrait table."""

    quality_review = tables.Column('Quality review', accessor='dcc_review.status')

    def render_quality_review(self, record):

        if not hasattr(record, 'dcc_review'):
            return ''
        elif record.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            btn_class = 'success'
            glyphicon = 'glyphicon-ok'
            text = record.dcc_review.get_status_display()
        elif record.dcc_review.status == models.DCCReview.STATUS_FOLLOWUP:
            btn_class = 'danger'
            glyphicon = 'glyphicon-remove'
            text = 'Flagged for removal'
        html = '<p class="text-{btn_class}">{text}</a>'.format(
            btn_class=btn_class,
            glyphicon=glyphicon,
            text=text
        )
        return mark_safe(html)


class TaggedTraitTableDCCReviewButtonMixin(TaggedTraitTableReviewStatusMixin):
    """Mixin to show DCCReview status and a button to review a TaggedTrait."""

    # This column will display a button to either create a new review or update an existing review.
    review_button = tables.Column(verbose_name='', accessor='pk')

    def render_review_button(self, record):
        if not hasattr(record, 'dcc_review'):
            url = reverse('tags:tagged-traits:pk:dcc-review:new', args=[record.pk])
            btn_text = "Add a DCC review"
            btn_class = 'btn-primary'
        else:
            if hasattr(record.dcc_review, 'study_response'):
                return ('')
            else:
                url = reverse('tags:tagged-traits:pk:dcc-review:update', args=[record.pk])
                btn_text = "Update DCC review"
                btn_class = 'btn-warning'
        html = REVIEW_BUTTON_HTML.format(url=url, btn_text=btn_text, btn_class=btn_class)
        return mark_safe(html)


class TaggedTraitTableWithReviewStatus(TaggedTraitTableReviewStatusMixin, TaggedTraitTable):
    """Table for displaying TaggedTraits with DCCReview information."""

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'details', 'quality_review', )


class TaggedTraitTableWithDCCReviewButton(TaggedTraitTableDCCReviewButtonMixin, TaggedTraitTable):
    """Table for displaying TaggedTraits with DCCReview information and review button."""

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'details', 'dcc_status', 'response_status',
                  'review_button', )


class DCCReviewTable(tables.Table):
    """Table for displaying TaggedTrait and DCCReviews."""

    trait = tables.TemplateColumn(verbose_name='Study Variable', orderable=False,
                                  template_code="""{{ record.trait.get_name_link_html|safe }}""")
    details = tables.TemplateColumn(verbose_name='', orderable=False,
                                    template_code=DETAIL_BUTTON_TEMPLATE)
    dataset = tables.TemplateColumn(verbose_name='Dataset', orderable=False,
                                    template_code="""{{ record.trait.source_dataset.get_name_link_html|safe }}""")
    dcc_comment = tables.Column('Reason for removal', accessor='dcc_review.comment', orderable=False)

    class Meta:
        # It doesn't really matter if we use TaggedTrait or DCCReview because of the one-to-one relationship.
        models.TaggedTrait
        fields = ('trait', 'dataset', 'dcc_comment', 'details', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'django_tables2/bootstrap-responsive.html'


class DCCReviewTableWithStudyResponseButtons(DCCReviewTable):
    """Table to display TaggedTrait and DCCReview info plus buttons for creating a StudyResponse."""

    buttons = tables.Column(verbose_name='', accessor='pk')

    def render_buttons(self, record):
        html = '<button type="button" class="btn btn-xs btn-{btn_type}" disabled="disabled">{text}</button>'
        if hasattr(record, 'dcc_review') and hasattr(record.dcc_review, 'study_response'):
            if record.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
                return mark_safe(html.format(btn_type='success', text='Agreed to remove'))
            else:
                return mark_safe(html.format(btn_type='danger', text='Gave explanation'))
        else:
            return get_template('tags/_studyreview_buttons.html').render({'record': record})

    class Meta(DCCReviewTable.Meta):
        pass
