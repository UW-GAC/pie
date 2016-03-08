"""Test the classes and functions in the populate_source_traits management command.

This test module won't run with the usual Django test command, because it's
in an unusual location. Instead, you must specify the path containing this
test module to get these tests to run.

Usage:
./manage.py test trait_browser/management/commands

This test module runs several unit tests and one integration test.
"""

from datetime import datetime

import mysql.connector
from django.test import TestCase
from django.utils import timezone

from trait_browser.management.commands.populate_source_traits import Command
from trait_browser.management.commands.db_factory import fake_row_dict
from trait_browser.models import Study, SourceTrait, SourceEncodedValue
from trait_browser.factories import StudyFactory, SourceTraitFactory


class PopulateSourceTraitsTestCase(TestCase):
    
    def test_populate(self):
        self.assertTrue(True)
        

class GetDbTestCase(TestCase):
    
    def test_get_snuffles_db_returns_connection(self):
        """Ensure that _get_snuffles returns a connector.connection object."""
        cmd = Command()
        db = cmd._get_snuffles(test=True)
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
    
    def test_get_snuffles_db_on_server(self):
        # TODO: Figure out a way to test that this works specifically on a server.
        pass
    
    def test_get_snuffles_db_on_workstation(self):
        # TODO: Figure out a way to test that this works specifically on a workstation.
        pass


class DbFixersTestCase(TestCase):

    def test_fix_bytearray_no_bytearrays_left(self):
        """Test that bytearrays from the row_dict are converted to strings."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        for k in fixed_row:
            self.assertNotIsInstance(fixed_row[k], bytearray)
    
    def test_fix_bytearray_only_bytearrays_altered(self):
        """Ensure that the non-bytearray values from the row_dict are not altered by _fix_bytearray."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])

    def test_fix_bytearray_to_string(self):
        """Ensure that the bytearray values from the row_dict are converted to string type."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in bytearray_keys:
            self.assertIsInstance(fixed_row[k], str)
        
    def test_fix_bytearray_empty_bytearray(self):
        """Ensure that the _fix_bytearray function works on an empty bytearray."""
        row = {'empty_bytearray': bytearray('', 'utf-8')}
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        self.assertEqual(fixed_row['empty_bytearray'], '')
    
    def test_fix_bytearray_non_utf8(self):
        """Ensure that _fix_bytearray works on a bytearray with a different encoding that utf-8."""
        row = {'ascii_bytearray': bytearray('foobar', 'ascii')}
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        self.assertEqual(fixed_row['ascii_bytearray'], 'foobar')
    
    def test_fix_bytearray_empty_dict(self):
        """Ensure that _fix_bytearray works on an empty dictionary."""
        row = {}
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        self.assertDictEqual(fixed_row, {})
    
    def test_fix_bytearray_no_bytearrays(self):
        """Ensure that the row_dict is unchanged when _fix_bytearray is given a dict with no bytearrays in it."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        cmd = Command()
        fixed_row = cmd._fix_bytearray(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_no_none_left(self):
        """Ensure that None is completely removed by _fix_null."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_null(row)
        for k in fixed_row:
            self.assertIsNotNone(fixed_row[k])
    
    def test_fix_null_only_none_altered(self):
        """Ensure that only dict values of None are altered."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_null_to_empty_string(self):
        """Ensure that the dict values of None are changed to empty strings."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in none_keys:
            self.assertEqual(fixed_row[k], '')
    
    def test_fix_null_no_nones(self):
        """Ensure that a dict containing no Nones is unchanged by _fix_null."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        cmd = Command()
        fixed_row = cmd._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_empty_dict(self):
        """Ensure that an empty dict is unchanged by _fix_null."""
        row = {}
        cmd = Command()
        fixed_row = cmd._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_timezone_result_is_aware(self):
        """Ensure that the resulting datetimes from _fix_timezone are in fact timezone aware."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(fixed_row[k].tzinfo is not None and
                                fixed_row[k].tzinfo.utcoffset(fixed_row[k]) is not None)
    
    def test_fix_timezone_only_datetimes_altered(self):
        """Ensure that non-datetime objects in the dict are not altered by _fix_timezone."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_timezone(row)
        for k in row:
            if not isinstance(row[k], datetime):
                self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_timezone_still_datetime(self):
        """Ensure that datetime objects in the dict are still of datetime type after conversion by _fix_timezone."""
        row = fake_row_dict()
        cmd = Command()
        fixed_row = cmd._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(isinstance(fixed_row[k], datetime))
    
    def test_fix_timezone_empty_dict(self):
        """Ensure that _fix_timezone works properly (doesn't alter) an empt dictionary input."""
        row = {}
        cmd = Command()
        fixed_row = cmd._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)
    
    def test_fix_timezone_no_datetimes(self):
        """Ensure that a dict containing no datetime objects is unaltered by _fix_timezone."""
        row = {
            'a':1,
            'b':'foobar',
            'c':1.56,
            'd': None,
            'e':bytearray('foobar', 'utf-8')
        }
        cmd = Command()
        fixed_row = cmd._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)
    

class MakeArgsTestCase(TestCase):
    
    def test_make_study_args_one_row_make_study_obj(self):
        """Get a single row of test data from the database and see if the results from _make_study_args can be used to successfully make and save a Study object."""
        cmd = Command()
        source_db = cmd._get_snuffles(test=True)
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_query = 'SELECT * FROM study;'
        cursor.execute(study_query)
        row_dict = cursor.fetchone()
        study_args = cmd._make_study_args(cmd._fix_null(cmd._fix_bytearray(row_dict)))
        study = Study(**study_args)
        study.save()
        self.assertIn(study, Study.objects.all())
        cursor.close()
        source_db.close()
        
    def test_make_source_trait_args_one_row_make_source_trait_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_trait_args can be used to successfully make and save a SourceTrait object."""
        cmd = Command()
        source_db = cmd._get_snuffles(test=True)
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_variable_metadata LIMIT 1;'
        cursor.execute(trait_query)
        row_dict = cursor.fetchone()
        row_dict = cmd._fix_null(cmd._fix_bytearray(row_dict))
        # Have to make a Study object first
        study = Study(
            study_id=row_dict['study_id'],
            dbgap_id='phs000001',
            name='Any Study'
        )
        study.save()
        source_trait_args = cmd._make_source_trait_args(row_dict)
        trait = SourceTrait(**source_trait_args)
        trait.save()
        self.assertIn(trait, SourceTrait.objects.all())
        cursor.close()
        source_db.close()

    def test_make_source_encoded_value_args_one_row_make_source_encoded_value_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_encoded_value_args can be used to successfully make and save a SourceEncodedValue object."""
        cmd = Command()
        source_db = cmd._get_snuffles(test=True)
        cursor = source_db.cursor(buffered=True, dictionary=True)
        value_query = 'SELECT * FROM source_encoded_values LIMIT 1;'
        cursor.execute(value_query)
        row_dict = cursor.fetchone()
        row_dict = cmd._fix_null(cmd._fix_bytearray(row_dict))
        # Have to make Study and SourceTrait objects first
        study = Study(
            study_id=1,
            dbgap_id='phs000001',
            name='Any Study'
        )
        study.save()
        trait = SourceTrait(
            dcc_trait_id=row_dict['source_trait_id'],
            name='a_name',
            description='some interesting trait',
            data_type='encoded',
            unit='',
            study=study,
            phs_string='phs000001',
            phv_string='phv00000001'
        )
        trait.save()
        value_args = cmd._make_source_encoded_value_args(row_dict)
        value = SourceEncodedValue(**value_args)
        value.save()
        self.assertIn(value, SourceEncodedValue.objects.all())
        cursor.close()
        source_db.close()

class GetCurrentListsTest(TestCase):
    
    def test_get_current_studies(self):
        """Test that Command._get_current_studies() returns the right number of study ids."""
        n = 32
        StudyFactory.create_batch(n)
        cmd = Command()
        current_studies = cmd._get_current_studies()
        self.assertEqual(len(current_studies), n)
    
    def test_get_current_traits(self):
        """Test that Command._get_current_traits() returns the right number of trait ids."""
        n = 32
        SourceTraitFactory.create_batch(n)
        cmd = Command()
        current_traits = cmd._get_current_traits()
        self.assertEqual(len(current_traits), n)

class IntegrationTest(TestCase):
    """Integration test of the whole management command.
    
    It's very difficult to test just one function at a time here, because of
    all the inter-object relationships and the data being pulled from the
    source database. So just run one big integration test here rather than
    nice unit tests.
    """
    
    def test_everything(self):
        """Ensure that the whole workflow of the management command works to add objects to the website databse, without limits."""
        # The test database should be a small size for this test to work well.
        cmd = Command()
        source_db = cmd._get_snuffles(test=True)
        # Test that adding studies works, and results in right number of studies.
        cmd._populate_studies(source_db, None)
        cursor = source_db.cursor()
        study_query = 'SELECT COUNT(*) FROM study;'
        cursor.execute(study_query)
        study_count = cursor.fetchone()[0]
        self.assertEqual(study_count, Study.objects.count())
        # Test that adding SourceTraits works, and results in right number of traits.
        cmd._populate_source_traits(source_db, None)
        trait_query = 'SELECT COUNT(*) FROM source_variable_metadata'
        cursor.execute(trait_query)
        trait_count = cursor.fetchone()[0]
        self.assertEqual(trait_count, SourceTrait.objects.count())
        # Test that adding SourceEncodedValues works, and results in right number of encodedvalues.
        cmd._populate_encoded_values(source_db)
        value_query = 'SELECT COUNT(*) FROM source_encoded_values'
        cursor.execute(value_query)
        value_count = cursor.fetchone()[0]
        self.assertEqual(value_count, SourceEncodedValue.objects.count())
        source_db.close()
    
    def test_limits(self):
        """Ensure that the management command workflow functions properly with n_studies and n_traits limits."""
        cmd = Command()
        source_db = cmd._get_snuffles(test=True)
        # Test that adding studies works, and results in right number of studies.
        n_studies = '2'
        cmd._populate_studies(source_db, n_studies)
        cursor = source_db.cursor()
        study_query = 'SELECT COUNT(*) FROM study;'
        cursor.execute(study_query)
        study_count = cursor.fetchone()[0]
        # Make sure the number of studies added is either n_studies or number of studies in the db.
        n_studies = int(n_studies)
        if study_count < n_studies:
            self.assertEqual(study_count, Study.objects.count())
        else:
            self.assertEqual(n_studies, Study.objects.count())
        # Test that adding SourceTraits works, and results in right number of traits.
        n_traits = '25'
        cmd._populate_source_traits(source_db, n_traits)
        studies_in_db = cmd._get_current_studies()
        trait_query = 'SELECT COUNT(*) FROM source_variable_metadata WHERE study_id IN ({})'.format(','.join(studies_in_db))
        cursor.execute(trait_query)
        trait_count = cursor.fetchone()[0]
        n_traits = int(n_traits)
        total_traits = n_studies * n_traits
        if trait_count < total_traits:
            self.assertEqual(trait_count, SourceTrait.objects.count())
        else:
            self.assertEqual(total_traits, SourceTrait.objects.count())
        # Test that adding SourceEncodedValues works, and results in right number of encodedvalues.
        cmd._populate_encoded_values(source_db)
        traits_in_db = cmd._get_current_traits()
        value_query = 'SELECT COUNT(*) FROM source_encoded_values WHERE source_trait_id IN ({})'.format(','.join(traits_in_db))
        cursor.execute(value_query)
        value_count = cursor.fetchone()[0]
        self.assertEqual(value_count, SourceEncodedValue.objects.count())
        source_db.close()
