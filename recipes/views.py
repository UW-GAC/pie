"""View functions and classes for the trait_browser app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, CreateView, UpdateView

from braces.views import LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin
from dal import autocomplete

from .forms import UnitRecipeForm, HarmonizationRecipeForm
from .models import UnitRecipe, HarmonizationRecipe


unit_invalid_message = u'Something went wrong. {} was not saved.'.format(UnitRecipe._meta.verbose_name.title())
harmonization_invalid_message = u'Something went wrong. {} was not saved.'.format(HarmonizationRecipe._meta.verbose_name.title())
formattable_valid_message = u'{} {} {}d!'


class CreateUnitRecipe(LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, CreateView):
    """ """
    model = UnitRecipe
    form_class = UnitRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = unit_invalid_message

    def form_valid(self, form):
        # Add current user as the creator and last_modifier.
        form.instance.creator = self.request.user
        form.instance.last_modifier = self.request.user
        return super(CreateUnitRecipe, self).form_valid(form)
    
    def get_form_valid_message(self):
        return formattable_valid_message.format(UnitRecipe._meta.verbose_name, self.object.name, 'create')


class CreateHarmonizationRecipe(LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, CreateView):
    """ """
    model = HarmonizationRecipe
    form_class = HarmonizationRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = harmonization_invalid_message

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.last_modifier = self.request.user
        return super(CreateHarmonizationRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        return formattable_valid_message.format(HarmonizationRecipe._meta.verbose_name.title(), self.object.name, 'create')


class UpdateUnitRecipe(LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, UpdateView):
    """ """
    model = UnitRecipe
    form_class = UnitRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = unit_invalid_message

    def form_valid(self, form):
        form.instance.last_modifier = self.request.user
        return super(UpdateUnitRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        return formattable_valid_message.format(UnitRecipe._meta.verbose_name.title(), self.object.name, 'save')


class UpdateHarmonizationRecipe(LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, UpdateView):
    """ """
    model = HarmonizationRecipe
    form_class = HarmonizationRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = harmonization_invalid_message

    def form_valid(self, form):
        form.instance.last_modifier = self.request.user
        return super(UpdateHarmonizationRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        return formattable_valid_message.format(HarmonizationRecipe._meta.verbose_name.title(), self.object.name, 'save')


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