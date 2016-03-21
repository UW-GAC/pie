"""URL configuration for the trait_browser app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /trait_browser.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^source_trait/(?P<pk>\d+)/detail/$', views.SourceTraitDetail.as_view(),
        name='trait_browser_source_trait_detail'),
    url(r'^table/source_trait/', views.source_trait_table,
        name='trait_browser_source_trait_table'),
    url(r'^search/source_trait/', views.source_trait_search,
        name='trait_browser_source_trait_search'),
    url(r'^source_trait/study/(?P<pk>\d+)/$', views.study_source_trait_table,
        name='trait_browser_study_source_trait_table')
]