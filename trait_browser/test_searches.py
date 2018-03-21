"""Test the functions in searches.py."""

from django.test import TestCase

from watson.models import SearchEntry

from . import models
from . import factories
from . import searches


class ClearSearchIndexMixin(object):
    """Clear django-watson search index records in tests.

    Normally, django runs the TestCase tests in a transaction, but this doesn't
    work for the watson search records because they are stored in a MyISAM
    table, which doesn't use transactions. The records in the table therefore
    need to be cleared after each test.
    """

    def tearDown(self):
        super(ClearSearchIndexMixin, self).tearDown()
        SearchEntry.objects.all().delete()


class SourceDatasetSearchTest(ClearSearchIndexMixin, TestCase):

    def test_returns_all_datasets_with_no_input(self):
        """All datasets are returned if nothing is passed to search."""
        datasets = factories.SourceDatasetFactory.create_batch(10)
        qs = searches.search_source_datasets()
        self.assertEqual(qs.count(), models.SourceDataset.objects.current().count())

    def test_does_not_find_deprecated_datasets(self):
        """No deprecated datasets are returned if nothing is passed to search."""
        dataset = factories.SourceDatasetFactory.create()
        dataset.source_study_version.i_is_deprecated = True
        dataset.source_study_version.save()
        qs = searches.search_source_datasets()
        self.assertEqual(qs.count(), 0)

    def test_description_no_matches(self):
        """No results are found if the search query doesn't match the dataset description."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        qs = searches.search_source_datasets(description='foobar')
        self.assertQuerysetEqual(qs, [])

    def test_description_one_word_exact_match(self):
        """Only the dataset whose description that matches the search query is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        qs = searches.search_source_datasets(description='lorem')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_one_word_substring_match(self):
        """Only the dataset whose description contains words that begin with the search query is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        qs = searches.search_source_datasets(description='lore')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_one_word_substring_matches_beginning_of_word_only(self):
        """Only datasets whose descriptions contains words that end with the search query are not found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        qs = searches.search_source_datasets(description='orem')
        self.assertEqual(qs.count(), 0)

    def test_description_one_word_substring_match_short_search(self):
        """Only datasets whose description contains words that begin with a (short) search query are found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem')
        qs = searches.search_source_datasets(description='lo')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_one_word_substring_match_short_word(self):
        """Short word with three letters in the description are found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='abc')
        qs = searches.search_source_datasets(description='abc')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_multiple_words_exact_match(self):
        """Only datasets whose description contains words that exactly match multiple search terms is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        qs = searches.search_source_datasets(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_multiple_words_substring_match(self):
        """Only datasets whose description contains words that begin with multiple search terms is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        qs = searches.search_source_datasets(description='lore ipsu')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_match_can_be_anywhere(self):
        """Datasets are found when the search query term is not the first word."""
        factories.SourceDatasetFactory.create(i_dbgap_description='other dataset')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        qs = searches.search_source_datasets(description='ipsu')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_finds_only_descriptions_with_all_search_terms(self):
        """Dataset whose descriptions contain all words in the search query is found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem other words')
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum other words')
        qs = searches.search_source_datasets(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_matches_search_terms_in_any_order(self):
        """Datasets whose descriptions contain all search query words in any order are found."""
        factories.SourceDatasetFactory.create(i_dbgap_description='lorem other words')
        dataset_1 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum other words')
        dataset_2 = factories.SourceDatasetFactory.create(i_dbgap_description='ipsum lorem other words')
        qs = searches.search_source_datasets(description='ipsum lorem')
        self.assertIn(dataset_1, qs)
        self.assertIn(dataset_2, qs)

    def test_description_stop_words(self):
        """Dataset whose description contains common default stop words is found."""
        # However is a stopword in MySQL by default.
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='however has stop words')
        qs = searches.search_source_datasets(description='however')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_is_case_insensitive(self):
        """Datasets whose descriptions match search term but with different case are found."""
        dataset_1 = factories.SourceDatasetFactory.create(i_dbgap_description='lorem ipsum')
        dataset_2 = factories.SourceDatasetFactory.create(i_dbgap_description='LOREM other')
        qs = searches.search_source_datasets(description='lorem')
        self.assertIn(dataset_1, qs)
        self.assertIn(dataset_2, qs)

    def test_description_does_not_match_dataset_name_field(self):
        """datasets whose name field matches description query are not found."""
        factories.SourceDatasetFactory.create(
            dataset_name='lorem',
            i_dbgap_description='other description')
        qs = searches.search_source_datasets(description='lorem')
        self.assertEqual(len(qs), 0)

    def test_dataset_name_does_not_match_description_field(self):
        """datasets whose description field matches name query are not found."""
        factories.SourceDatasetFactory.create(
            dataset_name='other',
            i_dbgap_description='lorem')
        qs = searches.search_source_datasets(name='lorem')
        self.assertEqual(len(qs), 0)

    def test_description_can_include_a_number(self):
        """Can search for "words" that contain both letters and numbers."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='abcd123')
        qs = searches.search_source_datasets(description='abcd123')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_description_can_be_only_numbers(self):
        """Can search for "words" that contain only letters."""
        dataset = factories.SourceDatasetFactory.create(i_dbgap_description='123456')
        qs = searches.search_source_datasets(description='123456')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_finds_matching_dataset_in_one_specified_study(self):
        """Datasets only in the requested study are found."""
        factories.StudyFactory.create()
        dataset = factories.SourceDatasetFactory.create()
        qs = searches.search_source_datasets(studies=[dataset.source_study_version.study.pk])
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_finds_matching_dataset_in_two_specified_studies(self):
        """Datasets in two requested studies are found."""
        dataset_1 = factories.SourceDatasetFactory.create()
        dataset_2 = factories.SourceDatasetFactory.create()
        studies = [
            dataset_1.source_study_version.study.pk,
            dataset_2.source_study_version.study.pk,
        ]
        qs = searches.search_source_datasets(studies=studies)
        self.assertEqual(qs.count(), 2)
        self.assertIn(dataset_1, qs)
        self.assertIn(dataset_2, qs)

    def test_finds_only_exact_match_name(self):
        """Dataset name must be an exact match."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum')
        factories.SourceDatasetFactory.create(dataset_name='other')
        qs = searches.search_source_datasets(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_name_finds_case_insensitive_match(self):
        """Dataset name can be case insensitive."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='IpSuM')
        factories.SourceDatasetFactory.create(dataset_name='other')
        qs = searches.search_source_datasets(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_does_not_find_substring_name_match(self):
        """Substrings of dataset names are not matched by default."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum')
        qs = searches.search_source_datasets(name='ipsu')
        self.assertEqual(len(qs), 0)

    def test_finds_name_beginning_with_requested_string_if_specified(self):
        """Substrings of at the beginning of dataset names are matched if requested."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum')
        qs = searches.search_source_datasets(name='ipsu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_finds_name_containing_requested_string_if_specified(self):
        """Substrings of dataset names are matched if requested."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum')
        qs = searches.search_source_datasets(name='psu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_works_with_both_dataset_name_and_description(self):
        """Searching works when dataset name and description are both specified."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum', i_dbgap_description='lorem')
        factories.SourceDatasetFactory.create(dataset_name='ipsum', i_dbgap_description='other')
        factories.SourceDatasetFactory.create(dataset_name='other', i_dbgap_description='lorem')
        qs = searches.search_source_datasets(name='ipsum', description='lorem')
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_works_with_dataset_name_description_and_study(self):
        """Searching works when dataset name, description, and study are all specified."""
        dataset = factories.SourceDatasetFactory.create(dataset_name='ipsum', i_dbgap_description='lorem')
        factories.SourceDatasetFactory.create(dataset_name='ipsum', i_dbgap_description='lorem')
        study = dataset.source_study_version.study
        qs = searches.search_source_datasets(name='ipsum', description='lorem', studies=[study.pk])
        self.assertQuerysetEqual(qs, [repr(dataset)])

    def test_default_ordering_by_dataset(self):
        """Datasets are ordered by dataset accession."""
        dataset_1 = factories.SourceDatasetFactory.create(i_accession=2)
        dataset_2 = factories.SourceDatasetFactory.create(i_accession=1)
        qs = searches.search_source_datasets()
        self.assertEqual(list(qs), [dataset_2, dataset_1])

    def test_does_not_find_special_characters_in_description(self):
        """Special characters are ignored."""
        characters = ['\'', '%', '#', '<', '>', '=', '?', '-']
        for character in characters:
            description = "special{char}character".format(char=character)
            dataset = factories.SourceDatasetFactory.create(dataset_name=description)
            qs = searches.search_source_datasets(description=description)
            msg = "found {char}".format(char=character)
            self.assertNotIn(dataset, qs, msg=msg)


class SourceTraitSearchTest(ClearSearchIndexMixin, TestCase):

    def test_returns_all_traits_with_no_input(self):
        """All traits are returned if nothing is passed to search."""
        traits = factories.SourceTraitFactory.create_batch(10)
        qs = searches.search_source_traits()
        self.assertEqual(qs.count(), models.SourceTrait.objects.current().count())

    def test_does_not_find_deprecated_traits(self):
        """No deprecated traits are returned if nothing is passed to search."""
        trait = factories.SourceTraitFactory.create()
        trait.source_dataset.source_study_version.i_is_deprecated = True
        trait.source_dataset.source_study_version.save()
        qs = searches.search_source_traits()
        self.assertEqual(qs.count(), 0)

    def test_description_no_matches(self):
        """No results are found if the search query doesn't match the trait description."""
        trait = factories.SourceTraitFactory.create(i_description='lorem')
        qs = searches.search_source_traits(description='foobar')
        self.assertQuerysetEqual(qs, [])

    def test_description_one_word_exact_match(self):
        """Only the trait whose description that matches the search query is found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem')
        qs = searches.search_source_traits(description='lorem')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match(self):
        """Trait whose description contains words that begin with the search query is found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem')
        qs = searches.search_source_traits(description='lore')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_matches_beginning_of_word_only(self):
        """Traits whose descriptions contains words that end with the search query are not found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem')
        qs = searches.search_source_traits(description='orem')
        self.assertEqual(qs.count(), 0)

    def test_description_one_word_substring_match_short_search(self):
        """Traits whose description contains words that begin with a (short) search query are found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem')
        qs = searches.search_source_traits(description='lo')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match_short_word(self):
        """Short word with three letters in the description are found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='abc')
        qs = searches.search_source_traits(description='abc')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_exact_match(self):
        """Trait whose description contains words that exactly match multiple search terms is found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_source_traits(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_substring_match(self):
        """Trait whose description contains words that begin with multiple search terms is found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_source_traits(description='lore ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_match_can_be_anywhere(self):
        """Trait when the search query term is not the first word is found."""
        factories.SourceTraitFactory.create(i_description='other trait')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_source_traits(description='ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_finds_only_descriptions_with_all_search_terms(self):
        """Trait whose descriptions contain all words in the search query is found."""
        factories.SourceTraitFactory.create(i_description='lorem other words')
        trait = factories.SourceTraitFactory.create(i_description='lorem ipsum other words')
        qs = searches.search_source_traits(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_matches_search_terms_in_any_order(self):
        """Traits whose descriptions contain all search query words in any order are found."""
        factories.SourceTraitFactory.create(i_description='lorem other words')
        trait_1 = factories.SourceTraitFactory.create(i_description='lorem ipsum other words')
        trait_2 = factories.SourceTraitFactory.create(i_description='ipsum lorem other words')
        qs = searches.search_source_traits(description='ipsum lorem')
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_description_stop_words(self):
        """Trait whose description contains common default stop words is found."""
        # However is a stopword in MySQL by default.
        trait = factories.SourceTraitFactory.create(i_description='however has stop words')
        qs = searches.search_source_traits(description='however')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_is_case_insensitive(self):
        """Traits whose descriptions match search term but with different case are found."""
        trait_1 = factories.SourceTraitFactory.create(i_description='lorem ipsum')
        trait_2 = factories.SourceTraitFactory.create(i_description='LOREM other')
        qs = searches.search_source_traits(description='lorem')
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_description_does_not_match_trait_name_field(self):
        """Traits whose name field matches description query are not found."""
        factories.SourceTraitFactory.create(
            i_trait_name='lorem',
            i_description='other description')
        qs = searches.search_source_traits(description='lorem')
        self.assertEqual(len(qs), 0)

    def test_trait_name_does_not_match_description_field(self):
        """Traits whose description field matches name query are not found."""
        factories.SourceTraitFactory.create(
            i_trait_name='other',
            i_description='lorem')
        qs = searches.search_source_traits(name='lorem')
        self.assertEqual(len(qs), 0)

    def test_description_can_include_a_number(self):
        """Can search for "words" that contain both letters and numbers."""
        trait = factories.SourceTraitFactory.create(i_description='abcd123')
        qs = searches.search_source_traits(description='abcd123')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_can_be_only_numbers(self):
        """Can search for "words" that contain only letters."""
        trait = factories.SourceTraitFactory.create(i_description='123456')
        qs = searches.search_source_traits(description='123456')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_finds_matching_trait_in_one_specified_study(self):
        """Traits only in the requested study are found."""
        factories.StudyFactory.create()
        trait = factories.SourceTraitFactory.create()
        qs = searches.search_source_traits(studies=[trait.source_dataset.source_study_version.study.pk])
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_finds_matching_trait_in_two_specified_studies(self):
        """Traits in two requested studies are found."""
        trait_1 = factories.SourceTraitFactory.create()
        trait_2 = factories.SourceTraitFactory.create()
        studies = [
            trait_1.source_dataset.source_study_version.study.pk,
            trait_2.source_dataset.source_study_version.study.pk,
        ]
        qs = searches.search_source_traits(studies=studies)
        self.assertEqual(qs.count(), 2)
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_finds_only_exact_match_name(self):
        """Trait name must be an exact match."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum')
        factories.SourceTraitFactory.create(i_trait_name='other')
        qs = searches.search_source_traits(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_name_finds_case_insensitive_match(self):
        """Trait name can be case insensitive."""
        trait = factories.SourceTraitFactory.create(i_trait_name='IpSuM')
        factories.SourceTraitFactory.create(i_trait_name='other')
        qs = searches.search_source_traits(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_does_not_find_substring_name_match(self):
        """Substrings of trait names are not matched by default."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_source_traits(name='ipsu')
        self.assertEqual(len(qs), 0)

    def test_finds_name_beginning_with_requested_string_if_specified(self):
        """Substrings of at the beginning of trait names are matched if requested."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_source_traits(name='ipsu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_finds_name_containing_requested_string_if_specified(self):
        """Substrings of trait names are matched if requested."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_source_traits(name='psu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_works_with_both_trait_name_and_description(self):
        """Searching works when trait name and description are both specified."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum', i_description='lorem')
        factories.SourceTraitFactory.create(i_trait_name='ipsum', i_description='other')
        factories.SourceTraitFactory.create(i_trait_name='other', i_description='lorem')
        qs = searches.search_source_traits(name='ipsum', description='lorem')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_works_with_trait_name_description_and_study(self):
        """Searching works when trait name, description, and study are all specified."""
        trait = factories.SourceTraitFactory.create(i_trait_name='ipsum', i_description='lorem')
        factories.SourceTraitFactory.create(i_trait_name='ipsum', i_description='lorem')
        study = trait.source_dataset.source_study_version.study
        qs = searches.search_source_traits(name='ipsum', description='lorem', studies=[study.pk])
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_default_ordering_by_trait(self):
        """Traits are ordered by dataset accession."""
        dataset = factories.SourceDatasetFactory.create()
        trait_1 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=2,
            source_dataset=dataset)
        trait_2 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=1,
            source_dataset=dataset)
        qs = searches.search_source_traits()
        self.assertEqual(list(qs), [trait_2, trait_1])

    def test_default_ordering_by_dataset_and_trait(self):
        """Traits are ordered by dataset accession and then variable accession."""
        dataset_1 = factories.SourceDatasetFactory.create(i_accession=2)
        dataset_2 = factories.SourceDatasetFactory.create(i_accession=1)
        trait_1 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=1,
            source_dataset=dataset_1)
        trait_2 = factories.SourceTraitFactory.create(
            i_dbgap_variable_accession=2,
            source_dataset=dataset_2)
        qs = searches.search_source_traits()
        self.assertEqual(list(qs), [trait_2, trait_1])

    def test_does_not_find_special_characters_in_description(self):
        """Special characters are ignored."""
        characters = ['\'', '%', '#', '<', '>', '=', '?', '-']
        for character in characters:
            description = "special{char}character".format(char=character)
            trait = factories.SourceTraitFactory.create(i_trait_name=description)
            qs = searches.search_source_traits(description=description)
            msg = "found {char}".format(char=character)
            self.assertNotIn(trait, qs, msg=msg)

    def test_does_not_find_harmonized_traits(self):
        """Source trait search function does not find matching harmonized traits."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='lorem')
        self.assertEqual(searches.search_source_traits(name='lorem').count(), 0)

    def test_filters_to_selected_datasets_only(self):
        dataset = factories.SourceDatasetFactory.create()
        traits = factories.SourceTraitFactory.create_batch(5, source_dataset=dataset)
        other_dataset = factories.SourceDatasetFactory.create()
        other_traits = factories.SourceTraitFactory.create_batch(5, source_dataset=other_dataset)
        qs = searches.search_source_traits(datasets=[dataset])
        self.assertEqual(len(qs), len(traits))
        for trait in traits:
            self.assertIn(trait, qs)
        for trait in other_traits:
            self.assertNotIn(trait, qs)


class HarmonizedTraitSearchTest(ClearSearchIndexMixin, TestCase):
    def test_returns_all_traits_with_no_input(self):
        """All traits are returned if nothing is passed to search."""
        traits = factories.HarmonizedTraitFactory.create_batch(10)
        qs = searches.search_harmonized_traits()
        self.assertEqual(qs.count(), models.HarmonizedTrait.objects.current().count())

    def test_does_not_find_deprecated_traits(self):
        """No deprecated traits are returned if nothing is passed to search."""
        trait = factories.HarmonizedTraitFactory.create()
        trait.harmonized_trait_set_version.i_is_deprecated = True
        trait.harmonized_trait_set_version.save()
        qs = searches.search_harmonized_traits()
        self.assertEqual(qs.count(), 0)

    def test_description_no_matches(self):
        """No results are found if the search query doesn't match the trait description."""
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem')
        qs = searches.search_harmonized_traits(description='foobar')
        self.assertQuerysetEqual(qs, [])

    def test_description_one_word_exact_match(self):
        """Only the trait whose description that matches the search query is found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem')
        qs = searches.search_harmonized_traits(description='lorem')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match(self):
        """Trait whose description contains words that begin with the search query is found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem')
        qs = searches.search_harmonized_traits(description='lore')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_matches_beginning_of_word_only(self):
        """Traits whose descriptions contains words that end with the search query are not found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem')
        qs = searches.search_harmonized_traits(description='orem')
        self.assertEqual(qs.count(), 0)

    def test_description_one_word_substring_match_short_search(self):
        """Traits whose description contains words that begin with a (short) search query are found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem')
        qs = searches.search_harmonized_traits(description='lo')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match_short_word(self):
        """Short word with three letters in the description are found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='abc')
        qs = searches.search_harmonized_traits(description='abc')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_exact_match(self):
        """Trait whose description contains words that exactly match multiple search terms is found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_harmonized_traits(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_substring_match(self):
        """Trait whose description contains words that begin with multiple search terms is found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_harmonized_traits(description='lore ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_match_can_be_anywhere(self):
        """Trait when the search query term is not the first word is found."""
        factories.HarmonizedTraitFactory.create(i_description='other trait')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        qs = searches.search_harmonized_traits(description='ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_finds_only_descriptions_with_all_search_terms(self):
        """Trait whose descriptions contain all words in the search query is found."""
        factories.HarmonizedTraitFactory.create(i_description='lorem other words')
        trait = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum other words')
        qs = searches.search_harmonized_traits(description='lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_matches_search_terms_in_any_order(self):
        """Traits whose descriptions contain all search query words in any order are found."""
        factories.HarmonizedTraitFactory.create(i_description='lorem other words')
        trait_1 = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum other words')
        trait_2 = factories.HarmonizedTraitFactory.create(i_description='ipsum lorem other words')
        qs = searches.search_harmonized_traits(description='ipsum lorem')
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_description_stop_words(self):
        """Trait whose description contains common default stop words is found."""
        # However is a stopword in MySQL by default.
        trait = factories.HarmonizedTraitFactory.create(i_description='however has stop words')
        qs = searches.search_harmonized_traits(description='however')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_is_case_insensitive(self):
        """Traits whose descriptions match search term but with different case are found."""
        trait_1 = factories.HarmonizedTraitFactory.create(i_description='lorem ipsum')
        trait_2 = factories.HarmonizedTraitFactory.create(i_description='LOREM other')
        qs = searches.search_harmonized_traits(description='lorem')
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_description_does_not_match_trait_name_field(self):
        """Traits whose name field matches description query are not found."""
        factories.HarmonizedTraitFactory.create(
            i_trait_name='lorem',
            i_description='other description')
        qs = searches.search_harmonized_traits(description='lorem')
        self.assertEqual(len(qs), 0)

    def test_trait_name_does_not_match_description_field(self):
        """Traits whose description field matches name query are not found."""
        factories.HarmonizedTraitFactory.create(
            i_trait_name='other',
            i_description='lorem')
        qs = searches.search_harmonized_traits(name='lorem')
        self.assertEqual(len(qs), 0)

    def test_description_can_include_a_number(self):
        """Can search for "words" that contain both letters and numbers."""
        trait = factories.HarmonizedTraitFactory.create(i_description='abcd123')
        qs = searches.search_harmonized_traits(description='abcd123')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_can_be_only_numbers(self):
        """Can search for "words" that contain only letters."""
        trait = factories.HarmonizedTraitFactory.create(i_description='123456')
        qs = searches.search_harmonized_traits(description='123456')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_finds_only_exact_match_name(self):
        """Trait name must be an exact match."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='ipsum')
        factories.HarmonizedTraitFactory.create(i_trait_name='other')
        qs = searches.search_harmonized_traits(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_name_finds_case_insensitive_match(self):
        """Trait name can be case insensitive."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='IpSuM')
        factories.HarmonizedTraitFactory.create(i_trait_name='other')
        qs = searches.search_harmonized_traits(name='ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_does_not_find_substring_name_match(self):
        """Substrings of trait names are not matched by default."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_harmonized_traits(name='ipsu')
        self.assertEqual(len(qs), 0)

    def test_finds_name_beginning_with_requested_string_if_specified(self):
        """Substrings of at the beginning of trait names are matched if requested."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_harmonized_traits(name='ipsu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_finds_name_containing_requested_string_if_specified(self):
        """Substrings of trait names are matched if requested."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='ipsum')
        qs = searches.search_harmonized_traits(name='psu', match_exact_name=False)
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_works_with_both_trait_name_and_description(self):
        """Searching works when trait name and description are both specified."""
        trait = factories.HarmonizedTraitFactory.create(i_trait_name='ipsum', i_description='lorem')
        factories.HarmonizedTraitFactory.create(i_trait_name='ipsum', i_description='other')
        factories.HarmonizedTraitFactory.create(i_trait_name='other', i_description='lorem')
        qs = searches.search_harmonized_traits(name='ipsum', description='lorem')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_default_ordering(self):
        """Traits are ordered by dataset accession."""
        trait_set_1 = factories.HarmonizedTraitSetFactory.create(i_id=2)
        trait_set_2 = factories.HarmonizedTraitSetFactory.create(i_id=1)
        trait_set_version_1 = factories.HarmonizedTraitSetVersionFactory.create(
            harmonized_trait_set=trait_set_1
        )
        trait_set_version_2 = factories.HarmonizedTraitSetVersionFactory.create(
            harmonized_trait_set=trait_set_2
        )
        trait_1 = factories.HarmonizedTraitFactory.create(
            i_trait_id=1,
            harmonized_trait_set_version=trait_set_version_1
        )
        trait_2 = factories.HarmonizedTraitFactory.create(
            i_trait_id=2,
            harmonized_trait_set_version=trait_set_version_2
        )
        qs = searches.search_harmonized_traits()
        self.assertEqual(list(qs), [trait_2, trait_1])

    def test_does_not_find_special_characters_in_description(self):
        """Special characters are ignored."""
        characters = ['\'', '%', '#', '<', '>', '=', '?', '-']
        for character in characters:
            description = "special{char}character".format(char=character)
            trait = factories.HarmonizedTraitFactory.create(i_trait_name=description)
            qs = searches.search_harmonized_traits(description=description)
            msg = "found {char}".format(char=character)
            self.assertNotIn(trait, qs, msg=msg)

    def test_does_not_find_source_traits(self):
        """Harmonized trait search function does not find matching source traits."""
        trait = factories.SourceTraitFactory.create(i_trait_name='lorem')
        self.assertEqual(searches.search_harmonized_traits(name='lorem').count(), 0)
