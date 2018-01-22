"""URL configuration for the tags app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /tag.
"""

from django.conf.urls import include, url
from django.views.generic import TemplateView

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

tagged_trait_patterns = [
    # url(r'^list', views.TagList.as_view(), name='list'),
    url(r'^by-study', views.StudyTaggedTraitList.as_view(), name='by-study'),
    url(r'^(?P<pk>\d+)/delete$', views.TaggedTraitDelete.as_view(), name='delete'),
]

urlpatterns = [
    url(r'^(?P<pk>\d+)/', include(tag_patterns, namespace='tag')),
    url(r'^add-to-phenotype/', include(add_one_patterns, namespace='add-one')),
    url(r'^add-to-many-phenotypes/', include(add_many_patterns, namespace='add-many')),
    url(r'^tagged/', include(tagged_trait_patterns, namespace='tagged-traits')),
    url(r'^all/$', views.TagList.as_view(), name='list'),
    url(r'^autocomplete/$', views.TagAutocomplete.as_view(), name='autocomplete'),
    url(r'^how-to/$', TemplateView.as_view(template_name="tags/how-to.html"), name='how-to'),
]