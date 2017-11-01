"""URL configuration for the tags app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /tag.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^detail/(?P<pk>\d+)/$', views.TagDetail.as_view(), name='detail'),
    url(r'^tagging/$', views.TaggedTraitCreate.as_view(), name='tagging'),
]
