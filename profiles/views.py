"""Views for the profiles app."""

from django.views.generic import TemplateView

from braces.views import LoginRequiredMixin

import recipes.models
import recipes.tables


class Profile(LoginRequiredMixin, TemplateView):

    template_name = 'profiles/profile.html'

    def get_context_data(self, **kwargs):
        context = super(Profile, self).get_context_data(**kwargs)
        user_unit_recipes = recipes.models.UnitRecipe.objects.filter(creator=self.request.user).order_by('-modified')
        context['unit_recipe_table'] = recipes.tables.UnitRecipeTable(user_unit_recipes)
        user_harmonization_recipes = recipes.models.HarmonizationRecipe.objects.filter(
            creator=self.request.user).order_by('-modified')
        context['harmonization_recipe_table'] = recipes.tables.HarmonizationRecipeTable(user_harmonization_recipes)
        return context
