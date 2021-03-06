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
    # factoryboy provides Fuzzy attributes that can do the same thing, but they are being deprecated.
    status = models.DCCReview.STATUS_CONFIRMED
    creator = factory.SubFactory(UserFactory)
    # Set comment based on the status field.
    comment = factory.Maybe(
        'status',
        yes_declaration='',
        no_declaration=factory.Faker('sentence')
    )

    class Meta:
        model = models.DCCReview


class StudyResponseFactory(factory.DjangoModelFactory):
    """Factory for StudyResponse objects using Faker data."""

    dcc_review = factory.SubFactory(DCCReviewFactory, status=models.DCCReview.STATUS_FOLLOWUP)
    # factoryboy provides Fuzzy attributes that can do the same thing, but they are being deprecated.
    status = models.StudyResponse.STATUS_AGREE
    creator = factory.SubFactory(UserFactory)
    comment = factory.Maybe(
        'status',
        yes_declaration='',
        no_declaration=factory.Faker('sentence')
    )

    class Meta:
        model = models.StudyResponse


class DCCDecisionFactory(factory.DjangoModelFactory):
    """Factory for DCCDecision objects using Faker data."""

    dcc_review = factory.SubFactory(DCCReviewFactory, status=models.DCCReview.STATUS_FOLLOWUP)
    # If you want a dcc_review with a study response, you will need to specify that explicitly.
    decision = models.DCCDecision.DECISION_REMOVE
    creator = factory.SubFactory(UserFactory)
    comment = factory.Faker('sentence')

    class Meta:
        model = models.DCCDecision
