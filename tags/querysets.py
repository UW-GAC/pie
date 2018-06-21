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
        return self.filter(dcc_review__status=followup_code)

    def delete(self, *args, **kwargs):
        """Only allow deletion if no objects have an associated DCCReview."""
        n_reviewed = self.filter(dcc_review__isnull=False).count()
        if n_reviewed > 0:
            raise DeleteNotAllowedError("Cannot delete TaggedTraits that have been reviewed.")
        super().delete(*args, **kwargs)
