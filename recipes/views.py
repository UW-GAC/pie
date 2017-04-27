"""View functions and classes for the trait_browser app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, CreateView, UpdateView

from braces.views import LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, GroupRequiredMixin
from dal import autocomplete

from recipes.tables import *
from trait_browser.tables import *
from .forms import *
from .models import *


unit_invalid_message = u'Something went wrong. {} was not saved.'.format(UnitRecipe._meta.verbose_name.title())
harmonization_invalid_message = u'Something went wrong. {} was not saved.'.format(HarmonizationRecipe._meta.verbose_name.title())
formattable_valid_message = u'{} {} {}d!'


class OwnerQuerysetMixin(object):
    """Mixin to restrict views to object instances the logged-in user is the creator of."""
    
    def get_queryset(self):
        queryset = super(OwnerQuerysetMixin, self).get_queryset()
        queryset = queryset.filter(creator=self.request.user)
        return queryset


class CreateUnitRecipe(LoginRequiredMixin, GroupRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, CreateView):
    """Create form view class for UnitRecipe creation, used with UnitRecipeModelForm.
    
    LoginRequiredMixin - requires user to be logged in to access this view
    UserFormKwargsMixin - adds the logged in user as an arg in the form's kwargs, so the form can access it
    FormMessagesMixin - adds messages (using the builtin messages app) when form is invalid or valid
    """
    
    model = UnitRecipe
    form_class = UnitRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = unit_invalid_message
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True
    
    def form_valid(self, form):
        """Custom processing for valid forms.
        
        Sets current user as the UnitRecipe's creator and last_modifier.
        """
        form.instance.creator = self.request.user
        form.instance.last_modifier = self.request.user
        return super(CreateUnitRecipe, self).form_valid(form)
    
    def get_form_valid_message(self):
        """Add a session message about creation success."""
        return formattable_valid_message.format(UnitRecipe._meta.verbose_name, self.object.name, 'create')


class CreateHarmonizationRecipe(LoginRequiredMixin, GroupRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, CreateView):
    """Create form view class for HarmonizationRecipe creation, used with HarmonizationRecipeModelForm.
        
    LoginRequiredMixin - requires user to be logged in to access this view
    UserFormKwargsMixin - adds the logged in user as an arg in the form's kwargs, so the form can access it
    FormMessagesMixin - adds messages (using the builtin messages app) when form is invalid or valid
    """
    model = HarmonizationRecipe
    form_class = HarmonizationRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = harmonization_invalid_message
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        """Custom processing for valid forms.
        
        Sets current user as the HarmonizationRecipe's creator and last_modifier.
        """
        form.instance.creator = self.request.user
        form.instance.last_modifier = self.request.user
        return super(CreateHarmonizationRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        """Add a session message about creation success."""
        return formattable_valid_message.format(HarmonizationRecipe._meta.verbose_name.title(), self.object.name, 'create')


class UpdateUnitRecipe(LoginRequiredMixin, GroupRequiredMixin, OwnerQuerysetMixin, UserFormKwargsMixin, FormMessagesMixin, UpdateView):
    """Update form view class for UnitRecipe editing, used with UnitRecipeModelForm.
    
    LoginRequiredMixin - requires user to be logged in to access this view
    OwnerQuerysetMixin - restricts the allowed objects to those the logged in user is an owner of (can only edit their own objects)
    UserFormKwargsMixin - adds the logged in user as an arg in the form's kwargs, so the form can access it
    FormMessagesMixin - adds messages (using the builtin messages app) when form is invalid or valid   
    """
    model = UnitRecipe
    form_class = UnitRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = unit_invalid_message
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        """Custom processing for valid forms.
        
        Sets current user as the UnitRecipe's last_modifier.
        """
        form.instance.last_modifier = self.request.user
        # TODO: Add code here to make a new UnitRecipe instance, with a higher version number.
        return super(UpdateUnitRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        """Add a session message about editing success."""
        return formattable_valid_message.format(UnitRecipe._meta.verbose_name.title(), self.object.name, 'save')


class UpdateHarmonizationRecipe(LoginRequiredMixin, GroupRequiredMixin, OwnerQuerysetMixin, UserFormKwargsMixin, FormMessagesMixin, UpdateView):
    """Update form view class for HarmonizationRecipe editing, used with HarmonizationRecipeModelForm.
    
    LoginRequiredMixin - requires user to be logged in to access this view
    OwnerQuerysetMixin - restricts the allowed objects to those the logged in user is an owner of (can only edit their own objects)
    UserFormKwargsMixin - adds the logged in user as an arg in the form's kwargs, so the form can access it
    FormMessagesMixin - adds messages (using the builtin messages app) when form is invalid or valid   
    """
    model = HarmonizationRecipe
    form_class = HarmonizationRecipeForm
    template_name = 'recipes/recipe_form.html'
    form_invalid_message = harmonization_invalid_message
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True

    def form_valid(self, form):
        """Custom processing for valid forms.
        
        Sets current user as the HarmonizationRecipe's last_modifier.
        """
        form.instance.last_modifier = self.request.user
        # TODO: Add code here to make a new HarmonizationRecipe instance, with a higher version number.
        return super(UpdateHarmonizationRecipe, self).form_valid(form)

    def get_form_valid_message(self):
        """Add a session message about editing success."""
        return formattable_valid_message.format(HarmonizationRecipe._meta.verbose_name.title(), self.object.name, 'save')


class UnitRecipeDetail(LoginRequiredMixin, GroupRequiredMixin, OwnerQuerysetMixin, DetailView):
    """Detail view class for UnitRecipe.
    
    LoginRequiredMixin - requires user to be logged in to access this view
    """
    
    model = UnitRecipe
    context_object_name = 'u_recipe'
    template_name = 'recipes/unit_recipe_detail.html'
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True
    
    def get_context_data(self, **kwargs):
        context = super(UnitRecipeDetail, self).get_context_data(**kwargs)
        context['age_table'] = SourceTraitTable(self.object.age_variables.all())
        context['batch_table'] = SourceTraitTable(self.object.batch_variables.all())
        context['phenotype_table'] = SourceTraitTable(self.object.phenotype_variables.all())
        context['harmonized_phenotype_table'] = HarmonizedTraitTable(self.object.harmonized_phenotype_variables.all())
        return context


class HarmonizationRecipeDetail(LoginRequiredMixin, GroupRequiredMixin, OwnerQuerysetMixin, DetailView):
    """Detail view class for HarmonizationRecipe.

    LoginRequiredMixin - requires user to be logged in to access this view
    """
    
    model = HarmonizationRecipe
    context_object_name = 'h_recipe'
    template_name = 'recipes/harmonization_recipe_detail.html'
    group_required = [u"dcc_analysts", u"dcc_developers", u"recipe_submitters"]
    raise_exception = True
    redirect_unauthenticated_users = True
    
    def get_context_data(self, **kwargs):
        context = super(HarmonizationRecipeDetail, self).get_context_data(**kwargs)
        context['unit_recipe_table'] = UnitRecipeTable(self.object.units.all())
        return context
