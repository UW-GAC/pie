"""Test the functions in searches.py."""

from django.test import TestCase

from watson.models import SearchEntry

from . import models
from . import factories
from . import searches


class SourceTraitSearchTest(TestCase):

    def tearDown(self):
        super(SourceTraitSearchTest, self).tearDown()
        # Delete the search index records. Normally, django runs the TestCase
        # tests in a transaction, but this doesn't work for the watson search
        # records because they are stored in a MyISAM table, which doesn't use
        # transactions.
        SearchEntry.objects.all().delete()

    def test_works_with_no_traits(self):
        """Tests that the search function works even if there are no source traits."""
        qs = searches.source_trait_search('lorem')
        self.assertQuerysetEqual(qs, [])

    def test_description_no_matches(self):
        """Tests that no results are found if the search query doesn't match the trait description."""
        trait = factories.SourceTraitFactory(i_description='lorem')
        qs = searches.source_trait_search('foobar')
        self.assertQuerysetEqual(qs, [])

    def test_description_one_word_exact_match(self):
        """Tests that only a trait description that matches the search query is found."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem')
        qs = searches.source_trait_search('lorem')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match(self):
        """Tests that traits with a description whose words begin with the search query are found."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem')
        qs = searches.source_trait_search('lore')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match_short_search(self):
        """Tests that traits with a description whose words begin with a (short) search query are found."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem')
        qs = searches.source_trait_search('lo')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_one_word_substring_match_short_word(self):
        """Tests that a short word in the description can be found."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='abc')
        qs = searches.source_trait_search('abc')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_exact_match(self):
        """Tests that a trait is found from a search query containing multiple exact matches."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem ipsum')
        qs = searches.source_trait_search('lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_multiple_words_substring_match(self):
        """Tests that a trait is found from a search query containing multiple substring matches."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem ipsum')
        qs = searches.source_trait_search('lore ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_match_can_be_anywhere(self):
        """Tests that a trait is found when the search query term is not the first word."""
        factories.SourceTraitFactory(i_description='other trait')
        trait = factories.SourceTraitFactory(i_description='lorem ipsum')
        qs = searches.source_trait_search('ipsu')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_finds_only_descriptions_with_all_search_terms(self):
        """Tests that only traits whose descriptions contain all words in the search query are found."""
        factories.SourceTraitFactory(i_description='lorem other words')
        trait = factories.SourceTraitFactory(i_description='lorem ipsum other words')
        qs = searches.source_trait_search('lorem ipsum')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_stop_words(self):
        """Tests that traits whose descriptions contain common default stop words are found."""
        # However is a stopword in MySQL by default.
        trait = factories.SourceTraitFactory(i_description='however has stop words')
        qs = searches.source_trait_search('however')
        self.assertQuerysetEqual(qs, [repr(trait)])

    def test_description_is_case_insensitive(self):
        """Tests that the search is case insensitive."""
        trait_1 = factories.SourceTraitFactory(i_description='lorem ipsum')
        trait_2 = factories.SourceTraitFactory(i_description='LOREM other')
        qs = searches.source_trait_search('lorem')
        self.assertIn(trait_1, qs)
        self.assertIn(trait_2, qs)

    def test_does_not_find_deprecated_traits(self):
        """Tests that the search does not found deprecated traits even if the description matches.."""
        trait_1 = factories.SourceTraitFactory(i_description='lorem ipsum')
        trait_1.source_dataset.source_study_version.i_is_deprecated = True
        trait_1.source_dataset.source_study_version.save()
        qs = searches.source_trait_search('lorem')
        self.assertEqual(len(qs), 0)
