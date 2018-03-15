"""Search functions for the trait_browser app."""

import watson.search as watson

from . import models


def search_source_traits(description='', studies=[], datasets=[], name='', match_exact_name=True):
    """Search source traits."""
    qs = models.SourceTrait.objects.current()
    if len(studies) > 0:
        qs = qs.filter(source_dataset__source_study_version__study__in=studies)
    if len(datasets) > 0:
        qs = qs.filter(source_dataset__in=datasets)
    if len(name) > 0:
        if match_exact_name:
            qs = qs.filter(i_trait_name__iexact=name)
        else:
            qs = qs.filter(i_trait_name__icontains=name)
    if len(description) > 0:
        qs = watson.filter(qs, description, ranking=False)
    return qs.order_by('source_dataset__i_accession', 'i_dbgap_variable_accession')


def search_harmonized_traits(description='', name='', match_exact_name=True):
    """Search harmonized traits."""
    qs = models.HarmonizedTrait.objects.current()
    if len(name) > 0:
        if match_exact_name:
            qs = qs.filter(i_trait_name__iexact=name)
        else:
            qs = qs.filter(i_trait_name__icontains=name)
    if len(description) > 0:
        qs = watson.filter(qs, description, ranking=False)
    return qs.order_by('harmonized_trait_set_version__harmonized_trait_set')
