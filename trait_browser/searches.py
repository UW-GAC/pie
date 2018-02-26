"""Search functions for the trait_browser app."""

import watson.search as watson

from . import models


def source_trait_search(description='', studies=[], name=''):
    """Search source traits."""
    qs = models.SourceTrait.objects.current()
    if len(studies) > 0:
        qs = qs.filter(source_dataset__source_study_version__study__in=studies)
    if len(name) > 0:
        qs = qs.filter(i_trait_name__iexact=name)
    if len(description) > 0:
        qs = watson.filter(qs, description)
    return qs.order_by('source_dataset__i_accession', 'i_dbgap_variable_accession')
