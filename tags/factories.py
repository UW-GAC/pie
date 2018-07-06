"""Factory classes for generating test data for each of the tags models."""

import factory
import factory.fuzzy

from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory

from . import models


class TagFactory(factory.DjangoModelFactory):
    """Factory for Tag objects using Faker faked data."""

    title = factory.Sequence(lambda n: 'phenotype tag {}'.format(n))
    description = factory.Faker('sentence')
    instructions = factory.Faker('sentence')
    creator = factory.SubFactory(UserFactory)

    class Meta:
        model = models.Tag
        django_get_or_create = ('title', )


class TaggedTraitFactory(factory.DjangoModelFactory):
    """Factory for TaggedTrait objects using Faker faked data."""

    trait = factory.SubFactory(SourceTraitFactory)
    tag = factory.SubFactory(TagFactory)
    creator = factory.SubFactory(UserFactory)

    class Meta:
        model = models.TaggedTrait


class DCCReviewFactory(factory.DjangoModelFactory):
    """Factory for DCCReview objects using Faker data."""

    tagged_trait = factory.SubFactory(TaggedTraitFactory)
    status = models.DCCReview.STATUS_CONFIRMED
    creator = factory.SubFactory(UserFactory)

    class Meta:
        model = models.DCCReview
