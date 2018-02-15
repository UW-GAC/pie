"""Test functions and classes from models.py."""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import TestCase

from . import factories
from . import models


class GlobalStudyTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a GlobalStudy object."""
        global_study = factories.GlobalStudyFactory.create()
        self.assertIsInstance(models.GlobalStudy.objects.get(pk=global_study.pk), models.GlobalStudy)

    def test_printing(self):
        """Test the custom __str__ method."""
        global_study = factories.GlobalStudyFactory.build()
        self.assertIsInstance(global_study.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        global_study = factories.GlobalStudyFactory.create()
        self.assertIsInstance(global_study.created, datetime)
        self.assertIsInstance(global_study.modified, datetime)


class StudyTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a Study object."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(models.Study.objects.get(pk=study.pk), models.Study)

    def test_printing(self):
        """Test the custom __str__ method."""
        study = factories.StudyFactory.build()
        self.assertIsInstance(study.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(study.created, datetime)
        self.assertIsInstance(study.modified, datetime)

    def test_custom_save(self):
        """Test that the custom save method works."""
        study = factories.StudyFactory.create()
        self.assertRegex(study.phs, 'phs\d{6}')
        self.assertEqual(study.dbgap_latest_version_link[:68], models.Study.STUDY_URL[:68])

    def test_get_search_url_creation(self):
        """Tests that the get_search_url method returns an appropriately constructed url."""
        study = factories.StudyFactory.create()
        url = ''.join([reverse('trait_browser:source:traits:search'), '\?study=\d+'])
        self.assertRegex(study.get_search_url(), url)

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.StudyFactory.create()
        url = instance.get_absolute_url()

    def test_get_name_link_html(self):
        """get_name_link_html() returns a string."""
        study = factories.StudyFactory.create()
        self.assertIsInstance(study.get_name_link_html(), str)


class SourceStudyVersionTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a SourceStudyVersion object."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsInstance(
            models.SourceStudyVersion.objects.get(pk=source_study_version.pk), models.SourceStudyVersion)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_study_version = factories.SourceStudyVersionFactory.build()
        self.assertIsInstance(source_study_version.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertIsInstance(source_study_version.created, datetime)
        self.assertIsInstance(source_study_version.modified, datetime)

    def test_custom_save(self):
        """Test that the custom save method works."""
        source_study_version = factories.SourceStudyVersionFactory.create()
        self.assertRegex(source_study_version.phs_version_string, 'phs\d{6}\.v\d{1,3}\.p\d{1,3}')


class SourceDatasetTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a SourceDataset object."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(models.SourceDataset.objects.get(pk=source_dataset.pk), models.SourceDataset)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_dataset = factories.SourceDatasetFactory.build()
        self.assertIsInstance(source_dataset.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertIsInstance(source_dataset.created, datetime)
        self.assertIsInstance(source_dataset.modified, datetime)

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.SourceDatasetFactory.create()
        url = instance.get_absolute_url()

    # def test_adding_subcohorts(self):
    #     """Test that adding associated subcohorts works."""
    #     global_study = factories.GlobalStudyFactory.create()
    #     subcohorts = factories.SubcohortFactory.create_batch(5, global_study=global_study)
    #     source_dataset = factories.SourceDatasetFactory.create(
    #         source_study_version__study__global_study=global_study, subcohorts=subcohorts)
    #     self.assertEqual(len(source_dataset.subcohorts.all()), 5)

    def test_custom_save(self):
        """Test that the custom save method works."""
        source_dataset = factories.SourceDatasetFactory.create()
        self.assertRegex(source_dataset.pht_version_string, 'pht\d{6}\.v\d{1,5}.p\d{1,5}')

    def test_current_queryset_method(self):
        """Test that SourceDataset.objects.current() does not return deprecated traits."""
        current_dataset = factories.SourceDatasetFactory.create()
        deprecated_dataset = factories.SourceDatasetFactory.create()
        deprecated_dataset.source_study_version.i_is_deprecated = True
        deprecated_dataset.source_study_version.save()
        self.assertIn(current_dataset, list(models.SourceDataset.objects.current()))
        self.assertNotIn(deprecated_dataset, list(models.SourceDataset.objects.current()))


class HarmonizedTraitSetTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a HarmonizedTraitSet object."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitSet.objects.get(pk=harmonized_trait_set.pk), models.HarmonizedTraitSet)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.build()
        self.assertIsInstance(harmonized_trait_set.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create()
        self.assertIsInstance(harmonized_trait_set.created, datetime)
        self.assertIsInstance(harmonized_trait_set.modified, datetime)


class HarmonizedTraitSetVersionTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a HarmonizedTraitSetVersion object."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitSetVersion.objects.get(pk=harmonized_trait_set_version.pk),
            models.HarmonizedTraitSetVersion)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.build()
        self.assertIsInstance(harmonized_trait_set_version.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
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


class HarmonizationUnitTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a HarmonizationUnit object."""
        harmonization_unit = factories.HarmonizationUnitFactory.create()
        self.assertIsInstance(models.HarmonizationUnit.objects.get(pk=harmonization_unit.pk), models.HarmonizationUnit)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonization_unit = factories.HarmonizationUnitFactory.build()
        self.assertIsInstance(harmonization_unit.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonization_unit = factories.HarmonizationUnitFactory.create()
        self.assertIsInstance(harmonization_unit.created, datetime)
        self.assertIsInstance(harmonization_unit.modified, datetime)

    def test_adding_component_source_traits(self):
        """Test that adding associated component_source_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_source_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonization_unit.component_source_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Test that adding associated component_batch_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_batch_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonization_unit.component_batch_traits.all()), 5)

    def test_adding_component_age_traits(self):
        """Test that adding associated component_age_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_age_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonization_unit = factories.HarmonizationUnitFactory.create(component_age_traits=component_age_traits)
        self.assertEqual(len(harmonization_unit.component_age_traits.all()), 5)

    def test_adding_component_harmonized_trait_set_versions(self):
        """Test that adding associated component_harmonized_trait_set_versions works."""
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


class SourceTraitTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a SourceTrait object."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(models.SourceTrait.objects.get(pk=source_trait.pk), models.SourceTrait)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_trait = factories.SourceTraitFactory.build()
        self.assertIsInstance(source_trait.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(source_trait.created, datetime)
        self.assertIsInstance(source_trait.modified, datetime)

    def test_is_latest_version(self):
        pass

    def test_custom_save(self):
        """Test that the custom save method works."""
        source_trait = factories.SourceTraitFactory.create()
        self.assertEqual(
            source_trait.study_accession, source_trait.source_dataset.source_study_version.phs_version_string)
        self.assertEqual(source_trait.dataset_accession, source_trait.source_dataset.pht_version_string)
        self.assertRegex(source_trait.variable_accession, 'phv\d{8}.v\d{1,3}.p\d{1,3}')
        self.assertEqual(source_trait.dbgap_study_link[:68], models.SourceTrait.STUDY_URL[:68])
        self.assertEqual(source_trait.dbgap_variable_link[:71], models.SourceTrait.VARIABLE_URL[:71])
        self.assertEqual(source_trait.dbgap_dataset_link[:70], models.SourceTrait.DATASET_URL[:70])

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = factories.SourceTraitFactory.create()
        url = instance.get_absolute_url()

    def test_get_name_link_html(self):
        """get_name_link_html returns a string."""
        trait = factories.SourceTraitFactory.create()
        self.assertIsInstance(trait.get_name_link_html(), str)

    def test_current_queryset_method(self):
        """Test that SourceTrait.objects.current() does not return deprecated traits."""
        current_trait = factories.SourceTraitFactory.create()
        deprecated_trait = factories.SourceTraitFactory.create()
        deprecated_trait.source_dataset.source_study_version.i_is_deprecated = True
        deprecated_trait.source_dataset.source_study_version.save()
        self.assertIn(current_trait, list(models.SourceTrait.objects.current()))
        self.assertNotIn(deprecated_trait, list(models.SourceTrait.objects.current()))


class HarmonizedTraitTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a HarmonizedTrait object."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(models.HarmonizedTrait.objects.get(pk=harmonized_trait.pk), models.HarmonizedTrait)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait = factories.HarmonizedTraitFactory.build()
        self.assertIsInstance(harmonized_trait.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertIsInstance(harmonized_trait.created, datetime)
        self.assertIsInstance(harmonized_trait.modified, datetime)

    def test_custom_save(self):
        """Test that the custom save method works."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        self.assertEqual(
            harmonized_trait.trait_flavor_name,
            '{}_{}'.format(harmonized_trait.i_trait_name,
                           harmonized_trait.harmonized_trait_set_version.harmonized_trait_set.i_flavor))

    def test_adding_component_source_traits(self):
        """Test that adding associated component_source_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_source_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_source_traits=component_source_traits)
        self.assertEqual(len(harmonized_trait.component_source_traits.all()), 5)

    def test_adding_component_batch_traits(self):
        """Test that adding associated component_batch_traits works."""
        global_study = factories.GlobalStudyFactory.create()
        component_batch_traits = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study__global_study=global_study)
        harmonized_trait = factories.HarmonizedTraitFactory.create(component_batch_traits=component_batch_traits)
        self.assertEqual(len(harmonized_trait.component_batch_traits.all()), 5)

    def test_adding_component_harmonized_trait_set_versions(self):
        """Test that adding associated component_harmonized_trait_set_versions works."""
        component_harmonized_trait_set_versions = factories.HarmonizedTraitSetVersionFactory.create_batch(5)
        harmonized_trait = factories.HarmonizedTraitFactory.create(
            component_harmonized_trait_set_versions=component_harmonized_trait_set_versions)
        self.assertEqual(len(harmonized_trait.component_harmonized_trait_set_versions.all()), 5)

    def test_adding_harmonization_units(self):
        """Test that adding associated harmonization_units works."""
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

    def test_unique_together(self):
        """Adding the same trait name and hts version combination doesn't work."""
        harmonized_trait = factories.HarmonizedTraitFactory.create()
        duplicate = factories.HarmonizedTraitFactory.build(
            i_trait_name=harmonized_trait.i_trait_name,
            harmonized_trait_set_version=harmonized_trait.harmonized_trait_set_version)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_current_queryset_method(self):
        """Test that HarmonizedTrait.objects.current() does not return deprecated traits."""
        current_trait = factories.HarmonizedTraitFactory.create()
        deprecated_trait = factories.HarmonizedTraitFactory.create()
        deprecated_trait.harmonized_trait_set_version.i_is_deprecated = True
        deprecated_trait.harmonized_trait_set_version.save()
        self.assertIn(current_trait, list(models.HarmonizedTrait.objects.current()))
        self.assertNotIn(deprecated_trait, list(models.HarmonizedTrait.objects.current()))


class SourceTraitEncodedValueTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a SourceTraitEncodedValue object."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(
            models.SourceTraitEncodedValue.objects.get(pk=source_trait_encoded_value.pk),
            models.SourceTraitEncodedValue)

    def test_printing(self):
        """Test the custom __str__ method."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.build()
        self.assertIsInstance(source_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        source_trait_encoded_value = factories.SourceTraitEncodedValueFactory.create()
        self.assertIsInstance(source_trait_encoded_value.created, datetime)
        self.assertIsInstance(source_trait_encoded_value.modified, datetime)


class HarmonizedTraitEncodedValueTestCase(TestCase):

    def test_model_saving(self):
        """Test that you can save a HarmonizedTraitEncodedValue object."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(
            models.HarmonizedTraitEncodedValue.objects.get(pk=harmonized_trait_encoded_value.pk),
            models.HarmonizedTraitEncodedValue)

    def test_printing(self):
        """Test the custom __str__ method."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.build()
        self.assertIsInstance(harmonized_trait_encoded_value.__str__(), str)

    def test_timestamps_added(self):
        """Test that timestamps are added."""
        harmonized_trait_encoded_value = factories.HarmonizedTraitEncodedValueFactory.create()
        self.assertIsInstance(harmonized_trait_encoded_value.created, datetime)
        self.assertIsInstance(harmonized_trait_encoded_value.modified, datetime)
