"""URL configuration for the tags app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /tag.
"""

from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views


app_name = 'tags'

add_one_patterns = ([
    url(r'^$', views.TaggedTraitCreate.as_view(), name='main'),
    url(r'^(?P<pk>\d+)/$', views.TaggedTraitCreateByTag.as_view(), name='by-tag'),
], 'add-one', )

add_many_patterns = ([
    url(r'^$', views.ManyTaggedTraitsCreate.as_view(), name='main'),
    url(r'^(?P<pk>\d+)/$', views.ManyTaggedTraitsCreateByTag.as_view(), name='by-tag'),
], 'add-many', )

tag_study_patterns = ([
    url(r'^$', views.TaggedTraitByTagAndStudyList.as_view(), name='list'),
    url(r'^dcc-review/$', views.DCCReviewByTagAndStudySelectFromURL.as_view(), name='dcc-review'),
], 'study', )

tag_patterns = ([
    url(r'^$', views.TagDetail.as_view(), name='detail'),
    url(r'^studies/(?P<pk_study>\d+)/', include(tag_study_patterns)),
], 'tag', )

dcc_review_by_tag_and_study_patterns = ([
    url(r'^select/$', views.DCCReviewByTagAndStudySelect.as_view(), name='select'),
    url(r'^next/$', views.DCCReviewByTagAndStudyNext.as_view(), name='next'),
    url(r'^review/$', views.DCCReviewByTagAndStudy.as_view(), name='review'),
], 'dcc-review')

single_dcc_review_patterns = ([
    url(r'^new/$', views.DCCReviewCreate.as_view(), name='new'),
    url(r'^update/$', views.DCCReviewUpdate.as_view(), name='update'),
], 'dcc-review')

single_tagged_trait_patterns = ([
    url(r'^dcc-review/', include(single_dcc_review_patterns)),
    url(r'^$', views.TaggedTraitDetail.as_view(), name='detail'),
    url(r'^delete/$', views.TaggedTraitDelete.as_view(), name='delete'),
], 'pk')

tagged_trait_patterns = ([
    # url(r'^list', views.TagList.as_view(), name='list'),
    url(r'^dcc-review/', include(dcc_review_by_tag_and_study_patterns)),
    url(r'^(?P<pk>\d+)/', include(single_tagged_trait_patterns)),
    url(r'^by-study/$', views.TaggedTraitTagCountsByStudy.as_view(), name='by-study'),
    url(r'^by-tag/$', views.TaggedTraitStudyCountsByTag.as_view(), name='by-tag'),
], 'tagged-traits', )

urlpatterns = [
    url(r'^(?P<pk>\d+)/', include(tag_patterns)),
    url(r'^add-to-phenotype/', include(add_one_patterns)),
    url(r'^add-to-many-phenotypes/', include(add_many_patterns)),
    url(r'^tagged/', include(tagged_trait_patterns)),
    url(r'^all/$', views.TagList.as_view(), name='list'),
    url(r'^autocomplete/$', views.TagAutocomplete.as_view(), name='autocomplete'),
    url(r'^how-to/$', TemplateView.as_view(template_name="tags/how-to.html"), name='how-to'),
]
