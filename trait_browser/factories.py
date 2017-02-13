"""Factory classes for generating test data for each of the trait_browser models."""

from datetime import datetime, timedelta
import factory
from faker import Factory
fake = Factory.create()
import pytz

from django.utils import timezone


from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


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
DETECTED_TYPES = ('encoded', 'character', 'double', 'integer')


class SourceDBTimeStampMixin(factory.DjangoModelFactory):
    
    i_date_added = factory.Faker('date_time_this_month', tzinfo=pytz.utc)
    
    @factory.lazy_attribute
    def i_date_changed(self):
        """Set i_date_changed based on the value of i_date_added."""
        return fake.date_time_between_dates(datetime_start=self.i_date_added, datetime_end=timezone.now(), tzinfo=pytz.utc)
    

class GlobalStudyFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for GlobalStudy objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('company')
    
    class Meta:
        model = GlobalStudy
        django_get_or_create = ('i_id', )


class StudyFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
        
    global_study = factory.SubFactory(GlobalStudyFactory)
    i_accession = factory.Faker('random_int', min=1, max=999999)
    i_study_name = factory.Faker('company')
    
    class Meta:
        model = Study
        django_get_or_create = ('i_accession', )


class SourceStudyVersionFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceStudyVersion objecsts using Faker faked data."""
    
    study = factory.SubFactory(StudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_version = factory.Faker('random_int', min=1, max=10)
    i_participant_set = factory.Faker('random_int', min=1, max=10)
    i_dbgap_date = factory.Faker('date_time_this_century', tzinfo=pytz.utc)
    i_is_prerelease = False
    i_is_deprecated = False
    
    class Meta:
        model = SourceStudyVersion
        django_get_or_create = ('i_id', )


class SubcohortFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for Subcohort objects using Faker faked data."""
    
    study = factory.SubFactory(StudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('job')

    class Meta:
        model = Subcohort
        django_get_or_create = ('i_id', )


class SourceDatasetFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceDataset objects using Faker faked data."""
    
    source_study_version = factory.SubFactory(SourceStudyVersionFactory)
    i_id = factory.Sequence(lambda n: n)
    i_accession = factory.Faker('random_int', min=1, max=999999)
    i_version = factory.Faker('random_int', min=1, max=10)
    i_is_subject_file = False
    i_study_subject_column = factory.Faker('pystr', max_chars=45)
    # Visit data is NULL by default.
    # i_is_medication_dataset = factory.Faker('boolean')
    # i_dbgap_description = factory.Faker('text')
    # i_dcc_description = factory.Faker('text')

    class Meta:
        model = SourceDataset
        django_get_or_create = ('i_id', )
        
    @factory.post_generation
    def subcohorts(self, create, extracted, **kwargs):
        # Do not add any subcohorts for simple builds.
        if not create:
            return
        # Add subcohorts from a list that was passed in.
        if extracted:
            for subcohort in extracted:
                self.subcohorts.add(subcohort)


class HarmonizedTraitSetFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizedTraitSet model using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_trait_set_name = factory.Faker('word')
    i_version = factory.Faker('random_int', min=1, max=10)
    i_description = factory.Faker('text')
    i_flavor = factory.Faker('random_int', min=1, max=10)
    
    class Meta:
        model = HarmonizedTraitSet
        django_get_or_create = ('i_id', )

    @factory.post_generation
    def component_source_traits(self, create, extracted, **kwargs):
        # Do not add any component_source_traits for simple builds.
        if not create:
            return
        # Add component_source_traits from a list that was passed in.
        if extracted:
            for source_trait in extracted:
                self.component_source_traits.add(source_trait)

    @factory.post_generation
    def component_harmonized_traits(self, create, extracted, **kwargs):
        # Do not add any component_harmonized_traits for simple builds.
        if not create:
            return
        # Add component_harmonized_traits from a list that was passed in.
        if extracted:
            for harmonized_trait in extracted:
                self.component_harmonized_traits.add(harmonized_trait)


class SourceTraitFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceTrait objects using Faker faked data."""
    
    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')
    
    source_dataset = factory.SubFactory(SourceDatasetFactory)
    i_detected_type = factory.Faker('random_element', elements=DETECTED_TYPES)
    i_dbgap_type = factory.Faker('word')
    i_dbgap_variable_accession = factory.Faker('random_int', min=1, max=99999999)
    i_dbgap_variable_version = factory.Faker('random_int', min=1, max=15)
    i_dbgap_comment = factory.Faker('text')
    i_dbgap_unit = factory.Faker('word')
    i_n_records = factory.Faker('random_int', min=100, max=5000)
    i_n_missing = factory.Faker('random_int', min=0, max=100) # This will always be less than i_n_records.
    # Visit data is NULL by default.
    
    class Meta:
        model = SourceTrait
        django_get_or_create = ('i_trait_id', )


class HarmonizedTraitFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizedTrait objects using Faker faked data."""
    
    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')
    
    harmonized_trait_set = factory.SubFactory(HarmonizedTraitSetFactory)
    i_data_type = factory.Faker('random_element', elements=('', 'encoded', 'character', 'double', 'integer', ))
    i_unit = factory.Faker('word')
    i_is_unique_key = False
    
    class Meta:
        model = HarmonizedTrait
        django_get_or_create = ('i_trait_id', )

    # @factory.post_generation
    # def component_source_traits(self, create, extracted, **kwargs):
    #     # Do not add any component_source_traits for simple builds.
    #     if not create:
    #         return
    #     # Add component_source_traits from a list that was passed in.
    #     if extracted:
    #         for source_trait in extracted:
    #             self.component_source_traits.add(source_trait)
    # 
    # @factory.post_generation
    # def component_harmonized_traits(self, create, extracted, **kwargs):
    #     # Do not add any component_harmonized_traits for simple builds.
    #     if not create:
    #         return
    #     # Add component_harmonized_traits from a list that was passed in.
    #     if extracted:
    #         for harmonized_trait in extracted:
    #             self.component_harmonized_traits.add(harmonized_trait)


class SourceTraitEncodedValueFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceTraitEncodedValue objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    source_trait = factory.SubFactory(SourceTraitFactory) 
       
    class Meta:
        model = SourceTraitEncodedValue


class HarmonizedTraitEncodedValueFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizedTraitEncodedValue objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    harmonized_trait = factory.SubFactory(HarmonizedTraitFactory) 
       
    class Meta:
        model = HarmonizedTraitEncodedValue