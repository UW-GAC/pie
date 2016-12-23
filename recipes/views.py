"""View functions and classes for the trait_browser app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from dal import autocomplete

from .forms import UnitRecipeForm, HarmonizationRecipeForm
from .models import UnitRecipe, HarmonizationRecipe


class LoginRequiredMixin(object):
    """Mixin to make class-based views require login for viewing.
    
    To use in a class-based view, add LoginRequiredMixin to the superclass
    definition in the class definition statement.
    
    example:
    class MyView(LoginRequiredMixin, ...):
    """
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


@login_required
def new_recipe(request, recipe_type):
    """View for creating new UnitRecipe or HarmonizationRecipe objects."""  
    if recipe_type == 'unit':
        recipe_form = UnitRecipeForm
        detail_url = 'recipes:unit_detail'
    elif recipe_type == 'harmonization':
        recipe_form = HarmonizationRecipeForm
        detail_url = 'recipes:harmonization_detail'
    if request.method == 'POST':
        form = recipe_form(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.creator = request.user
            instance.last_modifier = request.user
            instance.save()
            form.save_m2m() # Have to save the m2m fields manually because of using commit=False above.
            return redirect(detail_url, pk=instance.pk)
    else:
        form = recipe_form()
    return render(request, 'recipes/new_recipe_form.html', {'form': form})


class UnitRecipeIDAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """View for returning querysets that allow auto-completing UnitRecipe-based form fields.
    
    Used with django-autocomplete-light package.
    """    
    
    def get_queryset(self):
        """Return a queryset of UnitRecipes whose pk starts with the """
        retrieved = UnitRecipe.objects.all()
        if self.q:
            retrieved = retrieved.filter(id__regex=r'^{}'.format(self.q))
        return retrieved


class HarmonizationRecipeDetail(LoginRequiredMixin, DetailView):
    """Detail view class for HarmonizationRecipe."""
    
    model = HarmonizationRecipe
    context_object_name = 'h_recipe'
    template_name = 'recipes/harmonization_recipe_detail.html'
    

class UnitRecipeDetail(LoginRequiredMixin, DetailView):
    """Detail view class for UnitRecipe."""
    
    model = UnitRecipe
    context_object_name = 'u_recipe'
    template_name = 'recipes/unit_recipe_detail.html'