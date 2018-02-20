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
        pass

    def test_description_no_matches(self):
        pass

    def test_description_one_word_exact_match(self):
        pass

    def test_description_one_word_substring_match(self):
        pass

    def test_description_one_word_substring_match_short_search(self):
        pass

    def test_description_one_word_substring_match_short_word(self):
        pass

    def test_description_multiple_words_exact_match(self):
        pass

    def test_description_multiple_words_substring_match(self):
        pass

    def test_description_match_can_be_anywhere(self):
        pass

    def test_description_ranks_multiple_word_match_over_one_word_match(self):
        pass

    def test_description_stop_words(self):
        pass

    def test_description_is_case_insensitive(self):
        pass

    def test_does_not_find_deprecated_traits(self):
        pass
