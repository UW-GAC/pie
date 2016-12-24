"""URL configuration for the recipes app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /recipe.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    # Request form views
    url(r'^unit/new/$', views.CreateUnitRecipe.as_view(), name='new_unit'),
    url(r'^harmonization/new/$', views.CreateHarmonizationRecipe.as_view(), name='new_harmonization'),
    url(r'^unit/edit/(?P<pk>\d+)/$', views.UpdateUnitRecipe.as_view(), name='edit_unit'),
    url(r'^harmonization/edit/(?P<pk>\d+)/$', views.UpdateHarmonizationRecipe.as_view(), name='edit_harmonization'),
    # Autocomplete views
    url(r'^unit/autocomplete/$', views.UnitRecipeIDAutocomplete.as_view(), name='unit_autocomplete'),
    # Detail views
    url(r'^unit/detail/(?P<pk>\d+)/$', views.UnitRecipeDetail.as_view(), name='unit_detail'),
    url(r'^harmonization/detail/(?P<pk>\d+)/$', views.HarmonizationRecipeDetail.as_view(), name='harmonization_detail'),
]