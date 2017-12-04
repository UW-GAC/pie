"""URL configuration for the tags app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /tag.
"""

from django.conf.urls import include, url

from . import views

add_one_patterns = [
    url(r'^$', views.TaggedTraitCreate.as_view(), name='main'),
    url(r'^(?P<pk>\d+)/$', views.TaggedTraitCreateByTag.as_view(), name='by-tag'),
]

add_many_patterns = [
    url(r'^$', views.ManyTaggedTraitsCreate.as_view(), name='main'),
    url(r'^(?P<pk>\d+)/$', views.ManyTaggedTraitsCreateByTag.as_view(), name='by-tag'),
]

tag_patterns = [
    url(r'^$', views.TagDetail.as_view(), name='detail'),
]

urlpatterns = [
    url(r'^(?P<pk>\d+)/', include(tag_patterns, namespace='tag')),
    url(r'^add-to-phenotype/', include(add_one_patterns, namespace='add-one')),
    url(r'^add-to-many-phenotypes/', include(add_many_patterns, namespace='add-many')),
    url(r'^list', views.TagList.as_view(), name='list'),
]
