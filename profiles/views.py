"""Views for the profiles app."""

from itertools import groupby

from django.contrib.auth.models import Group
from django.db.models import Count, F
from django.views.generic import TemplateView

from braces.views import LoginRequiredMixin

import recipes.models
import recipes.tables
from tags.models import TaggedTrait


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
            user_taggedtraits = TaggedTrait.objects.current().non_archived().filter(creator=self.request.user)
            user_taggedtraits = user_taggedtraits.values(
                study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
                study_pk=F('trait__source_dataset__source_study_version__study__pk'),
                tag_name=F('tag__title'),
                tag_pk=F('tag__pk'),
                variable_name=F('trait__i_trait_name'),
                dataset_name=F('trait__source_dataset__dataset_name'),
                review=F('dcc_review'),
                taggedtrait_pk=F('pk')).order_by('study_name', 'tag_name', 'variable_name')
            # Group by study.
            user_taggedtraits = groupby(user_taggedtraits,
                                        lambda x: {'study_name': x['study_name'], 'study_pk': x['study_pk']})
            user_taggedtraits = [(key, list(group)) for key, group in user_taggedtraits]
            # Group by tag.
            user_taggedtraits_bytag = []
            for study, study_taggedtraits in user_taggedtraits:
                taggedtraits_groupedbytag = groupby(study_taggedtraits,
                                                    lambda x: {'tag_name': x['tag_name'], 'tag_pk': x['tag_pk']})
                taggedtraits_groupedbytag = [(key, list(group)) for key, group in taggedtraits_groupedbytag]
                user_taggedtraits_bytag.append((study, taggedtraits_groupedbytag))
            context['user_taggedtraits'] = user_taggedtraits_bytag
        # Get tagged traits for all of the studies this user can tag for.
        if is_phenotype_tagger:
            context['show_study_tagged'] = True
            taggable_studies = self.request.user.profile.taggable_studies.all()
            if len(taggable_studies) > 0:
                study_taggedtrait_counts = TaggedTrait.objects.current().non_archived().filter(
                    trait__source_dataset__source_study_version__study__in=taggable_studies)
                study_taggedtrait_counts = study_taggedtrait_counts.values(
                    study_name=F('trait__source_dataset__source_study_version__study__i_study_name'),
                    study_pk=F('trait__source_dataset__source_study_version__study__pk'),
                    tag_name=F('tag__title'),
                    tag_pk=F('tag__pk')).annotate(
                        tt_count=Count('pk')).values(
                            'study_name', 'study_pk', 'tag_name', 'tt_count', 'tag_pk').order_by(
                                'study_name', 'tag_name')
                # Group by study and count.
                study_taggedtrait_counts = groupby(study_taggedtrait_counts,
                                                   lambda x: {'study_name': x['study_name'],
                                                              'study_pk': x['study_pk']})
                study_taggedtrait_counts = [
                    (key, list(group)) for key, group in study_taggedtrait_counts]
                context['study_taggedtrait_counts'] = study_taggedtrait_counts
        return context
