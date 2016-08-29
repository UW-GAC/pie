"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime
from random import randint

from django.utils import timezone

import factory
import factory.fuzzy

from .models import (GlobalStudy, Study, SourceStudyVersion, Subcohort,
                     SourceDataset, SourceDatasetSubcohorts, SourceDatasetUniqueKeys, HarmonizedTraitSet,
                     SourceTrait, HarmonizedTrait, SourceTraitEncodedValue, HarmonizedTraitEncodedValue)

# Use these later for SourceStudyVersion factories.
VISIT_CHOICES = ("one_visit_per_file",
                 "visit_as_variable",
                 "event_data",
                 "not_associated_with_specific_visit",
                 "visit_in_variable_descriptions",
                 "complicated",
                 "missing_visit_information")

class GlobalStudyFactory(factor.DjangoModelFactory):
    """Factory for GlobalStudy objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('company')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    
    class Meta:
        model = GlobalStudy
        django_get_or_create = ('i_id', 'i_name')


class StudyFactory(factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
        
    global_study = factory.SubFactory(GlobalStudy)
    i_accession = randint(1, 999999)
    i_study_name = factory.Faker('company')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))    
    
    class Meta:
        model = Study
        django_get_or_create = ('i_accession', 'i_study_name', )


class SourceStudyVersionFactory(factory.DjangoModelFactory):
    """Factory for SourceStudyVersion objecsts using Faker faked data."""
    
    study = factory.SubFactory(Study)
    i_id = factory.Sequence(lambda n: n)
    i_accession = randint(1, 999999)
    i_version = randint(1, 10)
    i_is_subject_file = factory.Faker('boolean')
    i_study_subject_column = factory.Faker('pystr', max_chars=45)
    i_is_medication_dataset = factory.Faker('boolean')
    i_dbgap_description = factory.Faker('text')
    i_dcc_description = factory.Faker('text')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))    
    
    class Meta:
        model = SourceStudyVersion
        django_get_or_create = ('i_id', )


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
