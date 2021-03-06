"""URL configuration for the recipes app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /recipe.
"""

from django.conf.urls import include, url

from .views import *


app_name = 'recipes'

unit_patterns = ([
    url(r'^add/$', CreateUnitRecipe.as_view(), name='create'),
    url(r'^(?P<pk>\d+)/edit/$', UpdateUnitRecipe.as_view(), name='edit'),
    url(r'^(?P<pk>\d+)/$', UnitRecipeDetail.as_view(), name='detail'),
], 'unit', )

harmonization_patterns = ([
    url(r'^add/$', CreateHarmonizationRecipe.as_view(), name='create'),
    url(r'^(?P<pk>\d+)/edit/$', UpdateHarmonizationRecipe.as_view(), name='edit'),
    url(r'^(?P<pk>\d+)/$', HarmonizationRecipeDetail.as_view(), name='detail'),
], 'harmonization', )

urlpatterns = [
    url(r'^unit/', include(unit_patterns)),
    url(r'^harmonization/', include(harmonization_patterns)),
]