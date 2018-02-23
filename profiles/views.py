"""Views for the profiles app."""

from django.contrib.auth.models import Group
from django.views.generic import TemplateView

from braces.views import LoginRequiredMixin

import recipes.models
import recipes.tables
from tags.models import TaggedTrait
from tags.tables import TaggedTraitTableWithDelete, UserTaggedTraitTable
from trait_browser.models import Study


class Profile(LoginRequiredMixin, TemplateView):

    template_name = 'profiles/profile.html'

    def get_context_data(self, **kwargs):
        context = super(Profile, self).get_context_data(**kwargs)
        phenotype_tagger = Group.objects.get(name='phenotype_taggers')
        recipe_submitter = Group.objects.get(name='recipe_submitters')
        is_staff = self.request.user.is_staff
        is_phenotype_tagger = phenotype_tagger in self.request.user.groups.all()
        is_recipe_submitter = recipe_submitter in self.request.user.groups.all()
        # Set up variables for controlling which components show up on the page.
        context['show_tabs'] = False
        context['show_recipes'] = False
        context['show_my_tagged'] = False
        context['show_study_tagged'] = False
        # Show the tab panels only for staff members, phenotype_taggers, or recipe_submitters.
        if is_phenotype_tagger or is_recipe_submitter or is_staff:
            context['show_tabs'] = True
        # Get recipes for recipe_submitters and staff.
        if is_recipe_submitter or is_staff:
            context['show_recipes'] = True
            user_unit_recipes = recipes.models.UnitRecipe.objects.filter(
                creator=self.request.user).order_by('-modified')
            context['unit_recipe_table'] = recipes.tables.UnitRecipeTable(user_unit_recipes)
            user_harmonization_recipes = recipes.models.HarmonizationRecipe.objects.filter(
                creator=self.request.user).order_by('-modified')
            context['harmonization_recipe_table'] = recipes.tables.HarmonizationRecipeTable(user_harmonization_recipes)
        # Get tagged traits and their study names for phenotype_taggers and staff.
        if is_phenotype_tagger or is_staff:
            context['show_my_tagged'] = True
            user_tagged_traits = TaggedTrait.objects.filter(creator=self.request.user)
            context['user_tagged_traits'] = user_tagged_traits
            user_tagged_study_pks = set(user_tagged_traits.values_list(
                'trait__source_dataset__source_study_version__study__pk', flat=True))
            context['user_tagged_study_pks'] = user_tagged_study_pks
            user_tagged_tables = []
            user_tagged_studies = []
            for pk in user_tagged_study_pks:
                user_tagged_studies.append(Study.objects.get(pk=pk))
                user_tagged_tables.append(UserTaggedTraitTable(
                    user_tagged_traits.filter(trait__source_dataset__source_study_version__study__pk=pk)))
            # Force the zip() to evaluate so that tests work properly.
            context['user_tagged_tables'] = list(zip(user_tagged_studies, user_tagged_tables))
        if is_phenotype_tagger:
            context['show_study_tagged'] = True
            taggable_study_tagged_tables = []
            taggable_studies = self.request.user.profile.taggable_studies.all()
            if len(taggable_studies) > 0:
                for study in taggable_studies:
                    taggable_study_tagged_tables.append(TaggedTraitTableWithDelete(
                        TaggedTrait.objects.filter(trait__source_dataset__source_study_version__study=study)))
                # Force the zip() to evaluate so that tests work properly.
                context['taggable_study_tagged_tables'] = list(zip(taggable_studies, taggable_study_tagged_tables))
        return context
