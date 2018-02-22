"""Search functions for the trait_browser app."""

import watson.search as watson

from . import models


def source_trait_search(q='', studies=[]):
    """Search source traits."""
    qs = models.SourceTrait.objects.current()
    if len(studies) > 0:
        qs = qs.filter(source_dataset__source_study_version__study__in=studies)
    return watson.filter(qs, q)
