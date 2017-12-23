"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /phenotypes.
"""

from django.conf.urls import include, url

from tags.views import TaggedTraitByStudyList
from . import views


study_patterns = [
    url(r'^all/$', views.StudyList.as_view(), name='list'),
    url(r'^(?P<pk>\d+)/$', views.StudyDetail.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/tagged/$', TaggedTraitByStudyList.as_view(), name='tagged'),
]

source_patterns = [
    url(r'^all/$', views.SourceTraitList.as_view(), name='all'),
    url(r'^dataset/(?P<pk>\d+)/$', views.SourceDatasetDetail.as_view(), name='dataset'),
    url(r'^(?P<pk>\d+)/$', views.SourceTraitDetail.as_view(), name='detail'),
    url(r'^(?P<pk>\d+)/add-tag/$', views.SourceTraitTagging.as_view(), name='tagging'),
    url(r'^search/$', views.trait_search, {'trait_type': 'source'}, name='search'),
    url(r'^autocomplete/$', views.SourceTraitPHVAutocomplete.as_view(), name='autocomplete'),
    url(r'^taggable-autocomplete/$', views.TaggableStudyFilteredSourceTraitPHVAutocomplete.as_view(),
        name='taggable-autocomplete'),
    url(r'^study/', include(study_patterns, namespace='study')),
]

harmonized_patterns = [
    url(r'^all/$', views.HarmonizedTraitList.as_view(), name='all'),
    url(r'^(?P<pk>\d+)/$', views.HarmonizedTraitSetVersionDetail.as_view(), name='detail'),
    url(r'^search/$', views.trait_search, {'trait_type': 'harmonized'}, name='search'),
    url(r'^autocomplete/$', views.HarmonizedTraitFlavorNameAutocomplete.as_view(), name='autocomplete'),
]

urlpatterns = [
    url(r'^source/', include(source_patterns, namespace='source')),
    url(r'^harmonized/', include(harmonized_patterns, namespace='harmonized')),
    url(r'^search/save/$', views.save_search_to_profile, name='save_search'),
]
