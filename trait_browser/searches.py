"""Search functions for the trait_browser app."""

import watson.search as watson

from . import models


def search_source_datasets(description='', name='', studies=[], match_exact_name=True):
    """Search source datasets."""
    qs = models.SourceDataset.objects.current()
    if len(studies) > 0:
        qs = qs.filter(source_study_version__study__in=studies)
    if len(name) > 0:
        if match_exact_name:
            qs = qs.filter(dataset_name__iexact=name)
        else:
            qs = qs.filter(dataset_name__icontains=name)
    if len(description) > 0:
        qs = watson.filter(qs, description, ranking=False)
    return qs.order_by('source_study_version__study__i_accession', 'i_accession')


def search_source_traits(description='', datasets=None, name='', match_exact_name=True):
    """Search source traits."""
    qs = models.SourceTrait.objects.current()
    if datasets is not None:
        # Ensure that the queryset is evaluated, and pull out the pks; otherwise, unexpected errors are thrown.
        dataset_pks = [x.pk for x in datasets]
        qs = qs.filter(source_dataset__in=dataset_pks)
    if len(name) > 0:
        if match_exact_name:
            qs = qs.filter(i_trait_name__iexact=name)
        else:
            qs = qs.filter(i_trait_name__icontains=name)
    if len(description) > 0:
        qs = watson.filter(qs, description, ranking=False)
    return qs.order_by('source_dataset__source_study_version__study__i_accession',
                       'source_dataset__i_accession', 'i_dbgap_variable_accession')


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
