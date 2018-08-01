"""Custom QuerySets for the tags app."""

from django.db import models

from core.exceptions import DeleteNotAllowedError


class TaggedTraitQuerySet(models.query.QuerySet):
    """Class to hold custom query set filtering methods for the TaggedTrait model."""

    def unreviewed(self):
        """Filter to unreviewed TaggedTrait objects only."""
        return self.filter(dcc_review__isnull=True)

    def need_followup(self):
        """Filter to TaggedTrait object that need study followup only."""
        followup_code = self.model._meta.get_field('dcc_review').related_model.STATUS_FOLLOWUP
        return self.filter(dcc_review__status=followup_code).filter(dcc_review__study_response__isnull=True)

    def delete(self, *args, **kwargs):
        """Only allow deletion if no objects have an associated DCCReview."""
        reviewed_objects = self.filter(dcc_review__isnull=False)
        n_reviewed = reviewed_objects.count()
        if n_reviewed > 0:
            msg_part = ', '.join([str(x) for x in reviewed_objects])
            raise DeleteNotAllowedError("Cannot delete TaggedTraits that have been reviewed: {}.".format(msg_part))
        super().delete(*args, **kwargs)

    def hard_delete(self, *args, **kwargs):
        """Delete the queryset objects regardless of review status."""
        super().delete(*args, **kwargs)
