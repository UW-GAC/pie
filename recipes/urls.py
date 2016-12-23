"""URL configuration for the recipes app.

These urlpatterns are included in the project's urlpatterns, so these
urls will show up under /recipe.
"""

from django.conf.urls import url

from . import views


urlpatterns = [
    # Request form views
    url(r'^unit/new/$', views.new_recipe, {'recipe_type': 'unit'}, name='new_unit'),
    url(r'^harmonization/new/$', views.new_recipe, {'recipe_type': 'harmonization'}, name='new_harmonization'),
    # Autocomplete views
    url(r'^unit/autocomplete/$', views.UnitRecipeIDAutocomplete.as_view(), name='unit_autocomplete'),
    # Detail views
    url(r'^unit/detail/(?P<pk>\d+)/$', views.UnitRecipeDetail.as_view(), name='unit_detail'),
    url(r'^harmonization/detail/(?P<pk>\d+)/$', views.HarmonizationRecipeDetail.as_view(), name='harmonization_detail'),
]