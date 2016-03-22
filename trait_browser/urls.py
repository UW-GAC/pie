"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /trait_browser.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    # General views
    url(r'^studies/$', views.study_list, name='study_list'),
    # Source trait views
    url(r'^source/all/$', views.source_all, name='source_all'),
    url(r'^source/study/(?P<pk>\d+)/$', views.source_study_detail, name='source_study_detail'),
    url(r'^source/detail/(?P<pk>\d+)/$', views.SourceTraitDetail.as_view(), name='source_detail'),
    url(r'^source/search/$', views.source_search, name='source_search'),
    # Harmonized trait views
    # url(r'^harmonized/all/$', views.harmonized_trait_table, name='harmonized_all'),
    # url(r'^harmonized/study/(?P<pk>\d+)/$', views.study_harmonized_trait_table, name='study_detail'),
    # url(r'^harmonized/detail/(?P<pk>\d+)/$', views.harmonizedTraitDetail.as_view(), name='harmonized_trait_detail'),
    # url(r'^harmonized/search/$', views.harmonized_trait_search, name='harmonized_trait_search'),
]