"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /phenotypes.
"""

from django.conf.urls import include, url

from . import views


app_name = 'trait_browser'

# Study phenotype patterns.
source_trait_autocomplete_taggable_patterns = ([
    url(r'^by-phv/$', views.TaggableStudyFilteredSourceTraitPHVAutocomplete.as_view(),
        name='by-phv'),
    url(r'^by-name/$', views.TaggableStudyFilteredSourceTraitNameAutocomplete.as_view(),
        name='by-name'),
    url(r'^by-name-or-phv/$', views.TaggableStudyFilteredSourceTraitNameOrPHVAutocomplete.as_view(),
        name='by-name-or-phv'),
], 'taggable', )

source_trait_autocomplete_patterns = ([
    url(r'^taggable/', include(source_trait_autocomplete_taggable_patterns)),
    url(r'^by-phv/$', views.SourceTraitPHVAutocomplete.as_view(), name='by-phv'),
    url(r'^by-name/$', views.SourceTraitNameAutocomplete.as_view(), name='by-name'),
    url(r'^by-name-or-phv/$', views.SourceTraitNameOrPHVAutocomplete.as_view(), name='by-name-or-phv'),
], 'autocomplete', )

source_trait_patterns = ([
    url(r'^autocomplete/', include(source_trait_autocomplete_patterns)),
    url(r'^list/$', views.SourceTraitList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.SourceTraitDetail.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/add-tag/$', views.SourceTraitTagging.as_view(), name='tagging'),
    url(r'^search/$', views.SourceTraitSearch.as_view(), name='search'),
    url(r'^lookup/$', views.SourceTraitLookup.as_view(), name='lookup'),
], 'traits', )

source_dataset_autocomplete_patterns = ([
    url(r'^by-name/$', views.SourceDatasetNameAutocomplete.as_view(), name='by-name'),
    url(r'^by-pht/$', views.SourceDatasetPHTAutocomplete.as_view(), name='by-pht'),
    url(r'^by-name-or-pht/$', views.SourceDatasetNameOrPHTAutocomplete.as_view(), name='by-name-or-pht'),
], 'autocomplete', )

source_dataset_patterns = ([
    url(r'^(?P<pk>\d+)/$', views.SourceDatasetDetail.as_view(), name='detail'),
    url(r'^list/$', views.SourceDatasetList.as_view(), name='list'),
    url(r'^search/$', views.SourceDatasetSearch.as_view(), name='search'),
    url(r'^autocomplete/', include(source_dataset_autocomplete_patterns)),
    url(r'^lookup/$', views.SourceDatasetLookup.as_view(), name='lookup'),
], 'datasets', )

source_study_dataset_autocomplete_patterns = ([
    url(r'^by-name/$', views.StudySourceDatasetNameAutocomplete.as_view(), name='by-name'),
    url(r'^by-pht/$', views.StudySourceDatasetPHTAutocomplete.as_view(), name='by-pht'),
    url(r'^by-name-or-pht/$', views.StudySourceDatasetNameOrPHTAutocomplete.as_view(), name='by-name-or-pht'),
], 'autocomplete', )

source_study_dataset_patterns = ([
    url(r'^autocomplete/', include(source_study_dataset_autocomplete_patterns)),
    url(r'^$', views.StudySourceDatasetList.as_view(), name='list'),
    url(r'^search/$', views.StudySourceDatasetSearch.as_view(), name='search'),
], 'datasets', )

source_study_trait_patterns = ([
    url(r'^$', views.StudySourceTraitList.as_view(), name='list'),
    url(r'^new/$', views.StudySourceTraitNewList.as_view(), name='new'),
    url(r'^search/$', views.StudySourceTraitSearch.as_view(), name='search'),
    url(r'^tagged/$', views.StudyTaggedTraitList.as_view(), name='tagged'),
], 'traits', )

source_study_detail_patterns = ([
    url(r'^datasets/', include(source_study_dataset_patterns)),
    url(r'^variables/', include(source_study_trait_patterns)),
    url(r'^$', views.StudyDetail.as_view(), name='detail'),
], 'pk', )

source_study_autocomplete_patterns = ([
    url(r'^by-name/$', views.StudyNameAutocomplete.as_view(), name='by-name'),
    url(r'^by-phs/$', views.StudyPHSAutocomplete.as_view(), name='by-phs'),
    url(r'^by-name-or-phs/$', views.StudyNameOrPHSAutocomplete.as_view(), name='by-name-or-phs'),
], 'autocomplete', )

source_study_patterns = ([
    url(r'^autocomplete/', include(source_study_autocomplete_patterns)),
    url(r'^list/$', views.StudyList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/', include(source_study_detail_patterns)),
    url(r'^lookup/$', views.StudyLookup.as_view(), name='lookup'),
], 'studies', )

source_patterns = ([
    url(r'^variables/', include(source_trait_patterns)),
    url(r'^datasets/', include(source_dataset_patterns)),
    url(r'^studies/', include(source_study_patterns)),
    url(r'lookup/$', views.SourceObjectLookup.as_view(), name='lookup'),
], 'source', )

# Harmonized trait patterns.
harmonized_trait_autocomplete_patterns = ([
    url(r'^by-name/$', views.HarmonizedTraitFlavorNameAutocomplete.as_view(), name='by-name'),
], 'autocomplete', )

harmonized_trait_patterns = ([
    url(r'^autocomplete/', include(harmonized_trait_autocomplete_patterns)),
    url(r'^$', views.HarmonizedTraitList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.HarmonizedTraitSetVersionDetail.as_view(), name='detail'),
    url(r'^search/$', views.HarmonizedTraitSearch.as_view(), name='search'),
], 'traits', )

harmonized_patterns = ([
    url(r'^variables/', include(harmonized_trait_patterns)),
    # include datasets?
], 'harmonized', )


# list of the patterns with includes.
urlpatterns = [
    url(r'^study-phenotypes/', include(source_patterns)),
    url(r'^harmonized-phenotypes/', include(harmonized_patterns)),
]
