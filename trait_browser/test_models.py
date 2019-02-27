"""Test functions and classes from models.py."""

from datetime import datetime, timedelta

from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from faker import Factory

from tags.factories import TaggedTraitFactory
from tags.models import Tag

from . import factories
from . import models

fake = Factory.create()


class GlobalStudyTest(TestCase):

    def test_model_saving(self):
        """You can save a GlobalStudy object."""
        global_study = factories.GlobalStudyFactory.create()
        self.assertIsInstance(models.GlobalStudy.objects.get(pk=global_study.pk), models.GlobalStudy)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        global_study = factories.GlobalStudyFactory.build()
        self.assertIsInstance(global_study.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        global_study = factories.GlobalStudyFactory.create()
        self.assertIsInstance(global_study.created, datetime)
        self.assertIsInstance(global_study.modified, datetime)


class StudyTest(TestCase):

    def test_model_saving(self):
        """You can save a Study object."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(models.Study.objects.get(pk=study.pk), models.Study)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        study = factories.StudyFactory.build()
        self.assertIsInstance(study.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(study.created, datetime)
        self.assertIsInstance(study.modified, datetime)

    def test_custom_save(self):
        """The custom save method works."""
        study = factories.StudyFactory.create()
        self.assertRegex(study.phs, 'phs\d{6}')

    def test_get_search_url(self):
        """Tests that the get_search_url method returns an appropriately constructed url."""
        study = factories.StudyFactory.create()
        url = study.get_search_url()

    def test_get_dataset_search_url(self):
        """Tests that the get_search_url method returns an appropriately constructed url."""
        study = factories.StudyFactory.create()
        url = study.get_dataset_search_url()

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.StudyFactory.create()
        url = instance.get_absolute_url()

    def test_get_name_link_html(self):
        """get_name_link_html() returns a string."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(study.get_name_link_html(), str)

    def test_get_latest_version(self):
        """get_latest_version returns the latest version of this study."""
        study = factories.StudyFactory.create()
        ssv1 = factories.SourceStudyVersionFactory.create(study=study, i_version=1)
        self.assertEqual(study.get_latest_version(), ssv1)
        ssv2 = factories.SourceStudyVersionFactory.create(study=study, i_version=2)
        self.assertEqual(study.get_latest_version(), ssv2)

    def test_get_latest_version_link(self):
        """get_latest_version_link returns a link to the latest version of this study."""
        study = factories.StudyFactory.create()
        ssv1 = factories.SourceStudyVersionFactory.create(study=study, i_version=1)
        self.assertEqual(study.get_latest_version_link(), ssv1.dbgap_link)
        ssv2 = factories.SourceStudyVersionFactory.create(study=study, i_version=2)
        self.assertEqual(study.get_latest_version_link(), ssv2.dbgap_link)

    def test_get_latest_version_with_one_non_deprecated_version(self):
        """get_latest_version returns the proper version if there is only one non-deprecated version."""
        study = factories.StudyFactory.create()
        version = factories.SourceStudyVersionFactory.create(
            study=study
        )
        self.assertEqual(study.get_latest_version(), version)

    def test_get_latest_version_with_deprecated_old_versions(self):
        """get_latest_version returns the proper version if one non-deprecated and deprecated versions exist."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        self.assertEqual(study.get_latest_version(), current_study_version)

    def test_get_latest_version_no_versions(self):
        """get_latest_version returns None if there is no study version."""
        study = factories.StudyFactory.create()
        self.assertIsNone(study.get_latest_version())

    def test_get_latest_version_no_current_version(self):
        """get_latest_version returns None if there is no non-deprecated version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        self.assertIsNone(study.get_latest_version())

    def test_get_latest_version_breaks_ties_with_i_version(self):
        """get_latest_version chooses highest version for two non-deprecated versions."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_date_added=timezone.now()
        )
        study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=study_version_1.i_version + 1,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        self.assertEqual(study.get_latest_version(), study_version_2)

    def test_get_latest_version_breaks_ties_with_i_date_added(self):
        """get_latest_version chooses most recent i_date_added field if version is the same."""
        study = factories.StudyFactory.create()
        study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=1,
            i_date_added=timezone.now()
        )
        study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=1,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        self.assertEqual(study.get_latest_version(), study_version_1)


class SourceStudyVersionTest(TestCase):

    def test_model_saving(self):
        """You can save a SourceStudyVersion object."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsInstance(
            models.SourceStudyVersion.objects.get(pk=source_study_version.pk), models.SourceStudyVersion)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        source_study_version = factories.SourceStudyVersionFactory.build()
        self.assertIsInstance(source_study_version.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsInstance(source_study_version.created, datetime)
        self.assertIsInstance(source_study_version.modified, datetime)

    def test_custom_save(self):
        """The custom save method works."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertRegex(source_study_version.full_accession, 'phs\d{6}\.v\d{1,3}\.p\d{1,3}')
        self.assertEqual(source_study_version.dbgap_link[:68], models.SourceStudyVersion.STUDY_VERSION_URL[:68])

    def test_get_previous_version_no_other_versions(self):
        """Returns None when no other versions exist."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsNone(source_study_version.get_previous_version())

    def test_get_previous_version_no_previous_version(self):
        """Returns None when another version exists, but it is not a previous version."""
        study = factories.StudyFactory.create()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(study=study, i_version=1)
        source_study_version_2 = factories.SourceStudyVersionFactory.create(study=study, i_version=2)
        self.assertIsNone(source_study_version_1.get_previous_version())

    def test_get_previous_version_same_version_number(self):
        """Returns the correct previous version with the same version number."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        source_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now)
        self.assertEqual(source_study_version_2.get_previous_version(), source_study_version_1)
        self.assertIsNone(source_study_version_1.get_previous_version())

    def test_get_previous_version_ignores_other_studies(self):
        """"Does not return versions from other studies."""
        now = timezone.now()
        other_source_study_version = factories.SourceStudyVersionFactory.create(
            i_version=1, i_date_added=now - timedelta(hours=1))
        source_study_version = factories.SourceStudyVersionFactory.create(i_version=1, i_date_added=now)
        self.assertIsNone(source_study_version.get_previous_version())

    def test_get_previous_version_one_previous(self):
        """Returns the correct version when one other version exists."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        source_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now)
        self.assertEqual(source_study_version_2.get_previous_version(), source_study_version_1)

    def test_get_previous_version_two_previous(self):
        """Returns the correct version when two previous other versions exist."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=2))
        source_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now - timedelta(hours=1))
        source_study_version_3 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=3, i_date_added=now)
        self.assertEqual(source_study_version_3.get_previous_version(), source_study_version_2)

    def test_get_previous_verion_breaks_ties_with_date_added(self):
        """Returns a version with a higher date_added if two previous versions have the same version."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=2))
        source_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        source_study_version_3 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now)
        self.assertEqual(source_study_version_3.get_previous_version(), source_study_version_2)

    def test_get_previous_version_filters_by_version_before_date_added(self):
        """Returns a version with a higher version number before a higher date_added."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        source_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        source_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now - timedelta(hours=2))
        source_study_version_3 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=3, i_date_added=now)
        self.assertEqual(source_study_version_3.get_previous_version(), source_study_version_2)


class SourceStudyVersionGetNewSourceDatasetsTest(TestCase):

    def setUp(self):
        super().setUp()
        self.study = factories.StudyFactory.create()
        now = timezone.now()
        self.study_version_1 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=1, i_date_added=now - timedelta(hours=2), i_is_deprecated=True)
        self.study_version_2 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=2, i_date_added=now - timedelta(hours=1), i_is_deprecated=True)
        self.study_version_3 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=3, i_date_added=now)
        # Convert these lists to prevent queryset evaluation later on, after other traits have been created.
        # Create traits for the first version.
        self.datasets_v1 = list(factories.SourceDatasetFactory.create_batch(
            5, source_study_version=self.study_version_1))
        # Create traits with the same accessions for the second and third versions.
        for x in self.datasets_v1:
            factories.SourceDatasetFactory.create(source_study_version=self.study_version_2, i_accession=x.i_accession)
            factories.SourceDatasetFactory.create(source_study_version=self.study_version_3, i_accession=x.i_accession)
        self.datasets_v2 = list(models.SourceDataset.objects.filter(source_study_version=self.study_version_2))
        self.datasets_v3 = list(models.SourceDataset.objects.filter(source_study_version=self.study_version_3))

    def test_no_deprecated_datasets(self):
        """Does not include deprecated datasets."""
        result = self.study_version_3.get_new_sourcedatasets()
        for dataset in self.datasets_v1:
            self.assertNotIn(dataset, result)
        for dataset in self.datasets_v2:
            self.assertNotIn(dataset, result)

    def test_no_updated_datasets(self):
        """Does not include new datasets that also exist in previous version."""
        result = self.study_version_3.get_new_sourcedatasets()
        for dataset in self.datasets_v3:
            self.assertNotIn(dataset, result)

    def test_no_removed_datasets(self):
        """Includes datasets that only exist in previous version."""
        removed_dataset_1 = factories.SourceDatasetFactory.create(source_study_version=self.study_version_1)
        removed_dataset_2 = factories.SourceDatasetFactory.create(
            source_study_version=self.study_version_2, i_accession=removed_dataset_1.i_accession)
        result = self.study_version_3.get_new_sourcedatasets()
        self.assertNotIn(removed_dataset_1, result)
        self.assertNotIn(removed_dataset_2, result)
        self.assertEqual(len(result), 0)

    def test_includes_one_new_dataset(self):
        """Includes one new dataset in this version."""
        new_dataset = factories.SourceDatasetFactory.create(source_study_version=self.study_version_3)
        result = self.study_version_3.get_new_sourcedatasets()
        self.assertIn(new_dataset, result)

    def test_includes_two_new_datasets(self):
        """Includes two new traits in this version."""
        new_datasets = factories.SourceDatasetFactory.create_batch(2, source_study_version=self.study_version_3)
        result = self.study_version_3.get_new_sourcedatasets()
        for new_dataset in new_datasets:
            self.assertIn(new_dataset, result)

    def test_no_previous_study_version(self):
        """Works if there is no previous version of the study."""
        self.study_version_1.delete()
        self.study_version_2.delete()
        result = self.study_version_3.get_new_sourcedatasets()
        self.assertEqual(result.count(), 0)

    def test_does_not_compare_with_two_versions_ago(self):
        """Does not include datasets that were new in an older previous version but not the most recent version of the study."""  # noqa
        new_dataset_v2 = factories.SourceDatasetFactory.create(source_study_version=self.study_version_2)
        new_dataset_v3 = factories.SourceDatasetFactory.create(
            source_study_version=self.study_version_3,
            i_accession=new_dataset_v2.i_accession)
        result = self.study_version_3.get_new_sourcedatasets()
        self.assertNotIn(new_dataset_v3, result)

    def test_intermediate_version_no_new_current_datasets(self):
        """Does not show a new dataset in a more recent study version."""
        new_dataset_v3 = factories.SourceDatasetFactory.create(source_study_version=self.study_version_3)
        result = self.study_version_2.get_new_sourcedatasets()
        self.assertNotIn(new_dataset_v3, result)

    def test_intermediate_version_one_newer_dataset(self):
        """Shows a new dataset in an intermediate version."""
        new_dataset_v2 = factories.SourceDatasetFactory.create(source_study_version=self.study_version_2)
        new_dataset_v3 = factories.SourceDatasetFactory.create(
            source_study_version=self.study_version_3,
            i_accession=new_dataset_v2.i_accession)
        result = self.study_version_2.get_new_sourcedatasets()
        self.assertIn(new_dataset_v2, result)
        self.assertNotIn(new_dataset_v3, result)


class SourceStudyVersionGetNewSourcetraitsTest(TestCase):

    def setUp(self):
        super().setUp()
        self.study = factories.StudyFactory.create()
        now = timezone.now()
        self.study_version_1 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=1, i_date_added=now - timedelta(hours=2), i_is_deprecated=True)
        self.study_version_2 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=2, i_date_added=now - timedelta(hours=1), i_is_deprecated=True)
        self.study_version_3 = factories.SourceStudyVersionFactory.create(
            study=self.study, i_version=3, i_date_added=now)
        # Convert these lists to prevent queryset evaluation later on, after other traits have been created.
        # Create traits for the first version.
        self.source_traits_v1 = list(factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version=self.study_version_1))
        # Create traits with the same accessions for the second and third versions.
        for x in self.source_traits_v1:
            factories.SourceTraitFactory.create(
                source_dataset__source_study_version=self.study_version_2,
                i_dbgap_variable_accession=x.i_dbgap_variable_accession)
            factories.SourceTraitFactory.create(
                source_dataset__source_study_version=self.study_version_3,
                i_dbgap_variable_accession=x.i_dbgap_variable_accession)
        self.source_traits_v2 = list(models.SourceTrait.objects.filter(
            source_dataset__source_study_version=self.study_version_2))
        self.source_traits_v3 = list(models.SourceTrait.objects.filter(
            source_dataset__source_study_version=self.study_version_3))

    def test_no_deprecated_traits_in_table(self):
        """No deprecated traits are shown in the table."""
        result = self.study_version_3.get_new_sourcetraits()
        for trait in self.source_traits_v1:
            self.assertNotIn(trait, result)
        for trait in self.source_traits_v2:
            self.assertNotIn(trait, result)

    def test_no_updated_traits(self):
        """Table does not include new traits that also exist in previous version."""
        result = self.study_version_3.get_new_sourcetraits()
        for trait in self.source_traits_v3:
            self.assertNotIn(trait, result)

    def test_no_removed_traits(self):
        """Table does not include traits that only exist in previous version."""
        removed_trait_1 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_1)
        removed_trait_2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_2,
            i_dbgap_variable_accession=removed_trait_1.i_dbgap_variable_accession)
        result = self.study_version_3.get_new_sourcetraits()
        self.assertNotIn(removed_trait_1, result)
        self.assertNotIn(removed_trait_2, result)
        self.assertEqual(len(result), 0)

    def test_includes_one_new_trait(self):
        """Table includes one new trait in this version."""
        new_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_3)
        result = self.study_version_3.get_new_sourcetraits()
        self.assertIn(new_trait, result)

    def test_includes_two_new_traits(self):
        """Table includes two new traits in this version."""
        new_traits = factories.SourceTraitFactory.create_batch(
            2, source_dataset__source_study_version=self.study_version_3)
        result = self.study_version_3.get_new_sourcetraits()
        for new_trait in new_traits:
            self.assertIn(new_trait, result)

    def test_no_previous_study_version(self):
        """Works if there is no previous version of the study."""
        self.study_version_1.delete()
        self.study_version_2.delete()
        result = self.study_version_3.get_new_sourcetraits()
        self.assertEqual(result.count(), 0)

    def test_does_not_compare_with_two_versions_ago(self):
        """Does not include traits that were new in an older previous version but not the most recent version of the study."""  # noqa
        new_trait_v2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_2)
        new_trait_v3 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_3,
            i_dbgap_variable_accession=new_trait_v2.i_dbgap_variable_accession)
        result = self.study_version_3.get_new_sourcetraits()
        self.assertNotIn(new_trait_v3, result)

    def test_intermediate_version_no_new_current_traits(self):
        """Does not show a new trait in a more recent study version."""
        new_trait_v3 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_3)
        result = self.study_version_2.get_new_sourcetraits()
        self.assertNotIn(new_trait_v3, result)

    def test_intermediate_version_one_newer_traits(self):
        """Shows a new trait in an intermediate version."""
        new_trait_v2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_2)
        new_trait_v3 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=self.study_version_3,
            i_dbgap_variable_accession=new_trait_v2.i_dbgap_variable_accession)
        result = self.study_version_2.get_new_sourcetraits()
        self.assertIn(new_trait_v2, result)
        self.assertNotIn(new_trait_v3, result)


class SourceDatasetTest(TestCase):

    def test_model_saving(self):
        """You can save a SourceDataset object."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(models.SourceDataset.objects.get(pk=source_dataset.pk), models.SourceDataset)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        source_dataset = factories.SourceDatasetFactory.build()
        self.assertIsInstance(source_dataset.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(source_dataset.created, datetime)
        self.assertIsInstance(source_dataset.modified, datetime)

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.SourceDatasetFactory.create()
        url = instance.get_absolute_url()

    # def test_adding_subcohorts(self):
    #     """Adding associated subcohorts works."""
    #     global_study = factories.GlobalStudyFactory.create()
    #     subcohorts = factories.SubcohortFactory.create_batch(5, global_study=global_study)
    #     source_dataset = factories.SourceDatasetFactory.create(
    #         source_study_version__study__global_study=global_study, subcohorts=subcohorts)
    #     self.assertEqual(len(source_dataset.subcohorts.all()), 5)

    def test_custom_save(self):
        """The custom save method works."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertRegex(source_dataset.full_accession, 'pht\d{6}\.v\d{1,5}.p\d{1,5}')
        self.assertEqual(source_dataset.dbgap_link[:70], models.SourceDataset.DATASET_URL[:70])

    def test_current_queryset_method(self):
        """SourceDataset.objects.current() does not return deprecated traits."""
        current_dataset = factories.SourceDatasetFactory.create()
        deprecated_dataset = factories.SourceDatasetFactory.create()
        deprecated_dataset.source_study_version.i_is_deprecated = True
        deprecated_dataset.source_study_version.save()
        self.assertIn(current_dataset, models.SourceDataset.objects.current())
        self.assertNotIn(deprecated_dataset, models.SourceDataset.objects.current())

    def test_get_name_link_html(self):
        """get_name_link_html returns a string."""
        dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(dataset.get_name_link_html(), str)

    def test_get_name_link_html_mdash_for_blank_description(self):
        """get_name_link_html includes an mdash when description is blank."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='')
        self.assertIsInstance(dataset.get_name_link_html(), str)
        self.assertIn('&mdash;', dataset.get_name_link_html())

    def test_get_name_link_html_non_blank_description(self):
        """get_name_link_html includes an mdash when description is not blank."""
        desc = 'my dataset description'
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description=desc)
        self.assertIsInstance(dataset.get_name_link_html(), str)
        self.assertIn(desc, dataset.get_name_link_html())

    def test_get_name_link_html_truncates_long_description(self):
        """get_name_link_html truncates a long description."""
        desc = 'my dataset description with many words'
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description=desc)
        self.assertIsInstance(dataset.get_name_link_html(), str)
        self.assertIn('my dataset', dataset.get_name_link_html(max_popover_words=2))
        self.assertNotIn('description with many words', dataset.get_name_link_html(max_popover_words=2))
        self.assertIn('my dataset description...', dataset.get_name_link_html(max_popover_words=3))
        self.assertNotIn('with many words', dataset.get_name_link_html(max_popover_words=3))
        self.assertIn(desc, dataset.get_name_link_html())

    def test_get_latest_version_is_most_recent(self):
        """get_latest_version returns itself if the dataset is the most recent."""
        dataset = factories.SourceDatasetFactory.create()
        self.assertEqual(dataset.get_latest_version(), dataset)

    def test_get_latest_version_is_most_recent_with_old_version(self):
        """get_latest_version returns itself if the dataset is the most recent and an old version exists."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_dataset = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        self.assertEqual(current_dataset.get_latest_version(), current_dataset)

    def test_get_latest_version_is_most_recent_with_same_version(self):
        """get_latest_version returns itself if the dataset is the most recent and an old version exists."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_dataset = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version
        )
        self.assertEqual(current_dataset.get_latest_version(), current_dataset)

    def test_get_latest_version_same_version(self):
        """get_latest_version returns the newer dataset even if it has the same version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_dataset = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version
        )
        other_datasets = factories.SourceDatasetFactory.create_batch(10, source_study_version=current_study_version)
        self.assertEqual(deprecated_dataset.get_latest_version(), current_dataset)

    def test_get_latest_version_old_version(self):
        """get_latest_version returns the current dataset if it has a higher version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_dataset = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        other_datasets = factories.SourceDatasetFactory.create_batch(10, source_study_version=current_study_version)
        self.assertEqual(deprecated_dataset.get_latest_version(), current_dataset)

    def test_get_latest_version_new_study_version_with_same_version(self):
        """get_latest_version returns the current dataset if the newer study and dataset have the same version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version
        )
        current_dataset = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version
        )
        other_datasets = factories.SourceDatasetFactory.create_batch(10, source_study_version=current_study_version)
        self.assertEqual(deprecated_dataset.get_latest_version(), current_dataset)

    def test_get_latest_version_no_new_version(self):
        """get_latest_version returns None if there is no newer version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        other_datasets = factories.SourceDatasetFactory.create_batch(10, source_study_version=current_study_version)
        self.assertIsNone(deprecated_dataset.get_latest_version())

    def test_get_latest_version_no_new_study_version(self):
        """get_latest_version returns None if there is no newer version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        self.assertIsNone(deprecated_dataset.get_latest_version())

    def test_get_latest_version_breaks_ties_with_i_version(self):
        """get_latest_version chooses highest version for two non-deprecated versions."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        now = timezone.now()
        current_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now()
        )
        current_dataset_1 = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version_1,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        current_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 2,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        current_dataset_2 = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version_2,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        self.assertEqual(deprecated_dataset.get_latest_version(), current_dataset_2)

    def test_get_latest_version_breaks_ties_with_i_date_added(self):
        """get_latest_version chooses most recent i_date_added field if version is the same."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_dataset = factories.SourceDatasetFactory.create(source_study_version=deprecated_study_version)
        current_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now()
        )
        current_dataset_1 = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version_1,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        current_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        current_dataset_2 = factories.SourceDatasetFactory.create(
            source_study_version=current_study_version_2,
            i_accession=deprecated_dataset.i_accession,
            i_version=deprecated_dataset.i_version + 1
        )
        self.assertEqual(deprecated_dataset.get_latest_version(), current_dataset_1)


class HarmonizedTraitSetTest(TestCase):

    def test_model_saving(self):
        """You can save a HarmonizedTraitSet object."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitSet.objects.get(pk=harmonized_trait_set.pk), models.HarmonizedTraitSet)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.build()
        self.assertIsInstance(harmonized_trait_set.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create()
        self.assertIsInstance(harmonized_trait_set.created, datetime)
        self.assertIsInstance(harmonized_trait_set.modified, datetime)


class HarmonizedTraitSetVersionTest(TestCase):

    def test_model_saving(self):
        """You can save a HarmonizedTraitSetVersion object."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitSetVersion.objects.get(pk=harmonized_trait_set_version.pk),
            models.HarmonizedTraitSetVersion)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.build()
        self.assertIsInstance(harmonized_trait_set_version.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(harmonized_trait_set_version.created, datetime)
        self.assertIsInstance(harmonized_trait_set_version.modified, datetime)

    def test_get_trait_names(self):
        """List of trait names is correct."""
        htsv = factories.HarmonizedTraitSetVersionFactory.create()
        htraits = factories.HarmonizedTraitFactory.create_batch(5, harmonized_trait_set_version=htsv)
        htsv.refresh_from_db()
        self.assertEqual(sorted(htsv.get_trait_names()), sorted([tr.trait_flavor_name for tr in htraits]))

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.HarmonizedTraitSetVersionFactory.create()
        url = instance.get_absolute_url()

    def test_get_component_html(self):
        """get_component_html returns a string."""
        htsv = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(htsv.get_component_html(), str)


class HarmonizationUnitTest(TestCase):

    def test_model_saving(self):
        """You can save a HarmonizationUnit object."""
        harmonization_unit = factories.HarmonizationUnitFactory.create()
        self.assertIsInstance(models.HarmonizationUnit.objects.get(pk=harmonization_unit.pk), models.HarmonizationUnit)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        harmonization_unit = factories.HarmonizationUnitFactory.build()
        self.assertIsInstance(harmonization_unit.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        harmonization_unit = factories.HarmonizationUnitFactory.create()
        self.assertIsInstance(harmonization_unit.created, datetime)
        self.assertIsInstance(harmonization_unit.modified, datetime)

    def test_adding_component_source_traits(self):
        """Adding associated component_source_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_source_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonization_unit.component_source_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Adding associated component_batch_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_batch_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonization_unit.component_batch_traits.all()), 5)

    def test_adding_component_age_traits(self):
        """Adding associated component_age_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_age_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_age_traits=component_age_traits)
        self.assertEqual(len(harmonization_unit.component_age_traits.all()), 5)

    def test_adding_component_harmonized_trait_set_versions(self):
        """Adding associated component_harmonized_trait_set_versions works."""
        component_harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(5)
        harmonization_unit = factories.HarmonizationUnitFactory.create(
            component_harmonized_trait_set_versions=component_harmonized_trait_set_versions)
        self.assertEqual(len(harmonization_unit.component_harmonized_trait_set_versions.all()), 5)

    def test_get_all_source_traits(self):
        """Returned queryset of source traits is correct."""
        source_traits = factories.SourceTraitFactory.create_batch(6)
        hu = factories.HarmonizationUnitFactory.create(
            component_age_traits=source_traits[0:2], component_batch_traits=source_traits[2:4],
            component_source_traits=source_traits[4:])
        self.assertEqual(
            list(hu.get_all_source_traits().order_by('pk')), list(models.SourceTrait.objects.all().order_by('pk')))

    def test_get_source_studies(self):
        """Returned list of linked studies is correct."""
        global_study = factories.GlobalStudyFactory.create()
        studies = factories.StudyFactory.create_batch(2, global_study=global_study)
        traits1 = factories.SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study=studies[0])
        traits2 = factories.SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study=studies[1])
        hu = factories.HarmonizationUnitFactory.create(
            component_age_traits=[traits1[0], traits2[0]], component_batch_traits=[traits1[1], traits2[1]],
            component_source_traits=[traits1[2], traits2[2]])
        self.assertEqual(set(list(studies)), set(list(hu.get_source_studies())))

    def test_get_component_html(self):
        """get_component_html returns a string."""
        htsv = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(htsv.get_component_html(), str)


class SourceTraitTest(TestCase):

    def test_model_saving(self):
        """You can save a SourceTrait object."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(models.SourceTrait.objects.get(pk=source_trait.pk), models.SourceTrait)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        source_trait = factories.SourceTraitFactory.build()
        self.assertIsInstance(source_trait.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(source_trait.created, datetime)
        self.assertIsInstance(source_trait.modified, datetime)

    def test_is_latest_version(self):
        pass

    def test_custom_save(self):
        """The custom save method works."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertRegex(source_trait.full_accession, 'phv\d{8}.v\d{1,3}.p\d{1,3}')
        self.assertEqual(source_trait.dbgap_link[:71], models.SourceTrait.VARIABLE_URL[:71])

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.SourceTraitFactory.create()
        url = instance.get_absolute_url()

    def test_get_name_link_html(self):
        """get_name_link_html returns a string."""
        trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(trait.get_name_link_html(), str)

    def test_get_name_link_html_blank_description(self):
        """get_name_link_html includes an mdash when description is blank."""
        trait = factories.SourceTraitFactory.create(i_description='')
        self.assertIsInstance(trait.get_name_link_html(), str)
        self.assertIn('&mdash;', trait.get_name_link_html())

    def test_get_name_link_html_truncates_long_description(self):
        """get_name_link_html truncates a long description."""
        desc = 'my trait description with many words'
        trait = factories.SourceTraitFactory.create(i_description=desc)
        self.assertIsInstance(trait.get_name_link_html(), str)
        self.assertIn('my trait', trait.get_name_link_html(max_popover_words=2))
        self.assertNotIn('description with many words', trait.get_name_link_html(max_popover_words=2))
        self.assertIn('my trait description...', trait.get_name_link_html(max_popover_words=3))
        self.assertNotIn('with many words', trait.get_name_link_html(max_popover_words=3))
        self.assertIn(desc, trait.get_name_link_html())

    def test_current_queryset_method(self):
        """SourceTrait.objects.current() does not return deprecated traits."""
        current_trait = factories.SourceTraitFactory.create()
        deprecated_trait = factories.SourceTraitFactory.create()
        deprecated_trait.source_dataset.source_study_version.i_is_deprecated = True
        deprecated_trait.source_dataset.source_study_version.save()
        self.assertIn(current_trait, models.SourceTrait.objects.current())
        self.assertNotIn(deprecated_trait, models.SourceTrait.objects.current())

    def test_archived_tags_and_non_archived_tags(self):
        """Archived tags and non archived tags linked to the trait are where they should be."""
        trait = factories.SourceTraitFactory.create()
        archived = TaggedTraitFactory.create(archived=True, trait=trait)
        non_archived = TaggedTraitFactory.create(archived=False, trait=trait)
        self.assertIn(archived.tag, trait.all_tags.all())
        self.assertIn(non_archived.tag, trait.all_tags.all())
        self.assertIn(archived.tag, trait.archived_tags)
        self.assertIn(non_archived.tag, trait.non_archived_tags)
        self.assertNotIn(archived.tag, trait.non_archived_tags)
        self.assertNotIn(non_archived.tag, trait.archived_tags)

    def test_archived_tags_and_non_archived_tags_are_querysets(self):
        """The properties archived_traits and non_archived_traits are QuerySets."""
        # These need to be querysets to behave similarly to tag.traits and trait.all_tags.
        trait = factories.SourceTraitFactory.create()
        archived = TaggedTraitFactory.create(archived=True, trait=trait)
        non_archived = TaggedTraitFactory.create(archived=False, trait=trait)
        self.assertIsInstance(trait.archived_tags, QuerySet)
        self.assertIsInstance(trait.non_archived_tags, QuerySet)

    def test_multiple_archived_tags(self):
        """Archived tags show up in the archived_tags property with multiple tagged traits of each type."""
        trait = factories.SourceTraitFactory.create()
        archived = TaggedTraitFactory.create_batch(5, archived=True, trait=trait)
        non_archived = TaggedTraitFactory.create_batch(6, archived=False, trait=trait)
        for tagged_trait in archived:
            self.assertIn(tagged_trait.tag, trait.all_tags.all())
            self.assertIn(tagged_trait.tag, trait.archived_tags)
            self.assertNotIn(tagged_trait.tag, trait.non_archived_tags)
        self.assertEqual(len(archived), trait.archived_tags.count())

    def test_multiple_non_archived_tags(self):
        """Non-archived tags show up in the non_archived_tags property with multiple of each type."""
        trait = factories.SourceTraitFactory.create()
        archived = TaggedTraitFactory.create_batch(5, archived=True, trait=trait)
        non_archived = TaggedTraitFactory.create_batch(6, archived=False, trait=trait)
        for tagged_trait in non_archived:
            self.assertIn(tagged_trait.tag, trait.all_tags.all())
            self.assertIn(tagged_trait.tag, trait.non_archived_tags)
            self.assertNotIn(tagged_trait.tag, trait.archived_tags)
        self.assertEqual(len(non_archived), trait.non_archived_tags.count())

    def test_tags(self):
        """Test the method to get all of the trait's tags."""
        trait = factories.SourceTraitFactory.create()
        tagged_traits = TaggedTraitFactory.create_batch(10, trait=trait)
        self.assertListEqual(list(trait.all_tags.all()), list(Tag.objects.all()))

    def test_get_latest_version_is_most_recent(self):
        """get_latest_version returns itself if the trait is the most recent."""
        trait = factories.SourceTraitFactory.create()
        self.assertEqual(trait.get_latest_version(), trait)

    def test_get_latest_version_is_most_recent_with_old_version(self):
        """get_latest_version returns itself if the trait is the most recent and an old version exists."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version + 1
        )
        self.assertEqual(current_trait.get_latest_version(), current_trait)

    def test_get_latest_version_is_most_recent_with_same_version(self):
        """get_latest_version returns itself if the trait is the most recent and an old version exists."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        self.assertEqual(current_trait.get_latest_version(), current_trait)

    def test_get_latest_version_same_version(self):
        """get_latest_version returns the newer trait even if it has the same version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        other_traits = factories.SourceTraitFactory.create_batch(
            10,
            source_dataset__source_study_version=current_study_version
        )
        self.assertEqual(deprecated_trait.get_latest_version(), current_trait)

    def test_get_latest_version_old_version(self):
        """get_latest_version returns the current trait if it has a higher version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        current_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version + 1
        )
        other_traits = factories.SourceTraitFactory.create_batch(
            10,
            source_dataset__source_study_version=current_study_version
        )
        self.assertEqual(deprecated_trait.get_latest_version(), current_trait)

    def test_get_latest_version_new_study_version_with_same_version(self):
        """get_latest_version returns the current trait if the newer study and dataset have the same version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version
        )
        current_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        other_traits = factories.SourceTraitFactory.create_batch(
            10,
            source_dataset__source_study_version=current_study_version
        )
        self.assertEqual(deprecated_trait.get_latest_version(), current_trait)

    def test_get_latest_version_no_new_version(self):
        """get_latest_version returns None if there is no newer version."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1
        )
        other_traits = factories.SourceTraitFactory.create_batch(
            10,
            source_dataset__source_study_version=current_study_version
        )
        self.assertIsNone(deprecated_trait.get_latest_version())

    def test_get_latest_version_no_new_study_version(self):
        """get_latest_version returns None if there is no newer version."""
        study = factories.StudyFactory.create()
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version__i_is_deprecated=True)
        self.assertIsNone(deprecated_trait.get_latest_version())

    def test_get_latest_version_breaks_ties_with_i_version(self):
        """get_latest_version chooses highest version for two non-deprecated versions."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        now = timezone.now()
        current_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now()
        )
        current_trait_1 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version_1,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        current_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 2,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        current_trait_2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version_2,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        self.assertEqual(deprecated_trait.get_latest_version(), current_trait_2)

    def test_get_latest_version_breaks_ties_with_i_date_added(self):
        """get_latest_version chooses most recent i_date_added field if version is the same."""
        study = factories.StudyFactory.create()
        deprecated_study_version = factories.SourceStudyVersionFactory.create(study=study, i_is_deprecated=True)
        deprecated_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        current_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now()
        )
        current_trait_1 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version_1,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        current_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study,
            i_version=deprecated_study_version.i_version + 1,
            i_date_added=timezone.now() - timedelta(hours=1)
        )
        current_trait_2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=current_study_version_2,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession,
            i_dbgap_variable_version=deprecated_trait.i_dbgap_variable_version
        )
        self.assertEqual(deprecated_trait.get_latest_version(), current_trait_1)

    def test_get_previous_version_no_other_study_version(self):
        """Returns None if there is no other study version."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsNone(source_trait.get_previous_version())

    def test_get_previous_version_no_previous_study_version(self):
        """Returns None if there is no previous study version."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        newer_study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now)
        source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=100)
        newer_source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=newer_study_version, i_dbgap_variable_accession=100)
        self.assertIsNone(source_trait.get_previous_version())

    def test_get_previous_version_previous_version_has_trait(self):
        study = factories.StudyFactory.create()
        now = timezone.now()
        previous_study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now)
        previous_source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=previous_study_version, i_dbgap_variable_accession=100)
        source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=100)
        self.assertEqual(source_trait.get_previous_version(), previous_source_trait)

    def test_get_previous_version_previous_version_no_trait(self):
        """Returns None if the source trait doesn't exist in the previous version."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        previous_study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=1))
        study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now)
        source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=100)
        self.assertIsNone(source_trait.get_previous_version())

    def test_get_previous_version_two_previous_versions_have_trait(self):
        """Returns the correct source trait if it exists in multiple previous versions."""
        study = factories.StudyFactory.create()
        now = timezone.now()
        previous_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=2))
        previous_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now - timedelta(hours=1))
        study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=3, i_date_added=now)
        previous_source_trait_1 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=previous_study_version_1, i_dbgap_variable_accession=100)
        previous_source_trait_2 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=previous_study_version_2, i_dbgap_variable_accession=100)
        source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=100)
        self.assertEqual(source_trait.get_previous_version(), previous_source_trait_2)

    def test_get_previous_version_two_previous_versions_no_trait(self):
        """Returns None if the source trait doesn't exist in the previous study version, even if it exists in an earlier version.""" # noqa
        study = factories.StudyFactory.create()
        now = timezone.now()
        previous_study_version_1 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=1, i_date_added=now - timedelta(hours=2))
        previous_study_version_2 = factories.SourceStudyVersionFactory.create(
            study=study, i_version=2, i_date_added=now - timedelta(hours=1))
        study_version = factories.SourceStudyVersionFactory.create(
            study=study, i_version=3, i_date_added=now)
        previous_source_trait_1 = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=previous_study_version_1, i_dbgap_variable_accession=100)
        source_trait = factories.SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=100)
        self.assertIsNone(source_trait.get_previous_version())


class HarmonizedTraitTest(TestCase):

    def test_model_saving(self):
        """You can save a HarmonizedTrait object."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(models.HarmonizedTrait.objects.get(pk=harmonized_trait.pk), models.HarmonizedTrait)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        harmonized_trait = factories.HarmonizedTraitFactory.build()
        self.assertIsInstance(harmonized_trait.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(harmonized_trait.created, datetime)
        self.assertIsInstance(harmonized_trait.modified, datetime)

    def test_custom_save(self):
        """The custom save method works."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertEqual(
            harmonized_trait.trait_flavor_name,
            '{}_{}'.format(harmonized_trait.i_trait_name,
                           harmonized_trait.harmonized_trait_set_version.harmonized_trait_set.i_flavor))

    def test_adding_component_source_traits(self):
        """Adding associated component_source_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_source_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonized_trait.component_source_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Adding associated component_batch_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_batch_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonized_trait.component_batch_traits.all()), 5)

    def test_adding_component_harmonized_trait_set_versions(self):
        """Adding associated component_harmonized_trait_set_versions works."""
        component_harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(5)
        harmonized_trait = factories.HarmonizedTraitFactory.create(
            component_harmonized_trait_set_versions=component_harmonized_trait_set_versions)
        self.assertEqual(len(harmonized_trait.component_harmonized_trait_set_versions.all()), 5)

    def test_adding_harmonization_units(self):
        """Adding associated harmonization_units works."""
        htrait_set_version = factories.HarmonizedTraitSetVersionFactory.create()
        harmonization_units = factories.HarmonizationUnitFactory.create_batch(
            5, harmonized_trait_set_version=htrait_set_version)
        harmonized_trait = factories.HarmonizedTraitFactory.create(harmonization_units=harmonization_units)
        self.assertEqual(len(harmonized_trait.harmonization_units.all()), 5)

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.HarmonizedTraitFactory.create()
        url = instance.get_absolute_url()

    def test_get_component_html(self):
        """get_component_html returns a string."""
        trait = factories.HarmonizedTraitFactory.create()
        hunits = factories.HarmonizationUnitFactory.create_batch(
            5, harmonized_trait_set_version=trait.harmonized_trait_set_version)
        self.assertIsInstance(trait.get_component_html(hunits[0]), str)

    def test_get_name_link_html(self):
        """get_name_link_html returns a string."""
        trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(trait.get_name_link_html(), str)

    def test_get_name_link_html_blank_description(self):
        """get_name_link_html includes an mdash when description is blank."""
        trait = factories.HarmonizedTraitFactory.create(i_description='')
        self.assertIsInstance(trait.get_name_link_html(), str)
        self.assertIn('&mdash;', trait.get_name_link_html())

    def test_get_name_link_html_truncates_long_description(self):
        """get_name_link_html truncates a long description."""
        desc = 'my trait description with many words'
        trait = factories.HarmonizedTraitFactory.create(i_description=desc)
        self.assertIsInstance(trait.get_name_link_html(), str)
        self.assertIn('my trait...', trait.get_name_link_html(max_popover_words=2))
        self.assertIn('my trait description...', trait.get_name_link_html(max_popover_words=3))
        self.assertNotIn('with many words', trait.get_name_link_html(max_popover_words=3))
        self.assertIn(desc, trait.get_name_link_html())

    def test_unique_together(self):
        """Adding the same trait name and hts version combination doesn't work."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        duplicate = factories.HarmonizedTraitFactory.build(
            i_trait_name=harmonized_trait.i_trait_name,
            harmonized_trait_set_version=harmonized_trait.harmonized_trait_set_version)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_current_queryset_method(self):
        """HarmonizedTrait.objects.current() does not return deprecated traits."""
        current_trait = factories.HarmonizedTraitFactory.create()
        deprecated_trait = factories.HarmonizedTraitFactory.create()
        deprecated_trait.harmonized_trait_set_version.i_is_deprecated = True
        deprecated_trait.harmonized_trait_set_version.save()
        self.assertIn(current_trait, models.HarmonizedTrait.objects.current())
        self.assertNotIn(deprecated_trait, models.HarmonizedTrait.objects.current())

    def test_non_unique_keys_queryset_method(self):
        """HarmonizedTrait.objects.non_unique_keys() does not return unique key traits."""
        non_uk_trait = factories.HarmonizedTraitFactory.create(i_is_unique_key=False)
        uk_trait = factories.HarmonizedTraitFactory.create(i_is_unique_key=True)
        self.assertIn(non_uk_trait, models.HarmonizedTrait.objects.non_unique_keys())
        self.assertNotIn(uk_trait, models.HarmonizedTrait.objects.non_unique_keys())


class SourceTraitEncodedValueTest(TestCase):

    def test_model_saving(self):
        """You can save a SourceTraitEncodedValue object."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(
            models.SourceTraitEncodedValue.objects.get(pk=source_trait_encoded_value.pk),
            models.SourceTraitEncodedValue)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.build()
        self.assertIsInstance(source_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(source_trait_encoded_value.created, datetime)
        self.assertIsInstance(source_trait_encoded_value.modified, datetime)


class HarmonizedTraitEncodedValueTest(TestCase):

    def test_model_saving(self):
        """You can save a HarmonizedTraitEncodedValue object."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitEncodedValue.objects.get(pk=harmonized_trait_encoded_value.pk),
            models.HarmonizedTraitEncodedValue)

    def test_printing(self):
        """Custom __str__ method returns a string."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.build()
        self.assertIsInstance(harmonized_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Timestamp fields are added to the model."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(harmonized_trait_encoded_value.created, datetime)
        self.assertIsInstance(harmonized_trait_encoded_value.modified, datetime)
