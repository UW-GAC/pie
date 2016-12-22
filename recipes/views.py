"""View functions and classes for the trait_browser app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import UnitRecipeForm, HarmonizationRecipeForm


@login_required
def new_recipe(request, recipe_type):
    """View for creating new UnitRecipe or HarmonizationRecipe objects."""  
    if recipe_type == 'unit':
        recipe_form = UnitRecipeForm
    elif recipe_type == 'harmonization':
        recipe_form = HarmonizationRecipeForm
    if request.method == 'POST':
        form = recipe_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.creator = request.user
            instance.last_modifier = request.user
            instance.save()
            form.save_m2m() # Have to save the m2m fields manually because of using commit=False above.
    else:
        form = recipe_form()
    return render(request, 'recipes/new_recipe_form.html', {'form': form})
