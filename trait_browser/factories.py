"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime
from random import choice, randint

from django.utils import timezone

import factory
import factory.fuzzy

from .models import (GlobalStudy, Study, SourceStudyVersion, Subcohort,
                     SourceDataset, SourceDatasetSubcohorts, SourceDatasetUniqueKeys, HarmonizedTraitSet,
                     SourceTrait, HarmonizedTrait, SourceTraitEncodedValue, HarmonizedTraitEncodedValue)

# Use these later for SourceStudyVersion factories.
VISIT_CHOICES = ('one_visit_per_file',
                 'visit_as_variable',
                 'event_data',
                 'not_associated_with_specific_visit',
                 'visit_in_variable_descriptions',
                 'complicated',
                 'missing_visit_information',
                 '')
VISIT_NUMBERS = tuple([str(el) for el in range(1, 20)]) + ('', )

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
    i_version = randint(1, 10)
    i_participant_set = randint(1, 10)
    i_dbgap_date = timezone.make_aware(factory.Faker('date_time_this_decade'))
    i_is_prerelease = False
    i_is_deprecated = False
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))    
    
    class Meta:
        model = SourceStudyVersion
        django_get_or_create = ('i_id', )


class SubcohortFactory(factory.DjangoModelFactory):
    """Factory for Subcohort objects using Faker faked data."""
    
    study = factory.SubFactory(Study)
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('job')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))    

    class Meta:
        model = Subcohort
        django_get_or_create = ('i_id', )


class SourceDatasetFactory(factory.DjangoModelFactory):
    """Factory for SourceDataset objects using Faker faked data."""
    
    source_study_version = factory.SubFactory(SourceStudyVersion)
    i_id = factory.Sequence(lambda n: n)
    i_accession = randint(1, 999999)
    i_version = randint(1, 10)
    i_is_subject_file = False
    i_study_subject_column = factory.Faker('pystr', max_chars=45)
    i_is_medication_dataset = factory.Faker('boolean')
    i_dbgap_description = factory.Faker('text')
    i_dcc_description = factory.Faker('text')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))    

    class Meta:
        model = SourceDataset
        django_get_or_create = ('i_id', )


class SourceDatasetSubcohortsFactory(factory.DjangoModelFactory):
    """Factory for SourceDatasetSubcohorts objects using Faker faked data."""
    
    source_dataset = factory.SubFactory(SourceDataset)
    subcohort = factory.SubFactory(Subcohort)
    i_id = factory.Sequence(lambda n: n)
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    
    class Meta:
        model = SourceDatasetSubcohorts
        django_get_or_create = ('i_id', )


class SourceDatasetUniqueKeysFactory(factory.DjangoModelFactory):
    """Factory for SourceDatasetUniqueKeys objects using Faker faked data."""
    
    source_dataset = factory.SubFactory(SourceDataset)
    source_trait = factory.SubFactory(SourceTrait)
    i_id = factory.Sequence(lambda n: n)
    i_is_visit_column = factory.Faker('boolean', chance_of_getting_true=10)
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    
    class Meta:
        model = SourceDatasetUniqueKeys
        django_get_or_create = ('i_id', )


class HarmonizedTraitSetFactory(factory.DjangoModelFactory):
    """Factory for HarmonizedTraitSet model using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_trait_set_name = factory.Faker('word')
    i_version = factory.Sequence(lambda n: n)
    i_description = factory.Faker('text')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    
    class Meta:
        model = HarmonizedTraitSet
        django_get_or_create = ('i_id', )


class SourceTraitFactory(factory.DjangoModelFactory):
    """Factory for SourceTrait objects using Faker faked data."""
    
    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    
    source_dataset = factory.SubFactory(SourceDataset)
    i_detected_type = factory.Faker('word')
    i_dbgap_type = factory.Faker('word')
    i_visit_number = choice(VISIT_NUMBERS)
    i_dbgap_variable_accession = randint(1, 99999999)
    i_dbgap_variable_version = randint(1, 15)
    i_dbgap_comment = factory.Faker('text')
    i_dbgap_unit = factory.Faker('word')
    i_n_records = randint(100, 5000)
    i_n_missing = randint(0, 100) # This will always be less than i_n_records.
    
    class Meta:
        model = SourceTrait
        django_get_or_create = ('i_trait_id', )


class SourceEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for SourceEncodedValue objects using Faker faked data."""
    
    category = factory.Faker('word')
    value = factory.Faker('text', max_nb_chars=50)
    web_date_added = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(2016, 1, 1)))
    source_trait = factory.SubFactory(SourceTraitFactory) 
       
    class Meta:
        model = SourceEncodedValue
