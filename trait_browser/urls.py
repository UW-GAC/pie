from django.conf.urls import url
from .                import views

urlpatterns = [
    # Trait browser index page
    url(r'^$', views.index, name='index'),
    # Source trait detail page: /trait_browser/source_trait/<source_trait_id>/detail/
    url(r'^source_trait/(?P<source_trait_id>[0-9]+)/detail/$', views.source_trait_detail, name='trait_browser_source_trait_detail'),
    url(r'^table/source_trait/', views.source_trait_table, name='trait_browser_source_trait_table'),
]

