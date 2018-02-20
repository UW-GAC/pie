"""Search functions for the trait_browser app."""

import watson.search as watson

from . import models


def source_trait_search(query):
    """Search source traits."""
    return watson.filter(models.SourceTrait.objects.current(), query)
