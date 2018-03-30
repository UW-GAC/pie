"""Test the functions and classes for views.py."""

from copy import copy

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from core.utils import (DCCAnalystLoginTestCase, LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase,
                        get_autocomplete_view_ids)

from tags.models import TaggedTrait
from tags.factories import TagFactory
from . import models
from . import factories
from . import forms
from . import tables
from . import searches
from .views import TABLE_PER_PAGE

from .test_searches import ClearSearchIndexMixin

# NB: The database is reset for each test method within a class!
# NB: for test methods with multiple assertions, the first failed assert statement
# will preclude any subsequent assertions


class StudyDetailTest(UserLoginTestCase):
    """Unit tests for the StudyDetail view."""

    def setUp(self):
        super(StudyDetailTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_traits = factories.SourceTraitFactory.create_batch(
            10, source_dataset__source_study_version__i_is_deprecated=False,
            source_dataset__source_study_version__study=self.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('trait_count', context)
        self.assertIn('dataset_count', context)
        self.assertIn('phs_link', context)
        self.assertIn('phs', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['trait_count'], '{:,}'.format(len(self.source_traits)))
        dataset_count = models.SourceDataset.objects.filter(source_study_version__study=self.study).count()
        self.assertEqual(context['dataset_count'], '{:,}'.format(dataset_count))
        self.assertEqual(context['phs_link'], self.source_traits[0].dbgap_study_link)
        self.assertEqual(context['phs'], self.source_traits[0].study_accession)


class StudyListTest(UserLoginTestCase):
    """Unit tests for the StudyList view."""

    def setUp(self):
        super(StudyListTest, self).setUp()
        self.studies = factories.StudyFactory.create_batch(10)

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('study_table', context)
        self.assertIsInstance(context['study_table'], tables.StudyTable)

    def test_table_has_no_rows(self):
        """When there are no studies, there are no rows in the table, but the view still works."""
        models.Study.objects.all().delete()
        response = self.client.get(self.get_url())
        context = response.context
        table = context['study_table']
        self.assertEqual(len(table.rows), 0)


class StudySourceTraitListTest(UserLoginTestCase):
    """."""

    def setUp(self):
        super(StudySourceTraitListTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_traits = factories.SourceTraitFactory.create_batch(
            10, source_dataset__source_study_version__i_is_deprecated=False,
            source_dataset__source_study_version__study=self.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:variables', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('trait_count', context)
        self.assertIn('dataset_count', context)
        self.assertIn('phs_link', context)
        self.assertIn('phs', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['trait_count'], '{:,}'.format(len(self.source_traits)))
        dataset_count = models.SourceDataset.objects.filter(source_study_version__study=self.study).count()
        self.assertEqual(context['dataset_count'], '{:,}'.format(dataset_count))
        self.assertEqual(context['phs_link'], self.source_traits[0].dbgap_study_link)
        self.assertEqual(context['phs'], self.source_traits[0].study_accession)

    def test_no_deprecated_traits_in_table(self):
        """No deprecated traits are shown in the table."""
        deprecated_traits = factories.SourceTraitFactory.create_batch(
            10, source_dataset__source_study_version__i_is_deprecated=True,
            source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        table = context['source_trait_table']
        for trait in deprecated_traits:
            self.assertNotIn(trait, table.data)
        for trait in self.source_traits:
            self.assertIn(trait, table.data)

    # Commenting out this test for now. It currently fails because the phs_link and phs are accessed via the list
    # of source traits, so when there are no traits this fails.
    # def test_table_has_no_rows(self):
    #     """When there are no source traits, there are no rows in the table, but the view still works."""
    #     models.SourceTrait.objects.all().delete()
    #     response = self.client.get(self.get_url(self.study.pk))
    #     context = response.context
    #     table = context['source_trait_table']
    #     self.assertEqual(len(table.rows), 0)


class StudySourceDatasetListTest(UserLoginTestCase):
    """."""

    def setUp(self):
        super(StudySourceDatasetListTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.datasets = factories.SourceDatasetFactory.create_batch(
            3, source_study_version__i_is_deprecated=False, source_study_version__study=self.study)
        for ds in self.datasets:
            factories.SourceTraitFactory.create_batch(5, source_dataset=ds)

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:datasets:list', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('trait_count', context)
        self.assertIn('dataset_count', context)
        self.assertIn('phs_link', context)
        self.assertIn('phs', context)
        self.assertEqual(context['study'], self.study)
        traits = models.SourceTrait.objects.filter(source_dataset__source_study_version__study=self.study)
        self.assertEqual(context['trait_count'], '{:,}'.format(traits.count()))
        dataset_count = models.SourceDataset.objects.filter(source_study_version__study=self.study).count()
        self.assertEqual(context['dataset_count'], '{:,}'.format(dataset_count))
        self.assertEqual(context['phs_link'], traits[0].dbgap_study_link)
        self.assertEqual(context['phs'], traits[0].study_accession)

    def test_no_deprecated_traits_in_table(self):
        """No deprecated datasets are shown in the table."""
        deprecated_datasets = factories.SourceDatasetFactory.create_batch(
            3, source_study_version__i_is_deprecated=True, source_study_version__study=self.study)
        for ds in deprecated_datasets:
            factories.SourceTraitFactory.create_batch(5, source_dataset=ds)
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        table = context['source_dataset_table']
        for dataset in deprecated_datasets:
            self.assertNotIn(dataset, table.data)
        for dataset in self.datasets:
            self.assertIn(dataset, table.data)

    # Commenting out this test for now. It currently fails because the phs_link and phs are accessed via the list
    # of source traits, so when there are no traits this fails.
    # def test_table_has_no_rows(self):
    #     """When there are no source traits, there are no rows in the table, but the view still works."""
    #     models.SourceDataset.objects.all().delete()
    #     response = self.client.get(self.get_url(self.study.pk))
    #     context = response.context
    #     table = context['source_dataset_table']
    #     self.assertEqual(len(table.rows), 0)


class StudySourceDatasetNameAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(StudySourceDatasetNameAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_datasets = []
        self.TEST_DATASETS = ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefg', 'cdefgh', 'bcdefa',
                              'other1', 'other2', 'other3']
        self.TEST_NAME_QUERIES = {
            'a': ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefa'],
            'abc': ['abcde', 'abcdef', 'abcd_ef', 'abcd123'],
            'abcd1': ['abcd123'],
            'b': ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefg', 'bcdefa'],
            'abcde': ['abcde', 'abcdef'],
            'abcdef': ['abcdef'],
        }
        for dataset_name in self.TEST_DATASETS:
            self.source_datasets.append(factories.SourceDatasetFactory.create(
                source_study_version=self.source_study_version, dataset_name=dataset_name))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:datasets:autocomplete:by-name', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        tmp = self.get_url(self.study.pk)
        response = self.client.get(tmp)
        self.assertEqual(response.status_code, 200)

    def test_returns_all_datasets_with_no_query(self):
        """Queryset returns all of the datasets with no query."""
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([dataset.pk for dataset in self.source_datasets]), sorted(pks))

    def test_no_deprecated_datasets_in_queryset(self):
        """Queryset returns only the latest version of a dataset."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source datasets and increment their versions. Link it to the new ssv.
        datasets2 = []
        for dataset in self.source_datasets:
            d2 = copy(dataset)
            d2.source_study_version = source_study_version2
            d2.i_id = dataset.i_id + len(self.source_datasets)
            d2.save()
            datasets2.append(d2)
        # Get results from the autocomplete view and make sure only the new versions are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(datasets2))
        for dataset in datasets2:
            self.assertIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertNotIn(dataset.i_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only datasets belonging to the appropriate study."""
        # Delete all but five source traits, so that there are 5 from each study.
        study2 = factories.StudyFactory.create()
        datasets2 = factories.SourceDatasetFactory.create_batch(
            5, source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only datasets from the correct study are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that the other study's datasets do not show up.
        self.assertEqual(len(returned_pks), len(self.source_datasets))
        for dataset in datasets2:
            self.assertNotIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertIn(dataset.i_id, returned_pks)

    def test_correct_dataset_found_by_name(self):
        """Queryset returns only the correct dataset when found by whole dataset name."""
        dataset_name = 'my_unlikely_dataset_name'
        dataset = factories.SourceDatasetFactory.create(
            dataset_name=dataset_name,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': dataset_name})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(returned_pks, [dataset.i_id])

    def test_correct_dataset_found_by_case_insensitive_name(self):
        """Queryset returns only the correct source trait when found by whole name, with mismatched case."""
        dataset_name = 'my_unlikely_dataset_name'
        dataset = factories.SourceDatasetFactory.create(
            dataset_name=dataset_name,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': dataset_name.upper()})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(returned_pks, [dataset.i_id])

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_NAME_QUERIES.keys():
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_NAME_QUERIES[query]
            self.assertEqual(len(returned_pks), len(expected_matches),
                             msg='Did not find correct number of matches for query {}'.format(query))
            # Make sure the matches found are those that are expected.
            for expected_name in expected_matches:
                name_queryset = models.SourceDataset.objects.filter(dataset_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg='Could not find expected dataset name {} with query {}'.format(expected_name, query))


class StudySourceDatasetPHTAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(StudySourceDatasetPHTAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_datasets = []
        self.TEST_PHTS = (5, 50, 500, 500000, 55, 555, 555555, 52, 520, 5200, )
        self.TEST_PHT_QUERIES = {
            '5': (5, 50, 500, 500000, 55, 555, 555555, 52, 520, 5200, ),
            '05': (),
            '0005': (500, 555, 520, ),
            '000005': (5, ),
            '52': (52, 520, 5200, ),
            '052': (),
            '0052': (5200, ),
            '00052': (520, ),
            '555555': (555555, ),
            '0': (5, 50, 500, 55, 555, 52, 520, 5200, ),
        }
        for pht in self.TEST_PHTS:
            self.source_datasets.append(factories.SourceDatasetFactory.create(
                source_study_version=self.source_study_version,
                i_accession=pht
            ))

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:datasets:autocomplete:by-pht', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        tmp = self.get_url(self.study.pk)
        response = self.client.get(tmp)
        self.assertEqual(response.status_code, 200)

    def test_returns_all_datasets_with_no_query(self):
        """Queryset returns all of the datasets with no query."""
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([dataset.pk for dataset in self.source_datasets]), sorted(pks))

    def test_no_deprecated_datasets_in_queryset(self):
        """Queryset returns only the latest version of a dataset."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source datasets and increment their versions. Link it to the new ssv.
        datasets2 = []
        for dataset in self.source_datasets:
            d2 = copy(dataset)
            d2.source_study_version = source_study_version2
            d2.i_id = dataset.i_id + len(self.source_datasets)
            d2.save()
            datasets2.append(d2)
        # Get results from the autocomplete view and make sure only the new versions are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(datasets2))
        for dataset in datasets2:
            self.assertIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertNotIn(dataset.i_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only datasets belonging to the appropriate study."""
        # Delete all but five source traits, so that there are 5 from each study.
        study2 = factories.StudyFactory.create()
        datasets2 = factories.SourceDatasetFactory.create_batch(
            5, source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only datasets from the correct study are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that the other study's datasets do not show up.
        self.assertEqual(len(returned_pks), len(self.source_datasets))
        for dataset in datasets2:
            self.assertNotIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertIn(dataset.i_id, returned_pks)

    def test_pht_test_queries_without_pht_in_string(self):
        """Returns only the correct datasets for each of the TEST_PHT_QUERIES when 'pht' is not in query string."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_PHT_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_PHT_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_pht in expected_matches:
                expected_pk = models.SourceDataset.objects.get(i_accession=expected_pht).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected pht {} with query '{}'".format(expected_pht, query))

    def test_pht_test_queries_with_pht_in_string(self):
        """Returns only the correct source datasets for each of the TEST_PHT_QUERIES when 'pht' is in query string."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_PHT_QUERIES:
            response = self.client.get(url, {'q': 'pht' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_PHT_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_pht in expected_matches:
                expected_pk = models.SourceDataset.objects.get(i_accession=expected_pht).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected pht {} with query '{}'".format(expected_pht, query))


class StudySourceDatasetNameOrPHTAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(StudySourceDatasetNameOrPHTAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_datasets = []
        self.TEST_PHTS = (5, 50, 500, 500000, 55, 555, 555555, 52, 520, 5200, )
        self.TEST_NAMES = ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefg', 'cdefgh', 'bcdefa',
                           'other1', 'other2', 'other3']
        self.TEST_PHT_QUERIES = {
            '5': (5, 50, 500, 500000, 55, 555, 555555, 52, 520, 5200, ),
            '05': (),
            '0005': (500, 555, 520, ),
            '000005': (5, ),
            '52': (52, 520, 5200, ),
            '052': (),
            '0052': (5200, ),
            '00052': (520, ),
            '555555': (555555, ),
            '0': (5, 50, 500, 55, 555, 52, 520, 5200, ),
        }
        self.TEST_NAME_QUERIES = {
            'a': ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefa'],
            'abc': ['abcde', 'abcdef', 'abcd_ef', 'abcd123'],
            'abcd1': ['abcd123'],
            'b': ['abcde', 'abcdef', 'abcd_ef', 'abcd123', 'bcdefg', 'bcdefa'],
            'abcde': ['abcde', 'abcdef'],
            'abcdef': ['abcdef'],
            '123': ['abcd123']
        }
        for dataset_name, pht in zip(self.TEST_NAMES, self.TEST_PHTS):
            self.source_datasets.append(factories.SourceDatasetFactory.create(
                source_study_version=self.source_study_version,
                dataset_name=dataset_name,
                i_accession=pht
            ))

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:datasets:autocomplete:by-name-or-pht', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        tmp = self.get_url(self.study.pk)
        response = self.client.get(tmp)
        self.assertEqual(response.status_code, 200)

    def test_returns_all_datasets_with_no_query(self):
        """Queryset returns all of the datasets with no query."""
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([dataset.pk for dataset in self.source_datasets]), sorted(pks))

    def test_no_deprecated_datasets_in_queryset(self):
        """Queryset returns only the latest version of a dataset."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source datasets and increment their versions. Link it to the new ssv.
        datasets2 = []
        for dataset in self.source_datasets:
            d2 = copy(dataset)
            d2.source_study_version = source_study_version2
            d2.i_id = dataset.i_id + len(self.source_datasets)
            d2.save()
            datasets2.append(d2)
        # Get results from the autocomplete view and make sure only the new versions are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(datasets2))
        for dataset in datasets2:
            self.assertIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertNotIn(dataset.i_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only datasets belonging to the appropriate study."""
        # Delete all but five source datasets, so that there are 5 from each study.
        study2 = factories.StudyFactory.create()
        datasets2 = factories.SourceDatasetFactory.create_batch(
            5, source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only datasets from the correct study are found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that the other study's datasets do not show up.
        self.assertEqual(len(returned_pks), len(self.source_datasets))
        for dataset in datasets2:
            self.assertNotIn(dataset.i_id, returned_pks)
        for dataset in self.source_datasets:
            self.assertIn(dataset.i_id, returned_pks)

    def test_correct_dataset_found_by_name(self):
        """Queryset returns only the correct dataset when found by whole dataset name."""
        dataset_name = 'my_unlikely_dataset_name'
        dataset = factories.SourceDatasetFactory.create(
            dataset_name=dataset_name,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': dataset_name})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(returned_pks, [dataset.i_id])

    def test_correct_dataset_found_by_case_insensitive_name(self):
        """Queryset returns only the correct source dataset when found by whole name, with mismatched case."""
        dataset_name = 'my_unlikely_dataset_name'
        dataset = factories.SourceDatasetFactory.create(
            dataset_name=dataset_name,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': dataset_name.upper()})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(returned_pks, [dataset.i_id])

    def test_name_test_queries(self):
        """Returns only the correct source dataset for each of the TEST_NAME_QUERIES."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_NAME_QUERIES.keys():
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_NAME_QUERIES[query]
            self.assertEqual(len(returned_pks), len(expected_matches),
                             msg='Did not find correct number of matches for query {}'.format(query))
            # Make sure the matches found are those that are expected.
            for expected_name in expected_matches:
                name_queryset = models.SourceDataset.objects.filter(dataset_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg='Could not find expected dataset name {} with query {}'.format(expected_name, query))

    def test_pht_test_queries_without_pht_in_string(self):
        """Returns only the correct datasets for each of the TEST_PHT_QUERIES when 'pht' is not in query string."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_PHT_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_PHT_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_pht in expected_matches:
                expected_pk = models.SourceDataset.objects.get(i_accession=expected_pht).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected pht {} with query '{}'".format(expected_pht, query))

    def test_pht_test_queries_with_pht_in_string(self):
        """Returns only the correct source datasets for each of the TEST_PHT_QUERIES when 'pht' is in query string."""
        url = self.get_url(self.study.pk)
        for query in self.TEST_PHT_QUERIES:
            response = self.client.get(url, {'q': 'pht' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = self.TEST_PHT_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_pht in expected_matches:
                expected_pk = models.SourceDataset.objects.get(i_accession=expected_pht).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected pht {} with query '{}'".format(expected_pht, query))

    def test_correct_dataset_found_with_pht_in_name(self):
        """Queryset returns both datasets when one has dataset name of phtNNN and the other has pht NNN."""
        models.SourceTrait.objects.all().delete()
        name_trait = factories.SourceDatasetFactory.create(
            dataset_name='pht557',
            source_study_version=self.source_study_version
        )
        pht_trait = factories.SourceDatasetFactory.create(
            i_accession=557,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': 'pht557'})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), 2)
        self.assertIn(name_trait.pk, returned_pks)
        self.assertIn(pht_trait.pk, returned_pks)

    def test_dataset_found_when_querying_number_in_name(self):
        """Queryset returns both datasets when one has dataset name of NNN and the other has pht NNN."""
        models.SourceTrait.objects.all().delete()
        # Use a different study to ensure that one of the pre-created datasets doesn't match.
        dataset_name = 'unlikely_24601_dataset'
        # Use an accession that won't match for one dataset but not the other
        dataset_name_match = factories.SourceDatasetFactory.create(
            dataset_name=dataset_name,
            i_accession=123456,
            source_study_version=self.source_study_version
        )
        dataset_accession_match = factories.SourceDatasetFactory.create(
            dataset_name='other_name',
            i_accession=24601,
            source_study_version=self.source_study_version
        )
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': 246})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted(returned_pks), sorted([dataset_name_match.i_id, dataset_accession_match.i_id]))


class StudySourceDatasetSearchTest(UserLoginTestCase):

    def setUp(self):
        super(StudySourceDatasetSearchTest, self).setUp()
        self.study = factories.StudyFactory.create()

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:detail:datasets:search', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data_with_empty_form(self):
        """View has the correct context upon initial load."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIsInstance(context['form'], forms.SourceDatasetSearchForm)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_blank_form(self):
        """View has the correct context upon invalid form submission."""
        response = self.client.get(self.get_url(self.study.pk), {'description': ''})
        context = response.context
        self.assertTrue(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_valid_search_and_no_results(self):
        """View has correct context with a valid search but no results."""
        response = self.client.get(self.get_url(self.study.pk), {'description': 'test'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)

    def test_context_data_with_valid_search_and_some_results(self):
        """View has correct context with a valid search and existing results."""
        dataset = factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_only_finds_results_in_requested_study(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        dataset = factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            source_study_version__study=self.study)
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        get = {'description': 'lorem'}
        response = self.client.get(self.get_url(self.study.pk), get)
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_with_valid_search_and_trait_name(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        dataset = factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            dataset_name='dolor',
            source_study_version__study=self.study)
        factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem other',
            dataset_name='tempor',
            source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem', 'name': 'dolor'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_no_messages_for_initial_load(self):
        """No messages are displayed on initial load of page."""
        response = self.client.get(self.get_url(self.study.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_no_messages_for_invalid_form(self):
        """No messages are displayed if form is invalid."""
        response = self.client.get(self.get_url(self.study.pk), {'description': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_info_message_for_no_results(self):
        """A message is displayed if no results are found."""
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '0 results found.')

    def test_context_data_info_message_for_one_result(self):
        """A message is displayed if one result is found."""
        factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '1 result found.')

    def test_context_data_info_message_for_multiple_result(self):
        """A message is displayed if two results are found."""
        factories.SourceDatasetFactory.create_batch(2, i_dbgap_description='lorem ipsum',
                                                    source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '2 results found.')

    def test_reset_button_works_on_initial_page(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(self.study.pk), {'reset': 'Reset'}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_reset_button_works_with_data_in_form(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(self.study.pk), {'reset': 'Reset', 'name': ''}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_short_words_are_removed(self):
        """Short words are properly removed."""
        dataset_1 = factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            source_study_version__study=self.study
        )
        dataset_2 = factories.SourceDatasetFactory.create(
            i_dbgap_description='lorem ipsum',
            source_study_version__study=self.study
        )
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(dataset_1, context['results_table'].data)
        self.assertIn(dataset_2, context['results_table'].data)

    def test_message_for_ignored_short_words(self):
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Dataset description" field', str(messages[0]))


class StudySourceTableViewsTest(UserLoginTestCase):
    """Unit tests for the SourceTrait by Study views."""

    def test_study_source_table_one_page(self):
        """Tests that the study_source_table view works with fewer rows than will require a second page."""
        # Make less than one page of Studies.
        n_studies = TABLE_PER_PAGE - 2
        factories.StudyFactory.create_batch(n_studies)
        url = reverse('trait_browser:source:studies:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the study table object have n_studies rows?
        self.assertEqual(len(response.context['study_table'].rows), n_studies)

    def test_study_source_table_two_pages(self):
        """Tests that the study_source_table view works with two pages' worth of rows."""
        # Make less than one page of Studies.
        n_studies = TABLE_PER_PAGE * 2
        factories.StudyFactory.create_batch(n_studies)
        url = reverse('trait_browser:source:studies:list')
        response = self.client.get(url)
        # Does the URL work?
        self.assertEqual(response.status_code, 200)
        # Does the study source table object have n_studies rows?
        self.assertEqual(len(response.context['study_table'].rows), n_studies)

    def test_study_source_get_search_url_response(self):
        """Tests that the get_search_url method returns a valid and correct url for a given study."""
        this_study = factories.StudyFactory.create()
        url = this_study.get_search_url()
        response = self.client.get(url)
        # url should work
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], forms.SourceTraitSearchForm)


class StudyNameAutocompleteTest(UserLoginTestCase):

    def get_url(self):
        return reverse('trait_browser:source:studies:autocomplete:by-name')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_studies_with_no_query(self):
        studies = factories.StudyFactory.create_batch(10)
        response = self.client.get(self.get_url())
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([study.pk for study in studies]), sorted(pks))

    def test_works_with_no_studies(self):
        response = self.client.get(self.get_url())
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(pks), 0)

    def test_finds_one_matching_study(self):
        factories.StudyFactory.create(i_study_name='other')
        study = factories.StudyFactory.create(i_study_name='my study')
        response = self.client.get(self.get_url(), {'q': 'stu'})
        pks = get_autocomplete_view_ids(response)
        self.assertEqual([study.pk], pks)

    def test_finds_two_matching_studies(self):
        factories.StudyFactory.create(i_study_name='other')
        study_1 = factories.StudyFactory.create(i_study_name='my study')
        study_2 = factories.StudyFactory.create(i_study_name='another sturgeon')
        response = self.client.get(self.get_url(), {'q': 'stu'})
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([study_1.pk, study_2.pk]), sorted(pks))


class SourceDatasetDetailTest(UserLoginTestCase):
    """Unit tests for the SourceDataset views."""

    def setUp(self):
        super(SourceDatasetDetailTest, self).setUp()
        self.dataset = factories.SourceDatasetFactory.create()
        self.source_traits = factories.SourceTraitFactory.create_batch(10, source_dataset=self.dataset)

    def get_url(self, *args):
        return reverse('trait_browser:source:datasets:detail', args=args)

    def test_absolute_url(self):
        """get_absolute_url returns a 200 as a response."""
        response = self.client.get(self.dataset.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.dataset.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.dataset.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.dataset.pk))
        context = response.context
        self.assertIn('source_dataset', context)
        self.assertEqual(context['source_dataset'], self.dataset)
        self.assertIn('trait_table', context)
        self.assertIsInstance(context['trait_table'], tables.SourceTraitDatasetTable)
        self.assertIn('phs', context)
        self.assertIn('phs_link', context)
        self.assertIn('pht_link', context)
        self.assertIn('trait_count', context)


class SourceDatasetListTest(UserLoginTestCase):
    """Unit tests for the SourceDataset views."""

    def setUp(self):
        super(SourceDatasetListTest, self).setUp()
        self.datasets = factories.SourceDatasetFactory.create_batch(10)
        for ds in self.datasets:
            factories.SourceTraitFactory.create_batch(10, source_dataset=ds)

    def get_url(self, *args):
        return reverse('trait_browser:source:datasets:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('source_dataset_table', context)
        for ds in self.datasets:
            self.assertIn(ds, context['source_dataset_table'].data)
        self.assertIsInstance(context['source_dataset_table'], tables.SourceDatasetTableFull)

    def test_no_deprecated_traits_in_table(self):
        """No deprecated datasets are shown in the table."""
        # Set the ssv for three datasets to deprecated.
        for ds in self.datasets[1:3]:
            ssv = ds.source_study_version
            ssv.i_is_deprecated = True
            ssv.save()
        response = self.client.get(self.get_url())
        context = response.context
        table = context['source_dataset_table']
        for ds in self.datasets:
            if ds.source_study_version.i_is_deprecated:
                self.assertNotIn(ds, table.data)
            else:
                self.assertIn(ds, table.data)

    def test_table_has_no_rows(self):
        """When there are no datasets, there are no rows in the table, but the view still works."""
        models.SourceDataset.objects.all().delete()
        response = self.client.get(self.get_url())
        context = response.context
        table = context['source_dataset_table']
        self.assertEqual(len(table.rows), 0)


class SourceDatasetSearchTest(UserLoginTestCase):
    """Unit tests for SourceDatasetSearch view."""

    def get_url(self, *args):
        return reverse('trait_browser:source:datasets:search')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data_with_empty_form(self):
        """View has the correct context upon initial load."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIsInstance(context['form'], forms.SourceDatasetSearchForm)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_blank_form(self):
        """View has the correct context upon invalid form submission."""
        response = self.client.get(self.get_url(), {'description': ''})
        context = response.context
        self.assertTrue(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_valid_search_and_no_results(self):
        """View has correct context with a valid search but no results."""
        response = self.client.get(self.get_url(), {'description': 'test'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)

    def test_context_data_with_valid_search_and_some_results(self):
        """View has correct context with a valid search and existing results."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        factories.SourceDatasetFactory.create(i_dbgap_description='other')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_with_valid_search_and_a_specified_study(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        study = dataset.source_study_version.study
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem other')
        get = {'description': 'lorem', 'studies': [study.pk]}
        response = self.client.get(self.get_url(), get)
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_with_valid_search_and_dataset_name(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        study = factories.StudyFactory.create()
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum', dataset_name='dolor',
                                                        source_study_version__study=study)
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem other', dataset_name='tempor')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'name': 'dolor'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(dataset)])

    def test_context_data_no_messages_for_initial_load(self):
        """No messages are displayed on initial load of page."""
        response = self.client.get(self.get_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_no_messages_for_invalid_form(self):
        """No messages are displayed if form is invalid."""
        response = self.client.get(self.get_url(), {'description': '', 'name': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_info_message_for_no_results(self):
        """A message is displayed if no results are found."""
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '0 results found.')

    def test_context_data_info_message_for_one_result(self):
        """A message is displayed if one result is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '1 result found.')

    def test_context_data_info_message_for_multiple_result(self):
        """A message is displayed if two results are found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum 2')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '2 results found.')

    def test_table_pagination(self):
        """Table pagination works correctly on the first page."""
        n_datasets = TABLE_PER_PAGE + 2
        factories.SourceDatasetFactory.create_batch(n_datasets, i_dbgap_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertEqual(len(context['results_table'].rows), n_datasets)

    def test_form_works_with_table_pagination_on_second_page(self):
        """Table pagination works correctly on the second page."""
        n_datasets = TABLE_PER_PAGE + 2
        factories.SourceDatasetFactory.create_batch(n_datasets, i_dbgap_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'page': 2})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertEqual(len(context['results_table'].rows), n_datasets)

    def test_table_ordering(self):
        """Traits are ordered by study and then dataset accession."""
        study_1 = factories.StudyFactory.create(i_accession=2)
        dataset_1 = factories.SourceDatasetFactory.create(i_accession=4, source_study_version__study=study_1,
                                                          i_dbgap_description='lorem')
        dataset_2 = factories.SourceDatasetFactory.create(i_accession=3, source_study_version__study=study_1,
                                                          i_dbgap_description='lorem')
        study_2 = factories.StudyFactory.create(i_accession=1)
        dataset_3 = factories.SourceDatasetFactory.create(i_accession=2, source_study_version__study=study_2,
                                                          i_dbgap_description='lorem')
        dataset_4 = factories.SourceDatasetFactory.create(i_accession=1, source_study_version__study=study_2,
                                                          i_dbgap_description='lorem')
        dataset = factories.SourceDatasetFactory.create()
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        table = context['results_table']
        self.assertEqual(list(table.data), [dataset_4, dataset_3, dataset_2, dataset_1])

    def test_reset_button_works_on_initial_page(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset'}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_reset_button_works_with_data_in_form(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset', 'name': ''}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_short_words_in_description_are_removed(self):
        """Short words are properly removed."""
        dataset_1 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        dataset_2 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        response = self.client.get(self.get_url(), {'description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceDatasetTableFull)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(dataset_1, context['results_table'].data)
        self.assertIn(dataset_2, context['results_table'].data)

    def test_message_for_ignored_short_words_in_description(self):
        response = self.client.get(self.get_url(), {'name': 'foo', 'description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Dataset description" field', str(messages[0]))


class HarmonizedTraitSetVersionDetailTest(UserLoginTestCase):
    """Unit tests for the HarmonizedTraitSet views."""

    def setUp(self):
        super(HarmonizedTraitSetVersionDetailTest, self).setUp()
        self.htsv = factories.HarmonizedTraitSetVersionFactory.create()
        self.htraits = factories.HarmonizedTraitFactory.create_batch(
            2, harmonized_trait_set_version=self.htsv, i_is_unique_key=True)
        # Only one of the h. traits can be unique_key=False.
        self.htraits[0].i_is_unique_key = False
        self.htraits[0].save()

    def get_url(self, *args):
        return reverse('trait_browser:harmonized:traits:detail', args=args)

    def test_absolute_url(self):
        """get_absolute_url returns a 200 as a response."""
        response = self.client.get(self.htsv.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.htsv.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.htsv.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.htsv.pk))
        context = response.context
        self.assertIn('harmonized_trait_set_version', context)
        self.assertEqual(context['harmonized_trait_set_version'], self.htsv)


class SourceTraitDetailTest(UserLoginTestCase):

    def setUp(self):
        super(SourceTraitDetailTest, self).setUp()
        self.trait = factories.SourceTraitFactory.create()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertIn('source_trait', context)
        self.assertEqual(context['source_trait'], self.trait)
        self.assertIn('tag_tagged_trait_pairs', context)
        self.assertEqual(context['tag_tagged_trait_pairs'], [])
        self.assertIn('user_is_study_tagger', context)
        self.assertFalse(context['user_is_study_tagger'])

    def test_no_tagged_trait_remove_button(self):
        """The tag removal button shows up."""
        tag = TagFactory.create()
        tagged_trait = TaggedTrait.objects.create(tag=tag, trait=self.trait, creator=self.user)
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertNotContains(response, reverse('tags:tagged-traits:delete', kwargs={'pk': tag.pk}))

    def test_no_tagging_button(self):
        """Regular user does not see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertNotContains(response, reverse('trait_browser:source:traits:tagging', kwargs={'pk': self.trait.pk}))


class SourceTraitDetailPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(SourceTraitDetailPhenotypeTaggerTest, self).setUp()
        self.trait = factories.SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_has_tagged_trait(self):
        """The correct TaggedTrait is in the context."""
        tagged_trait = TaggedTrait.objects.create(tag=self.tag, trait=self.trait, creator=self.user)
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertEqual(context['tag_tagged_trait_pairs'][0], (self.tag, tagged_trait))

    def test_has_tagged_trait_remove_button(self):
        """The tag removal button shows up."""
        tagged_trait = TaggedTrait.objects.create(tag=self.tag, trait=self.trait, creator=self.user)
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertContains(response, reverse('tags:tagged-traits:delete', kwargs={'pk': tagged_trait.pk}))

    def test_no_tagged_trait_remove_button_for_other_study(self):
        """The tag removal button does not show up for a trait from another study."""
        other_trait = factories.SourceTraitFactory.create()
        tagged_trait = TaggedTrait.objects.create(tag=self.tag, trait=other_trait, creator=self.user)
        response = self.client.get(self.get_url(other_trait.pk))
        context = response.context
        self.assertNotContains(response, reverse('tags:tagged-traits:delete', kwargs={'pk': self.tag.pk}))

    def test_has_tagging_button(self):
        """A phenotype tagger does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertContains(response, reverse('trait_browser:source:traits:tagging', kwargs={'pk': self.trait.pk}))

    def test_user_is_study_tagger_true(self):
        """user_is_study_tagger is true in the view's context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertTrue(context['user_is_study_tagger'])


class SourceTraitDetailDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(SourceTraitDetailDCCAnalystTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.trait = factories.SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_has_tagged_trait(self):
        """The correct TaggedTrait is in the context."""
        tagged_trait = TaggedTrait.objects.create(tag=self.tag, trait=self.trait, creator=self.user)
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertEqual(context['tag_tagged_trait_pairs'][0], (self.tag, tagged_trait))

    def test_has_tagged_trait_remove_button(self):
        """The tag removal button shows up."""
        tagged_trait = TaggedTrait.objects.create(tag=self.tag, trait=self.trait, creator=self.user)
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertContains(response, reverse('tags:tagged-traits:delete', kwargs={'pk': tagged_trait.pk}))

    def test_has_tagging_button(self):
        """A phenotype tagger does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertContains(response, reverse('trait_browser:source:traits:tagging', kwargs={'pk': self.trait.pk}))

    def test_user_is_study_tagger_false(self):
        """user_is_study_tagger is false in the view's context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertFalse(context['user_is_study_tagger'])


class SourceTraitListTest(UserLoginTestCase):
    """Unit tests for the SourceTraitList view."""

    def setUp(self):
        super(SourceTraitListTest, self).setUp()
        self.source_traits = factories.SourceTraitFactory.create_batch(
            10, source_dataset__source_study_version__i_is_deprecated=False)

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('source_trait_table', context)
        self.assertIsInstance(context['source_trait_table'], tables.SourceTraitTableFull)

    def test_no_deprecated_traits_in_table(self):
        """No deprecated traits are shown in the table."""
        deprecated_traits = factories.SourceTraitFactory.create_batch(
            10, source_dataset__source_study_version__i_is_deprecated=True)
        response = self.client.get(self.get_url())
        context = response.context
        table = context['source_trait_table']
        for trait in deprecated_traits:
            self.assertNotIn(trait, table.data)
        for trait in self.source_traits:
            self.assertIn(trait, table.data)

    def test_table_has_no_rows(self):
        """When there are no source traits, there are no rows in the table, but the view still works."""
        models.SourceTrait.objects.all().delete()
        response = self.client.get(self.get_url())
        context = response.context
        table = context['source_trait_table']
        self.assertEqual(len(table.rows), 0)


class PhenotypeTaggerSourceTraitTaggingTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(PhenotypeTaggerSourceTraitTaggingTest, self).setUp()
        self.trait = factories.SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('trait_browser:source:traits:tagging', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('trait' in context)
        self.assertEqual(context['trait'], self.trait)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.trait.pk), {'tag': self.tag.pk})
        new_object = TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, TaggedTrait)
        self.assertRedirects(response, reverse('trait_browser:source:traits:detail', args=[self.trait.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_tag(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['tag'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.trait.pk),
                                    {'tag': self.tag.pk})
        new_object = TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_trait_not_in_taggable_studies(self):
        """View returns 403 code when the trait is not in the user's taggable_studies."""
        # Remove the study linked to the trait, but add another study so that taggable_studies is not empty.
        self.user.profile.taggable_studies.remove(self.study)
        another_study = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(another_study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)


class DCCAnalystSourceTraitTaggingTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(DCCAnalystSourceTraitTaggingTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.trait = factories.SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('trait_browser:source:traits:tagging', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.trait.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('trait' in context)
        self.assertEqual(context['trait'], self.trait)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.trait.pk), {'tag': self.tag.pk})
        new_object = TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, TaggedTrait)
        self.assertRedirects(response, reverse('trait_browser:source:traits:detail', args=[self.trait.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_tag(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.trait.pk), {'tag': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['tag'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.trait.pk),
                                    {'tag': self.tag.pk, })
        new_object = TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_forbidden_non_dcc_analyst(self):
        """View returns 403 code when the user is removed from dcc analysts and staff."""
        phenotype_taggers = Group.objects.get(name='dcc_analysts')
        self.user.groups.remove(phenotype_taggers)
        self.user.is_staff = False
        self.user.save()
        self.user.refresh_from_db()
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_with_empty_taggable_studies(self):
        """View returns 200 code when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_with_trait_not_in_taggable_studies(self):
        """View returns 200 code even when the trait is not in the user's taggable_studies."""
        # Remove the study linked to the trait, but add another study so that taggable_studies is not empty.
        self.user.profile.taggable_studies.remove(self.study)
        another_study = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(another_study)
        response = self.client.get(self.get_url(self.trait.pk))
        self.assertEqual(response.status_code, 200)


TEST_PHVS = (5, 50, 500, 50000000, 55, 555, 55555555, 52, 520, 5200, )
TEST_PHV_QUERIES = {'5': (5, 50, 500, 50000000, 55, 555, 55555555, 52, 520, 5200, ),
                    '05': (),
                    '000005': (500, 555, 520, ),
                    '00000005': (5, ),
                    '52': (52, 520, 5200, ),
                    '052': (),
                    '000052': (5200, ),
                    '0000052': (520, ),
                    '55555555': (55555555, ),
                    '0': (5, 50, 500, 55, 555, 52, 520, 5200, ),
                    }


class SourceTraitPHVAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(SourceTraitPHVAutocompleteTest, self).setUp()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset__i_id=6, source_dataset__source_study_version__i_version=2,
                source_dataset__source_study_version__i_is_deprecated=False,
                i_dbgap_variable_accession=phv)
            )

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:by-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Create an older, deprecated version of an existing source trait.
        trait = self.source_traits[0]
        # Make a new copy of the source study version, and decrement the version number.
        ssv2 = copy(trait.source_dataset.source_study_version)
        ssv2.i_version -= 1
        ssv2.i_id += 1
        ssv2.i_is_deprecated = True
        ssv2.save()
        # Make a new copy of the dataset, linked to older ssv.
        ds2 = copy(trait.source_dataset)
        ds2.i_id += 1
        ds2.source_study_version = ssv2
        ds2.save()
        # Copy the source trait and link it to the older dataset.
        trait2 = copy(trait)
        trait2.source_dataset = ds2
        trait2.i_trait_id += 1
        trait2.save()
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url, {'q': trait2.i_dbgap_variable_accession})
        pks = get_autocomplete_view_ids(response)
        self.assertIn(self.source_traits[0].pk, pks)
        self.assertNotIn(trait2.pk, pks)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))


class PhenotypeTaggerTaggableStudyFilteredSourceTraitPHVAutocompleteTest(PhenotypeTaggerLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(PhenotypeTaggerTaggableStudyFilteredSourceTraitPHVAutocompleteTest, self).setUp()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_dbgap_variable_accession=phv))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_returns_all_traits_with_two_taggable_studies(self):
        """Queryset returns all of the traits from two different studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits + source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only traits from the user's taggable studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits))
        for trait in source_traits2:
            self.assertNotIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))


class DCCAnalystTaggableStudyFilteredSourceTraitPHVAutocompleteTest(DCCAnalystLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(DCCAnalystTaggableStudyFilteredSourceTraitPHVAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_dbgap_variable_accession=phv))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns traits from all studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), models.SourceTrait.objects.all().count())
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_with_empty_taggable_studies(self):
        """View returns 200 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_remove_is_staff(self):
        """View returns 403 code when the user is no longer staff."""
        self.user.is_staff = False
        self.user.save()
        self.user.refresh_from_db()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))


TEST_NAMES = ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'c225ab', 'abc_and_ABC', )
TEST_NAME_QUERIES = {'a': ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'abc_and_ABC', ),
                     'A': ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'abc_and_ABC', ),
                     'ab': ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'abc_and_ABC', ),
                     'aB': ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'abc_and_ABC', ),
                     'abc2': ('abc2', 'abc22', ),
                     'abc22': ('abc22', ),
                     'c22': ('c225ab', ),
                     'abc': ('abc', 'ABC', 'aBc', 'abc2', 'abc22', 'abc_and_ABC', ),
                     'abc_and': ('abc_and_ABC', ),
                     '225': (),
                     'very_long_string': (),
                     }


class SourceTraitNameAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(SourceTraitNameAutocompleteTest, self).setUp()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset__i_id=6, source_dataset__source_study_version__i_version=2,
                source_dataset__source_study_version__i_is_deprecated=False,
                i_trait_name=name)
            )

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:by-name')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of traits with the same trait name."""
        # Create an older, deprecated version of an existing source trait.
        trait = self.source_traits[0]
        # Make a new copy of the source study version, and decrement the version number.
        ssv2 = copy(trait.source_dataset.source_study_version)
        ssv2.i_version -= 1
        ssv2.i_id += 1
        ssv2.i_is_deprecated = True
        ssv2.save()
        # Make a new copy of the dataset, linked to older ssv.
        ds2 = copy(trait.source_dataset)
        ds2.i_id += 1
        ds2.source_study_version = ssv2
        ds2.save()
        # Copy the source trait and link it to the older dataset.
        trait2 = copy(trait)
        trait2.source_dataset = ds2
        trait2.i_trait_id += 1
        trait2.save()
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url, {'q': trait.i_trait_name})
        pks = get_autocomplete_view_ids(response)
        self.assertIn(trait.pk, pks)
        self.assertNotIn(trait2.pk, pks)

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))


class PhenotypeTaggerTaggableStudyFilteredSourceTraitNameAutocompleteTest(PhenotypeTaggerLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(PhenotypeTaggerTaggableStudyFilteredSourceTraitNameAutocompleteTest, self).setUp()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_trait_name=name))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-name')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_returns_all_traits_with_two_taggable_studies(self):
        """Queryset returns all of the traits from two different studies."""
        # Delete all source traits and make 5 new ones, so there are only 5 for study 1.
        models.SourceTrait.objects.all().delete()
        self.source_traits = factories.SourceTraitFactory.create_batch(5, source_dataset=self.source_dataset)
        study2 = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits + source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only traits from the user's taggable studies."""
        # Delete all source traits and make 5 new ones, so there are only 5 for study 1.
        models.SourceTrait.objects.all().delete()
        self.source_traits = factories.SourceTraitFactory.create_batch(5, source_dataset=self.source_dataset)
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits))
        for trait in source_traits2:
            self.assertNotIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))


class DCCAnalystTaggableStudyFilteredSourceTraitNameAutocompleteTest(DCCAnalystLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(DCCAnalystTaggableStudyFilteredSourceTraitNameAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_trait_name=name))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-name')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_in_queryset(self):
        """Queryset returns traits from all studies."""
        # Delete all source traits and make 5 new ones, so there are only 5 for study 1.
        models.SourceTrait.objects.all().delete()
        self.source_traits = factories.SourceTraitFactory.create_batch(5, source_dataset=self.source_dataset)
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), models.SourceTrait.objects.all().count())
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_with_empty_taggable_studies(self):
        """View returns 200 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_remove_is_staff(self):
        """View returns 403 code when the user is no longer staff."""
        self.user.is_staff = False
        self.user.save()
        self.user.refresh_from_db()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))


class SourceTraitNameOrPHVAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(SourceTraitNameOrPHVAutocompleteTest, self).setUp()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset__i_id=6, source_dataset__source_study_version__i_version=2,
                source_dataset__source_study_version__i_is_deprecated=False,
                i_dbgap_variable_accession=phv)
            )

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:by-name-or-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of traits with the same trait name."""
        # Create an older, deprecated version of an existing source trait.
        trait = self.source_traits[0]
        # Make a new copy of the source study version, and decrement the version number.
        ssv2 = copy(trait.source_dataset.source_study_version)
        ssv2.i_version -= 1
        ssv2.i_id += 1
        ssv2.i_is_deprecated = True
        ssv2.save()
        # Make a new copy of the dataset, linked to older ssv.
        ds2 = copy(trait.source_dataset)
        ds2.i_id += 1
        ds2.source_study_version = ssv2
        ds2.save()
        # Copy the source trait and link it to the older dataset.
        trait2 = copy(trait)
        trait2.source_dataset = ds2
        trait2.i_trait_id += 1
        trait2.save()
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url, {'q': trait.i_trait_name})
        pks = get_autocomplete_view_ids(response)
        self.assertIn(trait.pk, pks)
        self.assertNotIn(trait2.pk, pks)

    def test_correct_trait_found_by_name(self):
        """Queryset returns only the correct source trait when found by whole trait name."""
        query_trait = self.source_traits[0]
        url = self.get_url()
        response = self.client.get(url, {'q': query_trait.i_trait_name})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(i_trait_name=query_trait.i_trait_name)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_correct_trait_found_by_case_insensitive_name(self):
        """Queryset returns only the correct source trait when found by whole name, with mismatched case."""
        query_trait = self.source_traits[0]
        url = self.get_url()
        response = self.client.get(url, {'q': query_trait.i_trait_name.upper()})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(i_trait_name=query_trait.i_trait_name)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        models.SourceTrait.objects.all().delete()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset__i_id=6, source_dataset__source_study_version__i_version=2,
                source_dataset__source_study_version__i_is_deprecated=False,
                i_trait_name=name)
            )
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))

    def test_correct_trait_found_with_phv_in_name(self):
        """Queryset returns both traits when one has trait name of phvNNN and the other has phv NNN."""
        models.SourceTrait.objects.all().delete()
        name_trait = factories.SourceTraitFactory.create(i_trait_name='phv557')
        phv_trait = factories.SourceTraitFactory.create(i_dbgap_variable_accession=557)
        url = self.get_url()
        response = self.client.get(url, {'q': 'phv557'})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), 2)
        self.assertIn(name_trait.pk, returned_pks)
        self.assertIn(phv_trait.pk, returned_pks)


class PhenotypeTaggerTaggableStudyFilteredSourceTraitNameOrPHVAutocompleteTest(PhenotypeTaggerLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(PhenotypeTaggerTaggableStudyFilteredSourceTraitNameOrPHVAutocompleteTest, self).setUp()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_dbgap_variable_accession=phv))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-name-or-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_returns_all_traits_with_two_taggable_studies(self):
        """Queryset returns all of the traits from two different studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits + source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_not_in_queryset(self):
        """Queryset returns only traits from the user's taggable studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), len(self.source_traits))
        for trait in source_traits2:
            self.assertNotIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_correct_trait_found_by_name(self):
        """Queryset returns only the correct source trait when found by whole trait name."""
        query_trait = self.source_traits[0]
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': query_trait.i_trait_name})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(i_trait_name=query_trait.i_trait_name)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_correct_trait_found_by_case_insensitive_name(self):
        """Queryset returns only the correct source trait when found by whole name, with mismatched case."""
        query_trait = self.source_traits[0]
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': query_trait.i_trait_name.upper()})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(i_trait_name=query_trait.i_trait_name)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        models.SourceTrait.objects.all().delete()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_trait_name=name))
        self.user.refresh_from_db()
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))

    def test_correct_trait_found_with_phv_in_name(self):
        """Queryset returns both traits when one has trait name of phvNNN and the other has phv NNN."""
        models.SourceTrait.objects.all().delete()
        study = models.Study.objects.all().first()
        name_trait = factories.SourceTraitFactory.create(
            i_trait_name='phv557', source_dataset__source_study_version__study=self.study)
        phv_trait = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=557, source_dataset__source_study_version__study=self.study)
        url = self.get_url()
        response = self.client.get(url, {'q': 'phv557'})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), 2)
        self.assertIn(name_trait.pk, returned_pks)
        self.assertIn(phv_trait.pk, returned_pks)


class DCCAnalystTaggableStudyFilteredSourceTraitNameOrPHVAutocompleteTest(DCCAnalystLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(DCCAnalystTaggableStudyFilteredSourceTraitNameOrPHVAutocompleteTest, self).setUp()
        self.study = factories.StudyFactory.create()
        self.source_study_version = factories.SourceStudyVersionFactory.create(study=self.study)
        self.source_dataset = factories.SourceDatasetFactory.create(source_study_version=self.source_study_version)
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for phv in TEST_PHVS:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_dbgap_variable_accession=phv))
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:autocomplete:taggable:by-name-or-phv')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.source_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of a trait."""
        # Copy the source study version and increment it.
        source_study_version2 = copy(self.source_study_version)
        source_study_version2.i_version += 1
        source_study_version2.i_id += 1
        source_study_version2.save()
        # Make the old ssv deprecated.
        self.source_study_version.i_is_deprecated = True
        self.source_study_version.save()
        # Copy the source dataset and increment it. Link it to the new ssv.
        source_dataset2 = copy(self.source_dataset)
        source_dataset2.i_id += 1
        source_dataset2.source_study_version = source_study_version2
        source_dataset2.save()
        # Copy the source traits and link them to the new source dataset.
        source_traits2 = []
        for trait in self.source_traits:
            st2 = copy(trait)
            st2.source_dataset = source_dataset2
            st2.i_trait_id = trait.i_trait_id + len(self.source_traits)
            st2.save()
            source_traits2.append(st2)
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), len(source_traits2))
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertNotIn(trait.i_trait_id, returned_pks)

    def test_other_study_in_queryset(self):
        """Queryset returns traits from all studies."""
        # Delete all but five source traits, so that there are 5 from each study.
        models.SourceTrait.objects.exclude(i_dbgap_variable_accession__in=TEST_PHVS[:5]).delete()
        self.source_traits = list(models.SourceTrait.objects.all())
        study2 = factories.StudyFactory.create()
        source_traits2 = factories.SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version__study=study2)
        # Get results from the autocomplete view and make sure only the correct study is found.
        url = self.get_url(self.study.pk)
        response = self.client.get(url)
        returned_pks = get_autocomplete_view_ids(response)
        # Make sure that there's only one page of results.
        self.assertTrue(models.SourceTrait.objects.all().count() <= 10)
        self.assertEqual(len(returned_pks), models.SourceTrait.objects.all().count())
        for trait in source_traits2:
            self.assertIn(trait.i_trait_id, returned_pks)
        for trait in self.source_traits:
            self.assertIn(trait.i_trait_id, returned_pks)

    def test_correct_trait_found_by_name(self):
        """Queryset returns only the correct source trait when found by whole trait name."""
        query_trait = self.source_traits[0]
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': query_trait.i_trait_name})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(
            i_trait_name=query_trait.i_trait_name, source_dataset__source_study_version__study=self.study)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_correct_trait_found_by_case_insensitive_name(self):
        """Queryset returns only the correct source trait when found by whole name, with mismatched case."""
        query_trait = self.source_traits[0]
        url = self.get_url(self.study.pk)
        response = self.client.get(url, {'q': query_trait.i_trait_name.upper()})
        returned_pks = get_autocomplete_view_ids(response)
        # Get traits that have the same trait name, to account for how small the word lists for faker are.
        traits_with_name = models.SourceTrait.objects.filter(i_trait_name=query_trait.i_trait_name)
        self.assertEqual(len(returned_pks), len(traits_with_name))
        for name_trait in traits_with_name:
            self.assertIn(name_trait.pk, returned_pks)

    def test_with_empty_taggable_studies(self):
        """View returns 200 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_remove_is_staff(self):
        """View returns 403 code when the user is no longer staff."""
        self.user.is_staff = False
        self.user.save()
        self.user.refresh_from_db()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_phv_test_queries_without_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is not in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_phv_test_queries_with_phv_in_string(self):
        """Returns only the correct source trait for each of the TEST_PHV_QUERIES when 'phv' is in query string."""
        url = self.get_url()
        for query in TEST_PHV_QUERIES:
            response = self.client.get(url, {'q': 'phv' + query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_PHV_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_phv in expected_matches:
                expected_pk = models.SourceTrait.objects.get(i_dbgap_variable_accession=expected_phv).pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected phv {} with query '{}'".format(expected_phv, query))

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        models.SourceTrait.objects.all().delete()
        # Create 10 source traits from the same dataset, with non-deprecated ssv of version 2.
        self.source_traits = []
        for name in TEST_NAMES:
            self.source_traits.append(factories.SourceTraitFactory.create(
                source_dataset=self.source_dataset, i_trait_name=name))
        self.user.refresh_from_db()
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_queryset = models.SourceTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_queryset.count(), 1)
                expected_pk = name_queryset.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))

    def test_correct_trait_found_with_phv_in_name(self):
        """Queryset returns both traits when one has trait name of phvNNN and the other has phv NNN."""
        models.SourceTrait.objects.all().delete()
        study = models.Study.objects.all().first()
        name_trait = factories.SourceTraitFactory.create(
            i_trait_name='phv557', source_dataset__source_study_version__study=self.study)
        phv_trait = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=557, source_dataset__source_study_version__study=self.study)
        url = self.get_url()
        response = self.client.get(url, {'q': 'phv557'})
        returned_pks = get_autocomplete_view_ids(response)
        self.assertEqual(len(returned_pks), 2)
        self.assertIn(name_trait.pk, returned_pks)
        self.assertIn(phv_trait.pk, returned_pks)


class HarmonizedTraitListTest(UserLoginTestCase):
    """Unit tests for the HarmonizedTraitList view."""

    def setUp(self):
        super(HarmonizedTraitListTest, self).setUp()
        self.harmonized_traits = factories.HarmonizedTraitFactory.create_batch(
            10, harmonized_trait_set_version__i_is_deprecated=False)

    def get_url(self, *args):
        return reverse('trait_browser:harmonized:traits:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('harmonized_trait_table', context)
        self.assertIsInstance(context['harmonized_trait_table'], tables.HarmonizedTraitTable)

    def test_no_deprecated_traits_in_table(self):
        """No deprecated traits are shown in the table."""
        deprecated_traits = factories.HarmonizedTraitFactory.create_batch(
            10, harmonized_trait_set_version__i_is_deprecated=True)
        response = self.client.get(self.get_url())
        context = response.context
        table = context['harmonized_trait_table']
        for trait in deprecated_traits:
            self.assertNotIn(trait, table.data)
        for trait in self.harmonized_traits:
            self.assertIn(trait, table.data)

    def test_no_unique_key_traits_in_table(self):
        """No unique key traits are shown in the table."""
        uk_traits = factories.HarmonizedTraitFactory.create_batch(10, i_is_unique_key=True)
        response = self.client.get(self.get_url())
        context = response.context
        table = context['harmonized_trait_table']
        for trait in uk_traits:
            self.assertNotIn(trait, table.data)
        for trait in self.harmonized_traits:
            self.assertIn(trait, table.data)

    def test_table_has_no_rows(self):
        """When there are no harmonized traits, there are no rows in the table, but the view still works."""
        models.HarmonizedTrait.objects.all().delete()
        response = self.client.get(self.get_url())
        context = response.context
        table = context['harmonized_trait_table']
        self.assertEqual(len(table.rows), 0)


class HarmonizedTraitFlavorNameAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(HarmonizedTraitFlavorNameAutocompleteTest, self).setUp()
        # Create 10 harmonized traits, non-deprecated.
        self.harmonized_traits = []
        for name in TEST_NAMES:
            self.harmonized_traits.append(factories.HarmonizedTraitFactory.create(
                harmonized_trait_set_version__i_is_deprecated=False, i_trait_name=name,
                harmonized_trait_set_version__i_version=2,
                harmonized_trait_set_version__harmonized_trait_set__i_flavor=1)
            )

    def get_url(self, *args):
        return reverse('trait_browser:harmonized:traits:autocomplete:by-name')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the traits with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([trait.pk for trait in self.harmonized_traits]), sorted(pks))

    def test_no_deprecated_traits_in_queryset(self):
        """Queryset returns only the latest version of traits with the same trait name."""
        # Create an older, deprecated version of an existing source trait.
        trait = self.harmonized_traits[0]
        # Make a new copy of the harmonized_trait_set_version, and decrement the version number.
        htsv2 = copy(trait.harmonized_trait_set_version)
        htsv2.i_version -= 1
        htsv2.i_id += 1
        htsv2.i_is_deprecated = True
        htsv2.save()
        # Note that the new htsv is still liknked to the existing h. trait set.
        # Copy the harmonized trait and link it to the older htsv.
        trait2 = copy(trait)
        trait2.harmonized_trait_set_version = htsv2
        trait2.i_trait_id += 1
        trait2.save()
        # Get results from the autocomplete view and make sure only the new version is found.
        url = self.get_url()
        response = self.client.get(url, {'q': trait.i_trait_name})
        pks = get_autocomplete_view_ids(response)
        self.assertIn(trait.pk, pks)
        self.assertNotIn(trait2.pk, pks)

    def test_name_test_queries(self):
        """Returns only the correct source trait for each of the TEST_NAME_QUERIES."""
        url = self.get_url()
        for query in TEST_NAME_QUERIES:
            response = self.client.get(url, {'q': query})
            returned_pks = get_autocomplete_view_ids(response)
            expected_matches = TEST_NAME_QUERIES[query]
            # Make sure number of matches is as expected.
            self.assertEqual(len(returned_pks), len(expected_matches))
            # Make sure the matches that are found are the ones expected.
            for expected_name in expected_matches:
                # This filter should only have one result, but I want to make sure.
                name_qs = models.HarmonizedTrait.objects.filter(i_trait_name__regex=r'^{}$'.format(expected_name))
                self.assertEqual(name_qs.count(), 1)
                expected_pk = name_qs.first().pk
                self.assertIn(expected_pk, returned_pks,
                              msg="Could not find expected trait name {} with query '{}'".format(expected_name, query))


class SourceTraitSearchTest(ClearSearchIndexMixin, UserLoginTestCase):

    def get_url(self, *args):
        return reverse('trait_browser:source:traits:search')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data_with_empty_form(self):
        """View has the correct context upon initial load."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIsInstance(context['form'], forms.SourceTraitSearchMultipleStudiesForm)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_blank_form(self):
        """View has the correct context upon invalid form submission."""
        response = self.client.get(self.get_url(), {'description': ''})
        context = response.context
        self.assertTrue(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_valid_search_and_no_results(self):
        """View has correct context with a valid search but no results."""
        response = self.client.get(self.get_url(), {'description': 'test'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)

    def test_context_data_with_valid_search_and_some_results(self):
        """View has correct context with a valid search and existing results."""
        factories.SourceTraitFactory.create(i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        qs = searches.search_source_traits(description='lorem')
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(qs, [repr(x) for x in context['results_table'].data])

    def test_context_data_with_valid_search_and_a_specified_study(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        study = trait.source_dataset.source_study_version.study
        factories.SourceTraitFactory.create(i_description='lorem other')
        get = {'description': 'lorem', 'studies': [study.pk]}
        response = self.client.get(self.get_url(), get)
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(trait)])

    def test_context_data_with_valid_search_and_trait_name(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum', i_trait_name='dolor')
        factories.SourceTraitFactory.create(i_description='lorem other', i_trait_name='tempor')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'name': 'dolor'})
        qs = searches.search_source_traits(description='lorem', name='dolor')
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(qs, [repr(x) for x in context['results_table'].data])

    def test_context_data_no_messages_for_initial_load(self):
        """No messages are displayed on initial load of page."""
        response = self.client.get(self.get_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_no_messages_for_invalid_form(self):
        """No messages are displayed if form is invalid."""
        response = self.client.get(self.get_url(), {'description': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_info_message_for_no_results(self):
        """A message is displayed if no results are found."""
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '0 results found.')

    def test_context_data_info_message_for_one_result(self):
        """A message is displayed if one result is found."""
        factories.SourceTraitFactory.create(i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '1 result found.')

    def test_context_data_info_message_for_multiple_result(self):
        """A message is displayed if two results are found."""
        factories.SourceTraitFactory.create(i_description='lorem ipsum')
        factories.SourceTraitFactory.create(i_description='lorem ipsum 2')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '2 results found.')

    def test_table_pagination(self):
        """Table pagination works correctly on the first page."""
        n_traits = TABLE_PER_PAGE + 2
        factories.SourceTraitFactory.create_batch(n_traits, i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), n_traits)

    def test_form_works_with_table_pagination_on_second_page(self):
        """Table pagination works correctly on the second page."""
        n_traits = TABLE_PER_PAGE + 2
        factories.SourceTraitFactory.create_batch(n_traits, i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'page': 2})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), n_traits)

    def test_table_ordering(self):
        """Traits are ordered by dataset and then variable accession."""
        dataset = factories.SourceDatasetFactory.create()
        trait_1 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=2,
            source_dataset=dataset, i_description='lorem ipsum')
        trait_2 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=1,
            source_dataset=dataset, i_description='lorem other')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        table = context['results_table']
        self.assertEqual(list(table.data), [trait_2, trait_1])

    def test_reset_button_works_on_initial_page(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset'}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_reset_button_works_with_data_in_form(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset', 'name': ''}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_short_words_in_trait_description_are_removed(self):
        """Short words are properly removed."""
        trait_1 = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        trait_2 = factories.SourceTraitFactory.create(i_description='lorem')
        response = self.client.get(self.get_url(), {'description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(trait_1, context['results_table'].data)
        self.assertIn(trait_2, context['results_table'].data)

    def test_message_for_ignored_short_words_in_trait_description(self):
        response = self.client.get(self.get_url(), {'description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Variable description" field', str(messages[0]))

    def test_filters_by_dataset_description_if_requested(self):
        """View has correct results when filtering by dataset."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='a dataset about demographic measurements')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum', source_dataset=dataset)
        other_dataset = factories.SourceDatasetFactory.create(i_dbgap_description='foo')
        factories.SourceTraitFactory.create(i_description='lorem ipsum', source_dataset=other_dataset)
        response = self.client.get(self.get_url(), {'description': 'lorem', 'dataset_description': 'demographic', 'dataset_name': ''})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(trait)])

    def test_finds_no_traits_if_dataset_search_doesnt_match(self):
        """View has correct results when filtering by dataset."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='a dataset about demographic measurements')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum', source_dataset=dataset)
        response = self.client.get(self.get_url(), {'description': 'lorem', 'dataset_description': 'something'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_short_words_in_dataset_description_are_removed(self):
        """Short words are properly removed."""
        dataset_1 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        trait_1 = factories.SourceTraitFactory.create(i_trait_name='foobar', source_dataset=dataset_1)
        dataset_2 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        trait_2 = factories.SourceTraitFactory.create(i_trait_name='foobar', source_dataset=dataset_2)
        response = self.client.get(self.get_url(), {'name': 'foobar', 'dataset_description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(trait_1, context['results_table'].data)
        self.assertIn(trait_2, context['results_table'].data)

    def test_message_for_ignored_short_words_in_dataset_description(self):
        response = self.client.get(self.get_url(), {'name': 'foo', 'dataset_description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Dataset description" field', str(messages[0]))

    def test_message_for_short_words_in_both_trait_and_dataset_descriptions(self):
        response = self.client.get(self.get_url(), {'description': 'lo ipsum', 'dataset_description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 3)
        self.assertEqual('Ignored short words in "Variable description" field: lo', str(messages[0]))
        self.assertEqual('Ignored short words in "Dataset description" field: ip', str(messages[1]))


class SourceTraitSearchByStudyTest(ClearSearchIndexMixin, UserLoginTestCase):

    def setUp(self):
        super(SourceTraitSearchByStudyTest, self).setUp()
        self.study = factories.StudyFactory.create()

    def get_url(self, *args):
        return reverse('trait_browser:source:studies:search', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data_with_empty_form(self):
        """View has the correct context upon initial load."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIsInstance(context['form'], forms.SourceTraitSearchForm)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_blank_form(self):
        """View has the correct context upon invalid form submission."""
        response = self.client.get(self.get_url(self.study.pk), {'description': ''})
        context = response.context
        self.assertTrue(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_valid_search_and_no_results(self):
        """View has correct context with a valid search but no results."""
        response = self.client.get(self.get_url(self.study.pk), {'description': 'test'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)

    def test_context_data_with_valid_search_and_some_results(self):
        """View has correct context with a valid search and existing results."""
        factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        qs = searches.search_source_traits(description='lorem')
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(qs, [repr(x) for x in context['results_table'].data])

    def test_context_data_only_finds_results_in_requested_study(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        trait = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study)
        factories.SourceTraitFactory.create(i_description='lorem ipsum')
        get = {'description': 'lorem'}
        response = self.client.get(self.get_url(self.study.pk), get)
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(trait)])

    def test_context_data_with_valid_search_and_trait_name(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        trait = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            i_trait_name='dolor',
            source_dataset__source_study_version__study=self.study)
        factories.SourceTraitFactory.create(
            i_description='lorem other',
            i_trait_name='tempor',
            source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem', 'name': 'dolor'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(trait)])

    def test_context_data_no_messages_for_initial_load(self):
        """No messages are displayed on initial load of page."""
        response = self.client.get(self.get_url(self.study.pk))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_no_messages_for_invalid_form(self):
        """No messages are displayed if form is invalid."""
        response = self.client.get(self.get_url(self.study.pk), {'description': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_info_message_for_no_results(self):
        """A message is displayed if no results are found."""
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '0 results found.')

    def test_context_data_info_message_for_one_result(self):
        """A message is displayed if one result is found."""
        factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '1 result found.')

    def test_context_data_info_message_for_multiple_result(self):
        """A message is displayed if two results are found."""
        factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study)
        factories.SourceTraitFactory.create(
            i_description='lorem ipsum 2',
            source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '2 results found.')

    def test_reset_button_works_on_initial_page(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(self.study.pk), {'reset': 'Reset'}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_reset_button_works_with_data_in_form(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(self.study.pk), {'reset': 'Reset', 'name': ''}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_context_data_with_valid_search_trait_description_and_dataset(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        dataset = factories.SourceDatasetFactory.create(source_study_version__study=self.study)
        other_dataset = factories.SourceDatasetFactory.create(source_study_version__study=self.study)
        trait = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            i_trait_name='dolor',
            source_dataset=dataset
        )
        factories.SourceTraitFactory.create(
            i_description='lorem other',
            i_trait_name='tempor',
            source_dataset=other_dataset
        )
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem', 'datasets': [dataset.pk]})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertQuerysetEqual(context['results_table'].data, [repr(trait)])

    def test_context_data_with_dataset_from_a_different_study(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        other_study = factories.StudyFactory.create()
        dataset = factories.SourceDatasetFactory.create(source_study_version__study=other_study)
        trait = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            i_trait_name='dolor',
            source_dataset=dataset
        )
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem', 'datasets': [dataset.pk]})
        self.assertFormError(response, "form", 'datasets', forms.SourceTraitSearchOneStudyForm.ERROR_DIFFERENT_STUDY)

    def test_context_data_with_deprecated_dataset(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        study_version = factories.SourceStudyVersionFactory(i_is_deprecated=True, study=self.study)
        dataset = factories.SourceDatasetFactory.create(source_study_version=study_version)
        trait = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            i_trait_name='dolor',
            source_dataset=dataset
        )
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem', 'datasets': [dataset.pk]})
        self.assertFormError(response, "form", 'datasets',
                             forms.SourceTraitSearchOneStudyForm.ERROR_DEPRECATED_DATASET)

    def test_short_words_are_removed(self):
        """Short words are properly removed."""
        trait_1 = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study
        )
        trait_2 = factories.SourceTraitFactory.create(
            i_description='lorem ipsum',
            source_dataset__source_study_version__study=self.study
        )
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.SourceTraitTableFull)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(trait_1, context['results_table'].data)
        self.assertIn(trait_2, context['results_table'].data)

    def test_message_for_ignored_short_words(self):
        response = self.client.get(self.get_url(self.study.pk), {'description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Variable description" field', str(messages[0]))


class HarmonizedTraitSearchTest(ClearSearchIndexMixin, UserLoginTestCase):

    def get_url(self, *args):
        return reverse('trait_browser:harmonized:traits:search')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data_with_empty_form(self):
        """View has the correct context upon initial load."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_blank_form(self):
        """View has the correct context upon invalid form submission."""
        response = self.client.get(self.get_url(), {'description': ''})
        context = response.context
        self.assertTrue(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)

    def test_context_data_with_valid_search_and_no_results(self):
        """View has correct context with a valid search but no results."""
        response = self.client.get(self.get_url(), {'description': 'test'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)

    def test_context_data_with_valid_search_and_some_results(self):
        """View has correct context with a valid search and existing results."""
        factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        qs = searches.search_harmonized_traits(description='lorem')
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)
        self.assertQuerysetEqual(qs, [repr(x) for x in context['results_table'].data])

    def test_context_data_with_valid_search_and_trait_name(self):
        """View has correct context with a valid search and existing results if a study is selected."""
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum', i_trait_name='dolor')
        factories.HarmonizedTraitFactory.create(i_description='lorem other', i_trait_name='tempor')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'name': 'dolor'})
        qs = searches.search_harmonized_traits(description='lorem', name='dolor')
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)
        self.assertQuerysetEqual(qs, [repr(x) for x in context['results_table'].data])

    def test_context_data_no_messages_for_initial_load(self):
        """No messages are displayed on initial load of page."""
        response = self.client.get(self.get_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_no_messages_for_invalid_form(self):
        """No messages are displayed if form is invalid."""
        response = self.client.get(self.get_url(), {'description': ''})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_context_data_info_message_for_no_results(self):
        """A message is displayed if no results are found."""
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '0 results found.')

    def test_context_data_info_message_for_one_result(self):
        """A message is displayed if one result is found."""
        factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '1 result found.')

    def test_context_data_info_message_for_multiple_result(self):
        """A message is displayed if two results are found."""
        factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        factories.HarmonizedTraitFactory.create(i_description='lorem ipsum 2')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '2 results found.')

    def test_table_pagination(self):
        """Table pagination works correctly on the first page."""
        n_traits = TABLE_PER_PAGE + 2
        factories.HarmonizedTraitFactory.create_batch(n_traits, i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)
        self.assertEqual(len(context['results_table'].rows), n_traits)

    def test_form_works_with_table_pagination_on_second_page(self):
        """Table pagination works correctly on the second page."""
        n_traits = TABLE_PER_PAGE + 2
        factories.HarmonizedTraitFactory.create_batch(n_traits, i_description='lorem ipsum')
        response = self.client.get(self.get_url(), {'description': 'lorem', 'page': 2})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)
        self.assertEqual(len(context['results_table'].rows), n_traits)

    def test_reset_button_works_on_initial_page(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset'}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_reset_button_works_with_data_in_form(self):
        """Reset button returns to original page."""
        response = self.client.get(self.get_url(), {'reset': 'Reset', 'name': ''}, follow=True)
        context = response.context
        self.assertIn('form', context)
        self.assertFalse(context['form'].is_bound)
        self.assertFalse(context['has_results'])
        self.assertIn('results_table', context)
        self.assertEqual(len(context['results_table'].rows), 0)

    def test_short_words_are_removed(self):
        """Short words are properly removed."""
        trait_1 = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        trait_2 = factories.HarmonizedTraitFactory.create(i_description='lorem')
        response = self.client.get(self.get_url(), {'description': 'lorem ip'})
        context = response.context
        self.assertIn('form', context)
        self.assertTrue(context['has_results'])
        self.assertIsInstance(context['results_table'], tables.HarmonizedTraitTable)
        self.assertEqual(len(context['results_table'].rows), 2)
        self.assertIn(trait_1, context['results_table'].data)
        self.assertIn(trait_2, context['results_table'].data)

    def test_message_for_ignored_short_words(self):
        response = self.client.get(self.get_url(), {'description': 'lorem ip'})
        context = response.context
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 2)
        self.assertIn('Ignored short words in "Variable description" field', str(messages[0]))


# Test of the login-required for each URL in the app.
class TraitBrowserLoginRequiredTest(LoginRequiredTestCase):

    def test_trait_browser_login_required(self):
        """All trait_browser urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('trait_browser')
