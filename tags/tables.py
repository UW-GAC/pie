"""Table classes for tags app, using django-tables2."""

from django.urls import reverse
from django.utils.safestring import mark_safe

import django_tables2 as tables

from . import models


# HTML template strings
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
STATUS_TEXT_HTML = '<p class="text-{text_class}">{text}</p>'

# Text for use in status columns
AGREE_TEXT = 'Agreed to remove'
DISAGREE_TEXT = 'Gave explanation'
ARCHIVED_TEXT = 'Removed by DCC'
CONFIRMED_TEXT = 'Confirmed'
FOLLOWUP_TEXT = 'Needs study followup'
FOLLOWUP_STUDY_USER_TEXT = 'Flagged for removal'
DECISION_CONFIRM_TEXT = 'Confirm'
DECISION_REMOVE_TEXT = 'Remove'
DECISION_CONFIRM_STUDY_USER_TEXT = 'DCC confirmed'
DECISION_REMOVE_STUDY_USER_TEXT = 'DCC will remove'

AGREE_CLASS = 'success'
DISAGREE_CLASS = 'danger'
ARCHIVED_CLASS = 'warning'
CONFIRMED_CLASS = 'success'
FOLLOWUP_CLASS = 'danger'
DECISION_CONFIRM_CLASS = 'success'
DECISION_REMOVE_CLASS = 'danger'


class TagTable(tables.Table):
    """Table for displaying all tags."""

    title = tables.LinkColumn('tags:tag:detail', args=[tables.utils.A('pk')], verbose_name='Tag')
    number_tagged_traits = tables.Column(
        empty_values=(), verbose_name='Number of tagged study variables', orderable=False)
    # TODO: Add column for the number of studies tagged.

    class Meta:
        model = models.Tag
        fields = ('title', 'description', )
        attrs = {'class': 'table table-striped table-bordered table-hover'}
        template = 'django_tables2/bootstrap-responsive.html'
        order_by = ('title', )

    def render_number_tagged_traits(self, record):
        """Render column with the count of non-archived non-deprecated tagged traits for each tag."""
        return record.current_non_archived_traits.count()


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


class TaggedTraitDeleteButtonColumnMixin(tables.Table):
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


class TaggedTraitDetailColumnMixin(tables.Table):
    """Mixin to show buttons linking to detail pages in a TaggedTrait table."""

    details = tables.TemplateColumn(verbose_name='', orderable=False, template_code=DETAIL_BUTTON_TEMPLATE)


class TaggedTraitQualityReviewColumnMixin(tables.Table):
    """Mixin to show 'quality review' column in a TaggedTrait table.

    Quality review status includes dcc review status, study response status,
    dcc decision status, and archived status.
    This column is intended for viewing by study users, and lacks the detail
    that DCC users will want to see.
    """

    quality_review = tables.Column('Quality review status', accessor='dcc_review.status')

    def render_quality_review(self, record):
        html = ''
        if not hasattr(record, 'dcc_review'):
            return html
        # Add status info for DCC review.
        elif record.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            html += STATUS_TEXT_HTML.format(text=CONFIRMED_TEXT, text_class=CONFIRMED_CLASS)
        elif record.dcc_review.status == models.DCCReview.STATUS_FOLLOWUP:
            html += STATUS_TEXT_HTML.format(text=FOLLOWUP_STUDY_USER_TEXT, text_class=FOLLOWUP_CLASS)
            if hasattr(record.dcc_review, 'study_response'):
                # Add status info for study response, if it exists.
                if record.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
                    html += '\n' + STATUS_TEXT_HTML.format(text=AGREE_TEXT, text_class=AGREE_CLASS)
                elif record.dcc_review.study_response.status == models.StudyResponse.STATUS_DISAGREE:
                    html += '\n' + STATUS_TEXT_HTML.format(text=DISAGREE_TEXT, text_class=DISAGREE_CLASS)
            if hasattr(record.dcc_review, 'dcc_decision'):
                # Add status info for dcc decision, if it exists.
                if record.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_CONFIRM:
                    html += '\n' + STATUS_TEXT_HTML.format(
                        text=DECISION_CONFIRM_STUDY_USER_TEXT, text_class=DECISION_CONFIRM_CLASS)
                elif record.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_REMOVE:
                    html += '\n' + STATUS_TEXT_HTML.format(
                        text=DECISION_REMOVE_STUDY_USER_TEXT, text_class=DECISION_REMOVE_CLASS)
        # Add status info for archiving.
        if record.archived:
            html += '\n' + STATUS_TEXT_HTML.format(text=ARCHIVED_TEXT, text_class=ARCHIVED_CLASS)
        return mark_safe(html)


class TaggedTraitDCCReviewStatusColumnMixin(tables.Table):
    """Mixin to show 'DCC review status' column in a TaggedTrait table."""

    dcc_review_status = tables.Column('DCC review status', accessor='dcc_review.status')

    def render_dcc_review_status(self, record):
        if not hasattr(record, 'dcc_review'):
            return ''
        elif record.dcc_review.status == models.DCCReview.STATUS_CONFIRMED:
            html = STATUS_TEXT_HTML.format(text=CONFIRMED_TEXT, text_class=CONFIRMED_CLASS)
        elif record.dcc_review.status == models.DCCReview.STATUS_FOLLOWUP:
            html = STATUS_TEXT_HTML.format(text=FOLLOWUP_TEXT, text_class=FOLLOWUP_CLASS)
        return mark_safe(html)


class TaggedTraitStudyResponseStatusColumnMixin(tables.Table):
    """Mixin to show 'Study response status' column in a TaggedTrait table."""

    study_response_status = tables.Column('Study response status', accessor='dcc_review.study_response.status')

    def render_study_response_status(self, record):
        if not hasattr(record, 'dcc_review'):
            return ''
        elif not hasattr(record.dcc_review, 'study_response'):
            return ''
        elif record.dcc_review.study_response.status == models.StudyResponse.STATUS_AGREE:
            html = STATUS_TEXT_HTML.format(text=AGREE_TEXT, text_class=AGREE_CLASS)
        elif record.dcc_review.study_response.status == models.StudyResponse.STATUS_DISAGREE:
            html = STATUS_TEXT_HTML.format(text=DISAGREE_TEXT, text_class=DISAGREE_CLASS)
        return mark_safe(html)


class TaggedTraitDCCDecisionColumnMixin(tables.Table):
    """Mixin to show 'DCC decision' column in a TaggedTrait table."""

    dcc_decision = tables.Column('Final decision by DCC', accessor='dcc_review.dcc_decision.decision')

    def render_dcc_decision(self, record):
        if not hasattr(record, 'dcc_review'):
            return ''
        elif not hasattr(record.dcc_review, 'dcc_decision'):
            return ''
        elif record.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_CONFIRM:
            html = STATUS_TEXT_HTML.format(text=DECISION_CONFIRM_TEXT, text_class=DECISION_CONFIRM_CLASS)
        elif record.dcc_review.dcc_decision.decision == models.DCCDecision.DECISION_REMOVE:
            html = STATUS_TEXT_HTML.format(text=DECISION_REMOVE_TEXT, text_class=DECISION_REMOVE_CLASS)
        return mark_safe(html)


class TaggedTraitArchivedColumnMixin(tables.Table):
    """Mixin to show 'Archived' column in a TaggedTrait table."""

    archived = tables.Column('Archived', accessor='archived')

    def render_archived(self, record):
        if record.archived:
            html = STATUS_TEXT_HTML.format(text=ARCHIVED_TEXT, text_class=ARCHIVED_CLASS)
            return mark_safe(html)
        else:
            return ''


class TaggedTraitDCCActionButtonMixin(tables.Table):
    """Mixin to show buttons for reviewing or deciding a TaggedTrait.

    This column will display a button to either create a new review or update an existing review,
    or to create a new dcc decision or update an existing decision.
    """

    dcc_action_button = tables.Column(verbose_name='Actions', accessor='pk', orderable=False)

    def render_dcc_action_button(self, record):
        html = ''
        if (not hasattr(record, 'dcc_review')) and (not record.archived):
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-review:new', args=[record.pk]),
                                             btn_text="Add DCC review", btn_class='btn-primary')
        if hasattr(record, 'dcc_review') and (not hasattr(record.dcc_review, 'study_response')):
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-review:update',
                                                         args=[record.pk]),
                                             btn_text="Update DCC review", btn_class='btn-warning')
        if hasattr(record, 'dcc_review') and hasattr(record.dcc_review, 'dcc_decision'):
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-decision:update',
                                                         args=[record.pk]),
                                             btn_text="Update final decision", btn_class='btn-warning')
        if hasattr(record, 'dcc_review') and hasattr(record.dcc_review, 'study_response') and \
            (record.dcc_review.study_response.status == models.StudyResponse.STATUS_DISAGREE) and \
                (not hasattr(record.dcc_review, 'dcc_decision')):
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-decision:new', args=[record.pk]),
                                             btn_text="Make final decision", btn_class='btn-primary')
        return mark_safe(html)


class TaggedTraitDCCDecisionButtonMixin(tables.Table):
    """Mixin to show button for deciding on a TaggedTrait.

    This column will display a button to either create a new DCC Decision or update an existing one.
    """

    decision_buttons = tables.Column(verbose_name='', accessor='pk')

    def render_decision_buttons(self, record):
        # Have an update button if a decision already exists.
        if hasattr(record.dcc_review, 'dcc_decision'):
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-decision:update',
                                                         args=[record.pk]),
                                             btn_text='Update final decision', btn_class='btn-warning')
        else:
            html = REVIEW_BUTTON_HTML.format(url=reverse('tags:tagged-traits:pk:dcc-decision:new', args=[record.pk]),
                                             btn_text='Make final decision', btn_class='btn-primary')
        return mark_safe(html)


class TaggedTraitTableForPhenotypeTaggersFromStudy(TaggedTraitDetailColumnMixin, TaggedTraitQualityReviewColumnMixin,
                                                   TaggedTraitTable):
    """Table to display tagged traits to phenotype taggers from the study being shown.

    Used for TaggedTraitByTagAndStudyList. Includes a column with links to detail pages, and a column
    with the quality review status.
    """

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'details', 'quality_review', )


class TaggedTraitTableForStaffByStudy(TaggedTraitDetailColumnMixin, TaggedTraitDCCActionButtonMixin,
                                      TaggedTraitDCCReviewStatusColumnMixin, TaggedTraitStudyResponseStatusColumnMixin,
                                      TaggedTraitDCCDecisionColumnMixin,
                                      TaggedTraitArchivedColumnMixin, TaggedTraitTable):
    """Table for displaying TaggedTraits to DCC staff users.

    Used for TaggedTraitByTagAndStudyList. Includes columns for DCC review, study response, and archived
    status. Includes column with DCC Review create/update button and links to detail pages.
    """

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'details', 'dcc_action_button', 'dcc_review_status',
                  'study_response_status', 'dcc_decision', 'archived', )


class TaggedTraitDCCReviewTable(tables.Table):
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


class TaggedTraitDCCReviewStudyResponseButtonTable(TaggedTraitQualityReviewColumnMixin, TaggedTraitDCCReviewTable):
    """Table to display TaggedTrait and DCCReview info plus buttons for creating a StudyResponse."""

    buttons = tables.TemplateColumn(verbose_name='Quality review action',
                                    template_name='tags/_studyreview_buttons.html',
                                    orderable=False)

    class Meta(TaggedTraitDCCReviewTable.Meta):
        fields = ('trait', 'dataset', 'dcc_comment', 'details', 'quality_review', 'buttons', )


class TaggedTraitDCCDecisionTable(TaggedTraitDetailColumnMixin, TaggedTraitDCCReviewStatusColumnMixin,
                                  TaggedTraitStudyResponseStatusColumnMixin, TaggedTraitArchivedColumnMixin,
                                  TaggedTraitDCCDecisionButtonMixin, TaggedTraitDCCDecisionColumnMixin,
                                  TaggedTraitTable):
    """Table for displaying tagged traits that need DCC Decisions for one study + tag combination."""

    class Meta(TaggedTraitTable.Meta):
        fields = ('tag', 'trait', 'description', 'dataset', 'details', 'dcc_review_status',
                  'study_response_status', 'dcc_decision', 'archived', 'decision_buttons', )
