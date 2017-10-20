"""Contains a function to fill a db with fake data of every model type, for testing."""

from copy import copy
from random import randrange, sample

from django.contrib.auth import get_user_model

from trait_browser import models
from trait_browser import factories

User = get_user_model()
USER_FACTORY_PASSWORD = 'qwerty'


def build_test_db(n_global_studies, n_subcohort_range, n_dataset_range, n_trait_range, n_enc_value_range):
    """Make a complete set of test data in the db, using the factory functions from above.

    n_subcohort_range -- tuple; (min, max) value to pick for n_subcohorts
    n_global_studies -- int; number of global studies to simulate
    n_dataset_range -- tuple; (min, max) value to pick for n_datasets
    n_trait_range -- tuple; (min, max) value to pick for n_traits; min value must be 3 or more;
        number of harmonized traits will use this range, but add some for necessary test cases to include
    n_enc_value_range -- tuple; (min, max) value to pick for number of encoded values to simulate for one trait
    """
    if n_global_studies < 3:
        raise ValueError('{} is too small for the n_global_studies argument. Try a value higher than 2.'.format(n_global_studies))
    if n_trait_range[0] < 3:
        raise ValueError('{} is too small for the minimum n_trait_range argument. Try a value higher than 1.'.format(n_trait_range[0]))
    if (n_dataset_range[1] - n_dataset_range[0] < 1):
        raise ValueError('Values for n_dataset_range are too close together. max n_dataset_range must be greater than min n_dataset_range.')
    if (n_trait_range[1] - n_trait_range[0] < 1):
        raise ValueError('Values for n_trait_range are too close together. max n_trait_range must be greater than min n_trait_range.')
    global_studies = factories.GlobalStudyFactory.create_batch(n_global_studies)
    # There will be global studies with 1, 2, or 3 linked studies.
    for (i, gs) in enumerate(models.GlobalStudy.objects.all()):
        factories.SubcohortFactory.create_batch(randrange(n_subcohort_range[0], n_subcohort_range[1]), global_study=gs)
        if i == 1:
            factories.StudyFactory.create_batch(2, global_study=gs)
        elif i == 2:
            factories.StudyFactory.create_batch(3, global_study=gs)
        else:
            factories.StudyFactory.create(global_study=gs)
    studies = models.Study.objects.all()
    for st in studies:
        factories.SourceStudyVersionFactory.create(study=st)
    source_study_versions = models.SourceStudyVersion.objects.all()
    for ssv in source_study_versions:
        factories.SourceDatasetFactory.create_batch(
            randrange(n_dataset_range[0], n_dataset_range[1]), source_study_version=ssv)
    source_datasets = models.SourceDataset.objects.all()
    for sd in source_datasets:
        # Make source traits.
        factories.SourceTraitFactory.create_batch(randrange(n_trait_range[0], n_trait_range[1]), source_dataset=sd)
        # # Choose random set of subcohorts to add to the dataset.
        # possible_subcohorts = list(
        #     models.Subcohort.objects.filter(global_study=sd.source_study_version.study.global_study).all())
        # if len(possible_subcohorts) > 0:
        #     if len(possible_subcohorts) > 1:
        #         add_subcohorts = sample(possible_subcohorts, randrange(1, len(possible_subcohorts) + 1))
        #     else:
        #         add_subcohorts = possible_subcohorts
        #     for sc in add_subcohorts:
        #         sd.subcohorts.add(sc)
    source_traits = models.SourceTrait.objects.all()
    for st in models.SourceTrait.objects.filter(i_detected_type='encoded'):
        factories.SourceTraitEncodedValueFactory.create_batch(
            randrange(n_enc_value_range[0], n_enc_value_range[1]), source_trait=st)

    # Add another source_study_version to one study. Use the same datasets, traits,
    # encoded values, etc. Maybe change or add a few traits and one dataset.
    # Duplicate a source study version.
    ssv_study = studies[len(studies) - 1]
    ssv_to_dup = ssv_study.sourcestudyversion_set.all()[0]
    existing_ssv_ids = [ssv.i_id for ssv in models.SourceStudyVersion.objects.all()]
    available_ssv_ids = list(set(range(1, 500)) - set(existing_ssv_ids))
    dup_ssv = copy(ssv_to_dup)
    dup_ssv.i_id = available_ssv_ids[0]
    dup_ssv.i_version = dup_ssv.i_version + 1
    dup_ssv.created = None
    dup_ssv.modified = None
    dup_ssv.save()
    # Duplicate datasets.
    datasets_to_dup = ssv_to_dup.sourcedataset_set.all()
    existing_dataset_ids = [sd.i_id for sd in models.SourceDataset.objects.all()]
    available_dataset_ids = iter(list(set(range(1, 10000)) - set(existing_dataset_ids)))
    duped_datasets = []
    for ds in datasets_to_dup:
        new_ds = copy(ds)
        new_ds.i_id = next(available_dataset_ids)
        new_ds.source_study_version = dup_ssv
        new_ds.created = None
        new_ds.modified = None
        new_ds.save()
        duped_datasets.append(new_ds)
    # Duplicate source traits.
    existing_trait_ids = [tr.i_trait_id for tr in models.SourceTrait.objects.all()]
    available_trait_ids = iter(list(set(range(1, 100000)) - set(existing_trait_ids)))
    existing_source_trait_encoded_value_ids = [ev.i_id for ev in models.SourceTraitEncodedValue.objects.all()]
    available_source_trait_encoded_value_ids = iter(
        list(set(range(1, 1000000)) - set(existing_source_trait_encoded_value_ids)))
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
    new_dataset = factories.SourceDatasetFactory.create(source_study_version=dup_ssv)
    new_traits = factories.SourceTraitFactory.create_batch(10, source_dataset=new_dataset)
    for tr in new_traits:
        if tr.i_detected_type == 'encoded':
            for n in range(randrange(n_enc_value_range[0], n_enc_value_range[1])):
                factories.SourceTraitEncodedValueFactory.create(
                    i_id=next(available_source_trait_encoded_value_ids), source_trait=tr)
    # Add some allowed update reasons.
    new_reasons = factories.AllowedUpdateReasonFactory.create_batch(5)
    #
    # Add simulated harmonized traits, each with a single harm. unit per global study.
    for nh in range(randrange(n_trait_range[0], n_trait_range[1])):
        ht_set = factories.HarmonizedTraitSetFactory.create()
        ht_set_v1 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=1)
        htrait = factories.HarmonizedTraitFactory.create(harmonized_trait_set_version=ht_set_v1)
        # Make a dict of (global_study, harmonization_unit) pairs.
        h_units = {gs: factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v1)
                   for gs in models.GlobalStudy.objects.all()}
        for gs in h_units:
            hunit = h_units[gs]
            # Randomly select two source traits to be components.
            source_traits = sample(list(models.SourceTrait.objects.filter(
                source_dataset__source_study_version__study__global_study=gs)), 2)
            # Add component source trait to harmonized trait and harmonization unit.
            htrait.component_source_traits.add(source_traits[0])
            hunit.component_source_traits.add(source_traits[0])
            # Add component age trait to harmonization unit.
            hunit.component_age_traits.add(source_traits[1])
            # Add harmonization unit to harmonized trait.
            htrait.harmonization_units.add(hunit)
    # Add one harmonized trait that has component harmonized traits.
    ht_set = factories.HarmonizedTraitSetFactory.create()
    ht_set_v1 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=1)
    htrait = factories.HarmonizedTraitFactory.create(harmonized_trait_set_version=ht_set_v1)
    hunit = factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v1)
    component = sample(list(models.HarmonizedTraitSetVersion.objects.all()), 1)[0]
    hunit.component_harmonized_trait_set_versions.add(component)
    htrait.component_harmonized_trait_set_versions.add(component)
    htrait.harmonization_units.add(hunit)
    # Add a second harmonized trait set version for the harmonized trait immediately above.
    ht_set_v2 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=2)
    reason = new_reasons[0]
    ht_set_v2.update_reasons.add(reason)
    htrait_v2 = factories.HarmonizedTraitFactory.create(harmonized_trait_set_version=ht_set_v2)
    hunit_v2 = factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v2)
    hunit_v2.component_harmonized_trait_set_versions.add(component)
    htrait_v2.component_harmonized_trait_set_versions.add(component)
    htrait_v2.harmonization_units.add(hunit_v2)
    # Add one harmonized trait that has component batch traits.
    ht_set = factories.HarmonizedTraitSetFactory.create()
    ht_set_v1 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=1)
    htrait = factories.HarmonizedTraitFactory.create(harmonized_trait_set_version=ht_set_v1)
    h_units = {gs: factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v1)
               for gs in models.GlobalStudy.objects.all()}
    for gs in h_units:
        hunit = h_units[gs]
        # Randomly select two source traits to be components.
        source_traits = sample(
            list(models.SourceTrait.objects.filter(source_dataset__source_study_version__study__global_study=gs)), 3)
        # Add component source trait to harmonized trait and harmonization unit.
        htrait.component_source_traits.add(source_traits[0])
        hunit.component_source_traits.add(source_traits[0])
        # Add component age trait to harmonization unit.
        hunit.component_age_traits.add(source_traits[1])
        # Add harmonization unit to harmonized trait.
        htrait.harmonization_units.add(hunit)
        # Add component batch traits
        htrait.component_batch_traits.add(source_traits[2])
        hunit.component_batch_traits.add(source_traits[2])
    # Add one harmonized trait that only uses source traits from *some* (only 2) of the studies.
    ht_set = factories.HarmonizedTraitSetFactory.create()
    ht_set_v1 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=1)
    htrait = factories.HarmonizedTraitFactory.create(harmonized_trait_set_version=ht_set_v1)
    h_units = {gs: factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v1)
               for gs in sample(list(models.GlobalStudy.objects.all()), 2)}
    for gs in h_units:
        hunit = h_units[gs]
        # Randomly select two source traits to be components.
        source_traits = sample(
            list(models.SourceTrait.objects.filter(source_dataset__source_study_version__study__global_study=gs)), 3)
        # Add component source trait to harmonized trait and harmonization unit.
        htrait.component_source_traits.add(source_traits[0])
        hunit.component_source_traits.add(source_traits[0])
        # Add component age trait to harmonization unit.
        hunit.component_age_traits.add(source_traits[1])
        # Add harmonization unit to harmonized trait.
        htrait.harmonization_units.add(hunit)
        # Add component batch traits
        htrait.component_batch_traits.add(source_traits[2])
        hunit.component_batch_traits.add(source_traits[2])
    # Add a pair of harmonized traits in the same trait set.
    ht_set = factories.HarmonizedTraitSetFactory.create()
    ht_set_v1 = factories.HarmonizedTraitSetVersionFactory.create(harmonized_trait_set=ht_set, i_version=1)
    htraits = factories.HarmonizedTraitFactory.create_batch(2, harmonized_trait_set_version=ht_set_v1)
    h_units = {gs: factories.HarmonizationUnitFactory.create(harmonized_trait_set_version=ht_set_v1)
               for gs in models.GlobalStudy.objects.all()}
    for gs in h_units:
        hunit = h_units[gs]
        for ht in htraits:
            # Randomly select two source traits to be components.
            source_traits = sample(list(models.SourceTrait.objects.filter(
                source_dataset__source_study_version__study__global_study=gs)), 3)
            # Add component source trait to harmonized trait and harmonization unit.
            ht.component_source_traits.add(source_traits[0])
            hunit.component_source_traits.add(source_traits[0])
            # Add component age trait to harmonization unit.
            hunit.component_age_traits.add(source_traits[1])
            # Add harmonization unit to harmonized trait.
            ht.harmonization_units.add(hunit)
            # Add component batch traits
            ht.component_batch_traits.add(source_traits[2])
            hunit.component_batch_traits.add(source_traits[2])
    # If there's not a harmonized trait with encoded values already, make one.
    encoded_harmonized_traits = models.HarmonizedTrait.objects.filter(i_data_type='encoded')
    if len(encoded_harmonized_traits) < 1:
        htrait_to_encode = sample(list(models.HarmonizedTrait.objects.all()), 1)[0]
        htrait_to_encode.i_data_type = 'encoded'
        htrait_to_encode.save()
    # Add encoded values to all of the encoded value traits.
    for htr in models.HarmonizedTrait.objects.filter(i_data_type='encoded'):
        for n in range(randrange(n_enc_value_range[0], n_enc_value_range[1])):
            factories.HarmonizedTraitEncodedValueFactory.create_batch(
                randrange(n_enc_value_range[0], n_enc_value_range[1]), harmonized_trait=htr)
