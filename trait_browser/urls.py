"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /phenotypes.
"""

from django.conf.urls import include, url

from tags.views import TaggedTraitByStudyList
from . import views


# Study phenotype patterns.
source_trait_autocomplete_taggable_patterns = [
    url(r'^by-phv/$', views.TaggableStudyFilteredSourceTraitPHVAutocomplete.as_view(),
        name='by-phv'),
    # by name
]

source_trait_autocomplete_patterns = [
    url(r'^taggable/', include(source_trait_autocomplete_taggable_patterns, namespace='taggable')),
    url(r'^by-phv/$', views.SourceTraitPHVAutocomplete.as_view(), name='by-phv'),
    # by-name
]

source_trait_patterns = [
    url(r'^autocomplete/', include(source_trait_autocomplete_patterns, namespace='autocomplete')),
    url(r'^list/$', views.SourceTraitList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.SourceTraitDetail.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/add-tag/$', views.SourceTraitTagging.as_view(), name='tagging'),
    url(r'^search/$', views.trait_search, {'trait_type': 'source'}, name='search'),
]

source_dataset_patterns = [
    url(r'^(?P<pk>\d+)/$', views.SourceDatasetDetail.as_view(), name='detail'),
    # list
    # search
    # include autocomplete?
]

source_study_detail_patterns = [
    url(r'^tagged/$', TaggedTraitByStudyList.as_view(), name='tagged'),
    url(r'^$', views.StudyDetail.as_view(), name='detail'),
    # variable list
    # dataset list
]

source_study_patterns = [
    url(r'^list/$', views.StudyList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/', include(source_study_detail_patterns, namespace='detail')),
    # search
    # include autocomplete?
]

source_patterns = [
    url(r'^variables/', include(source_trait_patterns, namespace='traits')),
    url(r'^datasets/', include(source_dataset_patterns, namespace='datasets')),
    url(r'^studies/', include(source_study_patterns, namespace='studies')),
]

# Harmonized trait patterns.
harmonized_trait_autocomplete_patterns = [
    url(r'^by-name/$', views.HarmonizedTraitFlavorNameAutocomplete.as_view(), name='by-name'),
]

harmonized_trait_patterns = [
    url(r'^autocomplete/', include(harmonized_trait_autocomplete_patterns, namespace='autocomplete')),
    url(r'^$', views.HarmonizedTraitList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.HarmonizedTraitSetVersionDetail.as_view(), name='detail'),
    url(r'^search/$', views.trait_search, {'trait_type': 'harmonized'}, name='search'),
]

harmonized_patterns = [
    url(r'^variables/', include(harmonized_trait_patterns, namespace='traits')),
    # include datasets?
]


# list of the patterns with includes.
urlpatterns = [
    url(r'^study-phenotypes/', include(source_patterns, namespace='source')),
    url(r'^harmonized-phenotypes/', include(harmonized_patterns, namespace='harmonized')),
    url(r'^search/save/$', views.save_search_to_profile, name='save_search'),
]
