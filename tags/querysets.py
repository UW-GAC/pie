"""Custom QuerySets for the tags app."""

from django.db import models


class TaggedTraitQuerySet(models.query.QuerySet):
    """Class to hold custom query set filtering methods for the TaggedTrait model."""

    def unreviewed(self):
        """Filter to unreviewed TaggedTrait objects only."""
        return self.filter(dcc_review__isnull=True)

    def need_followup(self):
        """Filter to TaggedTrait object that need study followup only."""
        # We can't import from models.py because of models.py imports
        # querysets.py. There might be a way to get the DCCReview model
        # constants without importing models.py, but I haven't been able to
        # figure out how.
        followup_code = self.model._meta.get_field('dcc_review').related_model.STATUS_FOLLOWUP
        return self.filter(dcc_review__status=followup_code)
