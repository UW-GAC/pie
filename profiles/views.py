from django.shortcuts import render
from django.contrib.auth.decorators import login_required

import recipes.models
import recipes.tables
from . import models
from . import tables


@login_required
def profile(request):
    page_title = 'My profile'
    user_unit_recipes = recipes.models.UnitRecipe.objects.filter(creator=request.user).order_by('-modified')
    unit_recipe_table = recipes.tables.UnitRecipeTable(user_unit_recipes)
    user_harmonization_recipes = recipes.models.HarmonizationRecipe.objects.filter(
        creator=request.user).order_by('-modified')
    harmonization_recipe_table = recipes.tables.HarmonizationRecipeTable(user_harmonization_recipes)

    if request.method == "POST":
        # remove saved searches
        if 'search_type' in request.POST:
            search_removal_list = request.POST.getlist('search_id')
            for search_id in search_removal_list:
                saved_search = models.SavedSearchMeta.objects.get(search_id=search_id)
                saved_search.active = False
                saved_search.save()

    savedsource = tables.SourceSearchTable(build_usersearches(request.user.id, 'source'), request=request)
    savedharmonized = tables.HarmonizedSearchTable(build_usersearches(request.user.id, 'harmonized'), request=request)

    return render(
        request,
        'profiles/profile.html',
        {'page_title': page_title, 'savedsource': savedsource, 'savedharmonized': savedharmonized,
         'unit_recipe_table': unit_recipe_table, 'harmonization_recipe_table': harmonization_recipe_table}
    )


def build_usersearches(user_id, search_type):
    """Return a list of dictionaries for building user's saved searches."""
    searches = models.Search.objects.select_related().filter(
        profile__user_id=user_id,
        search_type=search_type,
        savedsearchmeta__active=True)
    data = [
        {
            'search_id': x.id,
            'search_text': x.param_text,
            # only used in SourceSearchTable
            'search_studies': len([y['i_study_name'] for y in x.param_studies.values()]),
            'study_name_string': '<br>'.join([y['i_study_name'] for y in x.param_studies.values()]),
            'search_url': x.build_search_url(),
            'date_saved': x.created
        }
        for x in searches
    ]
    return data
