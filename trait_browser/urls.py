"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /phenotypes.
"""

from django.conf.urls import include, url

from .views import *


study_patterns = [
    url(r'^all/$', source_study_list, name='list'),
    url(r'^(?P<pk>\d+)/$', source_study_detail, name='detail'),
]

source_patterns = [
    url(r'^all/$', trait_table, {'trait_type': 'source'}, name='all'),
    url(r'^dataset/(?P<pk>\d+)/$', SourceDatasetDetail.as_view(), name='dataset'),
    url(r'^detail/(?P<pk>\d+)/$', SourceTraitDetail.as_view(), name='detail'),
    url(r'^search/$', trait_search, {'trait_type': 'source'}, name='search'),
    url(r'^autocomplete/$', SourceTraitPHVAutocomplete.as_view(), name='autocomplete'),
    url(r'^study/', include(study_patterns, namespace='study')),
]

harmonized_patterns = [
    url(r'^all/$', trait_table, {'trait_type': 'harmonized'}, name='all'),
    url(r'^detail/(?P<pk>\d+)/$', HarmonizedTraitSetDetail.as_view(), name='detail'),
    url(r'^search/$', trait_search, {'trait_type': 'harmonized'}, name='search'),
]

urlpatterns = [
    url(r'^source/', include(source_patterns, namespace='source')),
    url(r'^harmonized/', include(harmonized_patterns, namespace='harmonized')),
    url(r'^search/save/$', save_search_to_profile, name='save_search'),
]