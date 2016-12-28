"""URL configuration for the recipes app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /recipe.
"""

from django.conf.urls import include, url

from . import views

unit_patterns = [
    url(r'^new/$', views.CreateUnitRecipe.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', views.UpdateUnitRecipe.as_view(), name='edit'),
    url(r'^detail/(?P<pk>\d+)/$', views.UnitRecipeDetail.as_view(), name='detail'),    
    url(r'^unit/autocomplete/$', views.UnitRecipeIDAutocomplete.as_view(), name='autocomplete'),
]

harmonization_patterns = [
    url(r'^new/$', views.CreateHarmonizationRecipe.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', views.UpdateHarmonizationRecipe.as_view(), name='edit'),
    url(r'^detail/(?P<pk>\d+)/$', views.HarmonizationRecipeDetail.as_view(), name='detail'),
]

urlpatterns = [
    url(r'^unit/', include(unit_patterns, namespace='unit')),
    url(r'^harmonization/', include(harmonization_patterns, namespace='harmonization')),
]