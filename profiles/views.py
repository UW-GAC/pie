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

    return render(
        request,
        'profiles/profile.html',
        {'page_title': page_title,
         'unit_recipe_table': unit_recipe_table, 'harmonization_recipe_table': harmonization_recipe_table}
    )
