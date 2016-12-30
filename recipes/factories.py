"""Factory classes for generating test data for each of the recipe models."""

import factory
import factory.fuzzy

from .models import HarmonizationRecipe, UnitRecipe


class UnitRecipeFactory(factory.DjangoModelFactory):
    """Factory for UnitRecipe objects using Faker faked data."""
    
    creator = models.ForeignKey(User, related_name='units_created_by')
    last_modifier = models.ForeignKey(User, related_name='units_last_modified_by')
    instructions = models.TextField(verbose_name='harmonization instructions')
    version = models.IntegerField(default=1)
    name = models.CharField(max_length=1000, verbose_name='harmonization unit name')
    
    class Meta:
        model = UnitRecipe
        django_get_or_create = ()

    @factory.post_generation
    def subcohorts(self, create, extracted, **kwargs):
        # Do not add any subcohorts for simple builds.
        if not create:
            return
        # Add subcohorts from a list that was passed in.
        if extracted:
            for subcohort in extracted:
                self.subcohorts.add(subcohort)

    @factory.post_generation
    def subcohorts(self, create, extracted, **kwargs):
        # Do not add any subcohorts for simple builds.
        if not create:
            return
        # Add subcohorts from a list that was passed in.
        if extracted:
            for subcohort in extracted:
                self.subcohorts.add(subcohort)

    @factory.post_generation
    def subcohorts(self, create, extracted, **kwargs):
        # Do not add any subcohorts for simple builds.
        if not create:
            return
        # Add subcohorts from a list that was passed in.
        if extracted:
            for subcohort in extracted:
                self.subcohorts.add(subcohort)
    
    
class HarmonizationRecipeFactory(factory.DjangoModelFactory):