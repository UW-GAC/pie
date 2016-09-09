"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime
from random import choice, randint

from django.utils import timezone

import factory
import factory.fuzzy

from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceDatasetSubcohorts, SourceDatasetUniqueKeys, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


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

class GlobalStudyFactory(factory.DjangoModelFactory):
    """Factory for GlobalStudy objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('company')
    
    class Meta:
        model = GlobalStudy
        django_get_or_create = ('i_id', 'i_name')


class StudyFactory(factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
        
    global_study = factory.SubFactory(GlobalStudyFactory)
    i_accession = randint(1, 999999)
    i_study_name = factory.Faker('company')
    
    class Meta:
        model = Study
        django_get_or_create = ('i_accession', 'i_study_name', )


class SourceStudyVersionFactory(factory.DjangoModelFactory):
    """Factory for SourceStudyVersion objecsts using Faker faked data."""
    
    study = factory.SubFactory(StudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_version = randint(1, 10)
    i_participant_set = randint(1, 10)
    i_dbgap_date = factory.fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime(1998, 1, 1), timezone.get_current_timezone()))
    i_is_prerelease = False
    i_is_deprecated = False
    
    class Meta:
        model = SourceStudyVersion
        django_get_or_create = ('i_id', )


class SubcohortFactory(factory.DjangoModelFactory):
    """Factory for Subcohort objects using Faker faked data."""
    
    study = factory.SubFactory(StudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('job')

    class Meta:
        model = Subcohort
        django_get_or_create = ('i_id', )


class SourceDatasetFactory(factory.DjangoModelFactory):
    """Factory for SourceDataset objects using Faker faked data."""
    
    source_study_version = factory.SubFactory(SourceStudyVersionFactory)
    i_id = factory.Sequence(lambda n: n)
    i_accession = randint(1, 999999)
    i_version = randint(1, 10)
    i_is_subject_file = False
    i_study_subject_column = factory.Faker('pystr', max_chars=45)
    i_is_medication_dataset = factory.Faker('boolean')
    i_dbgap_description = factory.Faker('text')
    i_dcc_description = factory.Faker('text')

    class Meta:
        model = SourceDataset
        django_get_or_create = ('i_id', )


class SourceDatasetSubcohortsFactory(factory.DjangoModelFactory):
    """Factory for SourceDatasetSubcohorts objects using Faker faked data."""
    
    source_dataset = factory.SubFactory(SourceDatasetFactory)
    subcohort = factory.SubFactory(SubcohortFactory)
    i_id = factory.Sequence(lambda n: n)
    
    class Meta:
        model = SourceDatasetSubcohorts
        django_get_or_create = ('i_id', )


class HarmonizedTraitSetFactory(factory.DjangoModelFactory):
    """Factory for HarmonizedTraitSet model using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_trait_set_name = factory.Faker('word')
    i_version = factory.Sequence(lambda n: n)
    i_description = factory.Faker('text')
    
    class Meta:
        model = HarmonizedTraitSet
        django_get_or_create = ('i_id', )


class SourceTraitFactory(factory.DjangoModelFactory):
    """Factory for SourceTrait objects using Faker faked data."""
    
    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')
    
    source_dataset = factory.SubFactory(SourceDatasetFactory)
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


class HarmonizedTraitFactory(factory.DjangoModelFactory):
    """Factory for HarmonizedTrait objects using Faker faked data."""
    
    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')
    
    harmonized_trait_set = factory.SubFactory(HarmonizedTraitSetFactory)
    i_data_type = choice(('', 'encoded', 'character', 'double', 'integer', ))
    i_unit = factory.Faker('word')
    i_is_unique_key = factory.Faker('boolean', chance_of_getting_true=10)
    
    class Meta:
        model = HarmonizedTrait
        django_get_or_create = ('i_trait_id', )


class SourceTraitEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for SourceTraitEncodedValue objects using Faker faked data."""
    
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    source_trait = factory.SubFactory(SourceTraitFactory) 
       
    class Meta:
        model = SourceTraitEncodedValue


class HarmonizedTraitEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for HarmonizedTraitEncodedValue objects using Faker faked data."""
    
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    harmonized_trait = factory.SubFactory(HarmonizedTraitFactory) 
       
    class Meta:
        model = HarmonizedTraitEncodedValue


class SourceDatasetUniqueKeysFactory(factory.DjangoModelFactory):
    """Factory for SourceDatasetUniqueKeys objects using Faker faked data."""
    
    source_dataset = factory.SubFactory(SourceDatasetFactory)
    source_trait = factory.SubFactory(SourceTraitFactory)
    i_id = factory.Sequence(lambda n: n)
    i_is_visit_column = factory.Faker('boolean', chance_of_getting_true=10)
    
    class Meta:
        model = SourceDatasetUniqueKeys
        django_get_or_create = ('i_id', )