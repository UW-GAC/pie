"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime

from django.utils import timezone

import factory
import factory.fuzzy

from .models import Study, SourceTrait, SourceEncodedValue


class StudyFactory(factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
    
    class Meta:
        model = Study
        django_get_or_create = ('name', 'study_id', )
        
    name = factory.Faker('company')
    study_id = factory.Sequence(lambda n: n)
    dbgap_id = factory.Sequence(lambda n: 'phs{0}'.format(n))


class SourceTraitFactory(factory.DjangoModelFactory):
    """Factory for SourceTrait objects using Faker faked data."""
    
    class Meta:
        model = SourceTrait
        django_get_or_create = ('dcc_trait_id', )
    
    dcc_trait_id = factory.Sequence(lambda n: n)
    name = factory.Faker('word')
    description = factory.Faker('text')
    data_type = factory.fuzzy.FuzzyChoice(SourceTrait.DATA_TYPES)
    unit = factory.Faker('word')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    phs_string = factory.Sequence(lambda n: 'phs{0}'.format(n))
    phv_string = factory.Sequence(lambda n: 'phv{0}'.format(n))
    study = factory.SubFactory(StudyFactory)


class SourceEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for SourceEncodedValue objects using Faker faked data."""
    
    class Meta:
        model = SourceEncodedValue
    
    category = factory.Faker('word')
    value = factory.Faker('text', max_nb_chars=50)
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    source_trait = factory.SubFactory(SourceTraitFactory)