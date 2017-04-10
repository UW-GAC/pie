"""Factory classes for generating test data for each of the recipe models."""

import factory
import factory.fuzzy

from core.factories import UserFactory
from .models import *


class UnitRecipeFactory(factory.DjangoModelFactory):
    """Factory for UnitRecipe objects using Faker faked data."""
    
    creator = factory.SubFactory(UserFactory)
    instructions = factory.Faker('sentence')
    version = factory.Faker('random_digit')
    name = factory.Faker('sentence')
    type = factory.Faker('random_element', elements=[el[0] for el in UnitRecipe.TYPE_CHOICES])
    # Make last_modifier the same as creator.
    last_modifier = factory.LazyAttribute(lambda obj: obj.creator)
    
    class Meta:
        model = UnitRecipe
        django_get_or_create = ()

    @factory.post_generation
    def age_variables(self, create, extracted, **kwargs):
        # Do not add any age variables for simple builds.
        if not create:
            return
        # Add age variables from a list that was passed in.
        if extracted:
            for age_var in extracted:
                self.age_variables.add(age_var)

    @factory.post_generation
    def phenotype_variables(self, create, extracted, **kwargs):
        # Do not add any phenotype variables for simple builds.
        if not create:
            return
        # Add phenotype variables from a list that was passed in.
        if extracted:
            for phenotype_var in extracted:
                self.phenotype_variables.add(phenotype_var)

    @factory.post_generation
    def batch_variables(self, create, extracted, **kwargs):
        # Do not add any batch variables for simple builds.
        if not create:
            return
        # Add batch variables from a list that was passed in.
        if extracted:
            for batch_var in extracted:
                self.batch_variables.add(batch_var)

    @factory.post_generation
    def harmonized_phenotype_variables(self, create, extracted, **kwargs):
        # Do not add any phenotype variables for simple builds.
        if not create:
            return
        # Add phenotype variables from a list that was passed in.
        if extracted:
            for phenotype_var in extracted:
                self.phenotype_variables.add(phenotype_var)


class HarmonizationRecipeFactory(factory.DjangoModelFactory):
    """Factory for HarmonizationRecipe objects using Faker faked data."""
    
    creator = factory.SubFactory(UserFactory)
    # Make last_modifier the same as creator.
    last_modifier = factory.LazyAttribute(lambda obj: obj.creator)
    version = factory.Faker('random_digit')
    name = factory.Faker('sentence')
    target_name = factory.Faker('word')
    target_description = factory.Faker('sentence')
    measurement_unit = factory.Faker('rgb_css_color')

    class Meta:
        model = HarmonizationRecipe
        django_get_or_create = ()
    
    @factory.post_generation
    def units(self, create, extracted, **kwargs):
        # Do not add any unit recipes for simple builds.
        if not create:
            return
        # Add unit recipes from a list that was passed in.
        if extracted:
            for unit in extracted:
                self.units.add(unit)