"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime
from random import randint

from django.utils import timezone

import factory
import factory.fuzzy

from .models import Study, SourceTrait, SourceEncodedValue


class StudyFactory(factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
        
    name = factory.Faker('company')
    study_id = factory.Sequence(lambda n: n)
    phs = randint(1, 999999)
    
    class Meta:
        model = Study
        django_get_or_create = ('name', 'study_id', )


class SourceTraitFactory(factory.DjangoModelFactory):
    """Factory for SourceTrait objects using Faker faked data."""
    
    dcc_trait_id = factory.Sequence(lambda n: n)
    name = factory.Faker('word')
    description = factory.Faker('text')
    data_type = factory.fuzzy.FuzzyChoice(SourceTrait.DATA_TYPES)
    unit = factory.Faker('word')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    study = factory.SubFactory(StudyFactory)
    
    phv = randint(1, 99999999)
    pht = randint(1, 999999)
    study_version = randint(1,9)
    dataset_version = randint(1, 9)
    variable_version = randint(1, 9)
    participant_set = randint(1, 9)
    
    class Meta:
        model = SourceTrait
        django_get_or_create = ('dcc_trait_id', )


class SourceEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for SourceEncodedValue objects using Faker faked data."""
    
    category = factory.Faker('word')
    value = factory.Faker('text', max_nb_chars=50)
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    source_trait = factory.SubFactory(SourceTraitFactory) 
       
    class Meta:
        model = SourceEncodedValue
