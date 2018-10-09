"""Custom QuerySets for the tags app."""

from django.db import models

from core.exceptions import DeleteNotAllowedError


class TaggedTraitQuerySet(models.query.QuerySet):
    """Class to hold custom query set filtering methods for the TaggedTrait model."""

    def delete(self, *args, **kwargs):  # noqa
        """Archive (reviewed) or delete (unreviewed), unless any included objects are confirmed via DCCReview."""
        unreviewed = self.unreviewed()
        need_followup = self.need_followup()
        confirmed = self.confirmed()
        counts = (unreviewed.count(), need_followup.count(), confirmed.count(), )
        # First, raise an error if there are any confirmed. Then archive or delete as needed.
        if confirmed.count() > 0:
            msg_part = ', '.join([str(x) for x in confirmed])
            raise DeleteNotAllowedError(
                "Cannot delete TaggedTraits that are reviewed and confirmed: {}.".format(msg_part))
        unreviewed.hard_delete()
        for tagged_trait in need_followup:
            tagged_trait.archive()
        return counts

    def hard_delete(self, *args, **kwargs):
        """Delete the queryset objects regardless of review status."""
        super().delete(*args, **kwargs)

    def unreviewed(self):
        """Filter to unreviewed TaggedTrait objects only."""
        return self.filter(dcc_review__isnull=True)

    def need_followup(self):
        """Filter to TaggedTrait object that need study followup only."""
        followup_code = self.model._meta.get_field('dcc_review').related_model.STATUS_FOLLOWUP
        return self.filter(dcc_review__status=followup_code)

    def confirmed(self):
        """Filter to TaggedTrait object that are confirmed only."""
        confirmed_code = self.model._meta.get_field('dcc_review').related_model.STATUS_CONFIRMED
        return self.filter(dcc_review__status=confirmed_code)

    def non_archived(self):
        """Filter to non-archived tagged traits."""
        return self.filter(archived=False)

    def archived(self):
        """Filter to archived tagged traits."""
        return self.filter(archived=True)


class DCCReviewQuerySet(models.query.QuerySet):
    """Class to hold custom query set filtering methods for the DCCReviewQueryset model."""

    def delete(self, *args, **kwargs):
        """Only allow deletion if no objects have an associated StudyResponse."""
        reviewed_objects = self.filter(study_response__isnull=False)
        n_reviewed = reviewed_objects.count()
        if n_reviewed > 0:
            msg_part = ', '.join([str(x) for x in reviewed_objects])
            raise DeleteNotAllowedError("Cannot delete DCCReviews that have study responses: {}.".format(msg_part))
        super().delete(*args, **kwargs)

    def hard_delete(self, *args, **kwargs):
        """Delete the queryset objects regardless of response status."""
        super().delete(*args, **kwargs)
