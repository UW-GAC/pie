"""Factory classes for generating test data for each of the trait_browser models."""

from copy import copy
from datetime import datetime
from random import randrange, sample

from django.utils import timezone

import factory
import factory.fuzzy

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

class GlobalStudyFactory(factory.DjangoModelFactory):
    """Factory for GlobalStudy objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_name = factory.Faker('company')
    
    class Meta:
        model = GlobalStudy
        django_get_or_create = ('i_id', )


class StudyFactory(factory.DjangoModelFactory):
    """Factory for Study objects using Faker faked data."""
        
    global_study = factory.SubFactory(GlobalStudyFactory)
    i_accession = factory.Faker('random_int', min=1, max=999999)
    i_study_name = factory.Faker('company')
    
    class Meta:
        model = Study
        django_get_or_create = ('i_accession', )


class SourceStudyVersionFactory(factory.DjangoModelFactory):
    """Factory for SourceStudyVersion objecsts using Faker faked data."""
    
    study = factory.SubFactory(StudyFactory)
    i_id = factory.Sequence(lambda n: n)
    i_version = factory.Faker('random_int', min=1, max=10)
    i_participant_set = factory.Faker('random_int', min=1, max=10)
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


class HarmonizedTraitSetFactory(factory.DjangoModelFactory):
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


class SourceTraitFactory(factory.DjangoModelFactory):
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


class HarmonizedTraitFactory(factory.DjangoModelFactory):
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


class SourceTraitEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for SourceTraitEncodedValue objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    source_trait = factory.SubFactory(SourceTraitFactory) 
       
    class Meta:
        model = SourceTraitEncodedValue


class HarmonizedTraitEncodedValueFactory(factory.DjangoModelFactory):
    """Factory for HarmonizedTraitEncodedValue objects using Faker faked data."""
    
    i_id = factory.Sequence(lambda n: n)
    i_category = factory.Faker('word')
    i_value = factory.Faker('text', max_nb_chars=50)
    
    harmonized_trait = factory.SubFactory(HarmonizedTraitFactory) 
       
    class Meta:
        model = HarmonizedTraitEncodedValue


def build_test_db(n_global_studies, n_subcohort_range, n_dataset_range, n_trait_range, n_enc_value_range):
    """Make a complete set of test data in the db, using the factory functions from above.
    
    n_subcohort_range -- tuple; (min, max) value to pick for n_subcohorts
    n_global_studies -- int; number of global studies to simulate
    n_dataset_range -- tuple; (min, max) value to pick for n_datasets
    n_trait_range -- tuple; (min, max) value to pick for n_traits; min value must be 2 or more;
        number of harmonized traits will use this range, but add 4 for necessary test cases to include
    n_enc_value_range -- tuple; (min, max) value to pick for number of encoded values to simulate for one trait
    
    """
    if n_global_studies < 3:
        raise ValueError('{} is too small for the n_global_studies argument. Try a value higher than 2.'.format(n_global_studies))
    if n_trait_range[0] < 2:
        raise ValueError('{} is too small for the minimum n_trait_range argument. Try a value higher than 1.'.format(n_trait_range[0]))

    global_studies = GlobalStudyFactory.create_batch(n_global_studies)
    # There will be global studies with 1, 2, or 3 linked studies.
    for (i, gs) in enumerate(GlobalStudy.objects.all()):
        if i == 1:
            StudyFactory.create_batch(2, global_study=gs)
        elif i == 2:
            StudyFactory.create_batch(3, global_study=gs)
        else:
            StudyFactory.create(global_study=gs)
    studies = Study.objects.all()
    for st in studies:
        SourceStudyVersionFactory.create(study=st)
        SubcohortFactory.create_batch(randrange(n_subcohort_range[0], n_subcohort_range[1]), study=st)
    source_study_versions = SourceStudyVersion.objects.all()
    for ssv in source_study_versions:
        SourceDatasetFactory.create_batch(randrange(n_dataset_range[0], n_dataset_range[1]), source_study_version=ssv)
    source_datasets = SourceDataset.objects.all()
    for sd in source_datasets:
        # Make source traits.
        SourceTraitFactory.create_batch(randrange(n_trait_range[0], n_trait_range[1]), source_dataset=sd)
        # Choose random set of subcohorts to add to the dataset.
        possible_subcohorts = list(Subcohort.objects.filter(study=sd.source_study_version.study).all())
        if len(possible_subcohorts) > 0:
            if len(possible_subcohorts) > 1:
                add_subcohorts = sample(possible_subcohorts, randrange(1, len(possible_subcohorts) + 1))
            else:
                add_subcohorts = possible_subcohorts
            for sc in add_subcohorts:
                sd.subcohorts.add(sc)
    source_traits = SourceTrait.objects.all()
    for st in SourceTrait.objects.filter(i_detected_type='encoded'):
        SourceTraitEncodedValueFactory.create_batch(randrange(n_enc_value_range[0], n_enc_value_range[1]), source_trait=st)
    # Add another source_study_version to one study. Use the same datasets, traits, 
    # encoded values, etc. Maybe change or add a few traits and one dataset.
    
    # Duplicate a source study version.
    ssv_study = studies[len(studies) - 1]
    ssv_to_dup = ssv_study.sourcestudyversion_set.all()[0]
    existing_ssv_ids = [ssv.i_id for ssv in SourceStudyVersion.objects.all()]
    available_ssv_ids = list(set(range(1, 500)) - set(existing_ssv_ids))
    dup_ssv = copy(ssv_to_dup)
    dup_ssv.i_id = available_ssv_ids[0]
    dup_ssv.i_version = dup_ssv.i_version + 1
    dup_ssv.created = None
    dup_ssv.modified = None
    dup_ssv.save()
    # Duplicate datasets.
    datasets_to_dup = ssv_to_dup.sourcedataset_set.all()
    existing_dataset_ids = [sd.i_id for sd in SourceDataset.objects.all()]
    available_dataset_ids = iter(list(set(range(1, 10000)) - set(existing_dataset_ids)))
    duped_datasets = []
    for ds in datasets_to_dup:
        new_ds = copy(ds)
        new_ds.i_id = next(available_dataset_ids)
        new_ds.source_study_version = dup_ssv
        new_ds.created = None
        new_ds.modified = None
        new_ds.save()
        new_ds.subcohorts.add(*ds.subcohorts.all())
        duped_datasets.append(new_ds)
    # Duplicate source traits.
    existing_trait_ids = [tr.i_trait_id for tr in SourceTrait.objects.all()]
    available_trait_ids = iter(list(set(range(1, 100000)) - set(existing_trait_ids)))
    existing_source_trait_encoded_value_ids = [ev.i_id for ev in SourceTraitEncodedValue.objects.all()]
    available_source_trait_encoded_value_ids = iter(list(set(range(1, 1000000)) - set(existing_source_trait_encoded_value_ids)))
    # available_source_trait_encoded_value_ids = set(range(1, 1000000)) - set(existing_source_trait_encoded_value_ids)
    # print(existing_source_trait_encoded_value_ids)
    # print(available_source_trait_encoded_value_ids)
    for (old_ds, new_ds) in zip(datasets_to_dup, duped_datasets):
        traits_to_dup = old_ds.sourcetrait_set.all()
        for tr in traits_to_dup:
            encoded_values_to_dup = tr.sourcetraitencodedvalue_set.all()
            new_tr = copy(tr)
            new_tr.i_trait_id = next(available_trait_ids)
            new_tr.source_dataset = new_ds
            new_tr.created = None
            new_tr.save()
            # Duplicate encoded values.
            if len(encoded_values_to_dup) > 0:
                for val in encoded_values_to_dup:
                    new_val = copy(val)
                    new_val.i_id = next(available_source_trait_encoded_value_ids)
                    new_val.source_trait = tr
                    new_val.created = None
                    new_val.modified = None
                    new_val.save()
    # Add a completely new dataset to this study version.
    new_dataset = SourceDatasetFactory.create(source_study_version=dup_ssv)
    new_traits = SourceTraitFactory.create_batch(10, source_dataset=new_dataset)
    for tr in new_traits:
        if tr.i_detected_type == 'encoded':
            for n in range(randrange(n_enc_value_range[0], n_enc_value_range[1])):
                SourceTraitEncodedValueFactory.create(i_id=next(available_source_trait_encoded_value_ids), source_trait=tr)
    
    # Add simulated harmonized traits.
    for nh in range(randrange(n_trait_range[0], n_trait_range[1])):
        # component_source_traits = [sample(list(SourceTrait.objects.filter(source_dataset__source_study_version__study=study)), 1)[0] for study in Study.objects.all()]
        # HarmonizedTraitFactory.create(component_source_traits=component_source_traits)
        HarmonizedTraitFactory.create()
    # # Add one harmonized trait that has component harmonized and component source traits.
    # component_source_traits = [sample(list(SourceTrait.objects.filter(source_dataset__source_study_version__study=study)), 1)[0] for study in Study.objects.all()]
    # component_harmonized_traits = sample(list(HarmonizedTrait.objects.all()), 2)
    # HarmonizedTraitFactory.create(component_source_traits=component_source_traits, component_harmonized_traits=component_harmonized_traits)
    # # Add one harmonized trait that only uses source traits from *some* of the studies.
    # component_source_traits = [sample(list(SourceTrait.objects.filter(source_dataset__source_study_version__study=study)), 1)[0] for study in Study.objects.all()]
    # component_source_traits = sample(component_source_traits, int(len(component_source_traits) * 0.8))
    # HarmonizedTraitFactory.create(component_source_traits=component_source_traits)
    # Add a pair of harmonized traits in the same trait set.
    h_trait_set = HarmonizedTraitSetFactory.create()
    h_trait1 = HarmonizedTraitFactory.create(harmonized_trait_set=h_trait_set)
    h_trait2 = HarmonizedTraitFactory.create(harmonized_trait_set=h_trait_set, i_is_unique_key=True)
    # Make sure there's at least one encoded value trait.
    encoded_harmonized_traits = HarmonizedTrait.objects.filter(i_data_type='encoded')
    if len(encoded_harmonized_traits) < 1:
        # component_source_traits = [sample(list(SourceTrait.objects.filter(source_dataset__source_study_version__study=study)), 1)[0] for study in Study.objects.all()]
        # HarmonizedTraitFactory.create(component_source_traits=component_source_traits, i_data_type='encoded')
        HarmonizedTraitFactory.create(i_data_type='encoded')
    # Add encoded values to all of the encoded value traits.
    for htr in HarmonizedTrait.objects.filter(i_data_type='encoded'):
        for n in range(randrange(n_enc_value_range[0], n_enc_value_range[1])):
            HarmonizedTraitEncodedValueFactory.create_batch(randrange(n_enc_value_range[0], n_enc_value_range[1]), harmonized_trait=htr)
        
    
