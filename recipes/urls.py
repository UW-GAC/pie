"""URL configuration for the recipes app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /recipe.
"""

from django.conf.urls import include, url

from .views import *

unit_patterns = [
    url(r'^new/$', CreateUnitRecipe.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', UpdateUnitRecipe.as_view(), name='edit'),
    url(r'^detail/(?P<pk>\d+)/$', UnitRecipeDetail.as_view(), name='detail'),    
]

harmonization_patterns = [
    url(r'^new/$', CreateHarmonizationRecipe.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', UpdateHarmonizationRecipe.as_view(), name='edit'),
    url(r'^detail/(?P<pk>\d+)/$', HarmonizationRecipeDetail.as_view(), name='detail'),
]

urlpatterns = [
    url(r'^unit/', include(unit_patterns, namespace='unit')),
    url(r'^harmonization/', include(harmonization_patterns, namespace='harmonization')),
]