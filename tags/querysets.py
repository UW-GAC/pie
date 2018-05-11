"""Custom QuerySets for the tags app."""

from django.db import models


class TaggedTraitQuerySet(models.query.QuerySet):
    """Class to hold custom query set filtering methods for the TaggedTrait model."""

    def unreviewed(self):
        """Filter to unreviewed TaggedTrait objects only."""
        return self.filter(dcc_review__isnull=True)
