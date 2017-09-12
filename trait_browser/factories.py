"""Factory classes for generating test data for each of the trait_browser models."""

import factory
import pytz
from faker import Factory

from django.utils import timezone

from . import models

fake = Factory.create()


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
        return fake.date_time_between_dates(
            datetime_start=self.i_date_added, datetime_end=timezone.now(), tzinfo=pytz.utc)


class GlobalStudyFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for GlobalStudy objects using Faker faked data."""

    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('company')

    class Meta:
        model = models.GlobalStudy
        django_get_or_create = ('i_id', )


class StudyFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""

    global_study = factory.SubFactory(GlobalStudyFactory)
    i_accession = factory.Faker('random_int', min=1, max=999999)
    i_study_name = factory.Faker('company')

    class Meta:
        model = models.Study
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
        model = models.SourceStudyVersion
        django_get_or_create = ('i_id', )


class SubcohortFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for Subcohort objects using Faker faked data."""

    global_study = factory.SubFactory(GlobalStudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('job')

    class Meta:
        model = models.Subcohort
        django_get_or_create = ('i_id', )


class SourceDatasetFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceDataset objects using Faker faked data."""

    source_study_version = factory.SubFactory(SourceStudyVersionFactory)
    i_id = factory.Sequence(lambda n: n)
    i_accession = factory.Faker('random_int', min=1, max=999999)
    i_version = factory.Faker('random_int', min=1, max=10)
    i_is_subject_file = False
    i_study_subject_column = factory.Faker('pystr', max_chars=45)
    i_dbgap_date_created = factory.Faker('date_time_this_century', tzinfo=pytz.utc)
    # Visit data is NULL by default.
    # i_is_medication_dataset = factory.Faker('boolean')
    # i_dbgap_description = factory.Faker('text')
    # i_dcc_description = factory.Faker('text')
    # i_date_visit_reviewed = factory.Faker('date_time_this_year', tzinfo=pytz.utc)

    class Meta:
        model = models.SourceDataset
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
    i_harmonized_by = factory.Faker('user_name')
    i_git_commit_hash = factory.Faker('sha1')
    i_is_demographic = factory.Faker('boolean')
    i_is_longitudinal = factory.Faker('boolean')

    class Meta:
        model = models.HarmonizedTraitSet
        django_get_or_create = ('i_id', )


class HarmonizationUnitFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizationUnit objects using Faker faked data."""

    i_id = factory.Sequence(lambda n: n)
    i_tag = factory.Faker('word')
    harmonized_trait_set = factory.SubFactory(HarmonizedTraitSetFactory)

    class Meta:
        model = models.HarmonizationUnit
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
    def component_batch_traits(self, create, extracted, **kwargs):
        # Do not add any component_source_traits for simple builds.
        if not create:
            return
        # Add component_source_traits from a list that was passed in.
        if extracted:
            for source_trait in extracted:
                self.component_batch_traits.add(source_trait)

    @factory.post_generation
    def component_age_traits(self, create, extracted, **kwargs):
        # Do not add any component_age_traits for simple builds.
        if not create:
            return
        # Add component_age_traits from a list that was passed in.
        if extracted:
            for source_trait in extracted:
                self.component_age_traits.add(source_trait)

    @factory.post_generation
    def component_harmonized_trait_sets(self, create, extracted, **kwargs):
        # Do not add any component_harmonized_traits for simple builds.
        if not create:
            return
        # Add component_harmonized_traits from a list that was passed in.
        if extracted:
            for harmonized_trait_set in extracted:
                self.component_harmonized_trait_sets.add(harmonized_trait_set)


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
    i_dbgap_description = factory.Faker('sentence')
    i_dbgap_comment = factory.Faker('text')
    i_dbgap_unit = factory.Faker('word')
    i_n_records = factory.Faker('random_int', min=100, max=5000)
    i_n_missing = factory.Faker('random_int', min=0, max=100)  # This will always be less than i_n_records.
    # Visit data is NULL by default.

    class Meta:
        model = models.SourceTrait
        django_get_or_create = ('i_trait_id', )


class HarmonizedTraitFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizedTrait objects using Faker faked data."""

    i_trait_id = factory.Sequence(lambda n: n)
    i_trait_name = factory.Faker('word')
    i_description = factory.Faker('text')

    harmonized_trait_set = factory.SubFactory(HarmonizedTraitSetFactory)
    i_data_type = factory.Faker('random_element', elements=('', 'encoded', 'character', 'double', 'integer', ))
    i_unit = factory.Faker('word')
    i_has_batch = factory.Faker('boolean')
    i_is_unique_key = False

    class Meta:
        model = models.HarmonizedTrait
        django_get_or_create = ('i_trait_id', )

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
    def component_batch_traits(self, create, extracted, **kwargs):
        # Do not add any component_source_traits for simple builds.
        if not create:
            return
        # Add component_source_traits from a list that was passed in.
        if extracted:
            for source_trait in extracted:
                self.component_batch_traits.add(source_trait)

    @factory.post_generation
    def harmonization_units(self, create, extracted, **kwargs):
        # Do not add any harmonization_units for simple builds.
        if not create:
            return
        # Add harmonization_units from a list that was passed in.
        if extracted:
            for harmonization_unit in extracted:
                self.harmonization_units.add(harmonization_unit)

    @factory.post_generation
    def component_harmonized_trait_sets(self, create, extracted, **kwargs):
        # Do not add any component_harmonized_traits for simple builds.
        if not create:
            return
        # Add component_harmonized_traits from a list that was passed in.
        if extracted:
            for harmonized_trait_set in extracted:
                self.component_harmonized_trait_sets.add(harmonized_trait_set)


class SourceTraitEncodedValueFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for SourceTraitEncodedValue objects using Faker faked data."""

    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)

    source_trait = factory.SubFactory(SourceTraitFactory)

    class Meta:
        model = models.SourceTraitEncodedValue


class HarmonizedTraitEncodedValueFactory(SourceDBTimeStampMixin, factory.DjangoModelFactory):
    """Factory for HarmonizedTraitEncodedValue objects using Faker faked data."""

    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)

    harmonized_trait = factory.SubFactory(HarmonizedTraitFactory)

    class Meta:
        model = models.HarmonizedTraitEncodedValue
