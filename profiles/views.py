"""Views for the profiles app."""

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
        user_unit_recipes = recipes.models.UnitRecipe.objects.filter(creator=self.request.user).order_by('-modified')
        context['unit_recipe_table'] = recipes.tables.UnitRecipeTable(user_unit_recipes)
        user_harmonization_recipes = recipes.models.HarmonizationRecipe.objects.filter(
            creator=self.request.user).order_by('-modified')
        context['harmonization_recipe_table'] = recipes.tables.HarmonizationRecipeTable(user_harmonization_recipes)
        user_tagged_traits = TaggedTrait.objects.filter(creator=self.request.user)
        study_pks = set(user_tagged_traits.values_list(
            'trait__source_dataset__source_study_version__study__pk', flat=True))
        taggedtrait_tables_by_study = []
        studies = []
        for pk in study_pks:
            studies.append(Study.objects.get(pk=pk))
            taggedtrait_tables_by_study.append(UserTaggedTraitTable(
                user_tagged_traits.filter(trait__source_dataset__source_study_version__study__pk=pk)))
        context['study_table_tuple'] = zip(studies, taggedtrait_tables_by_study)
        all_taggedtrait_tables_by_study = []
        taggable_studies = self.request.user.profile.taggable_studies.all()
        if len(taggable_studies) > 0:
            for study in taggable_studies:
                all_taggedtrait_tables_by_study.append(TaggedTraitTableWithDelete(
                    TaggedTrait.objects.filter(trait__source_dataset__source_study_version__study=study)))
            context['all_taggedtraits_study_table_tuple'] = zip(taggable_studies, all_taggedtrait_tables_by_study)
        return context
