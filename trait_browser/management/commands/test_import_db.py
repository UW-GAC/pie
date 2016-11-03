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
from django.core import management
from django.test import TestCase
from django.utils import timezone

from trait_browser.management.commands.import_db import Command
from trait_browser.management.commands.db_factory import fake_row_dict
from trait_browser.factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory
from trait_browser.models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class CommandTestCase(TestCase):
    """Superclass to test things using the management command from import_db."""
    
    def setUp(self):
        self.cmd = Command()
        self.source_db = self.cmd._get_source_db(which_db='test')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
    
    def tearDown(self):
        self.cursor.close()
        self.source_db.close()


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
        """Ensure that _fix_timezone works properly on (doesn't alter) an empty dictionary input."""
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
    

class GetDbTestCase(TestCase):
    
    def test_get_source_db_returns_connection_test(self):
        """Ensure that _get_source_db returns a connector.connection object from the test db."""
        cmd = Command()
        db = cmd._get_source_db(which_db='test')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()
    
    def test_get_source_db_returns_connection_production(self):
        """Ensure that _get_source_db returns a connector.connection object from the production db."""
        # TODO: make sure this works after Robert finished setting up the new topmed db on hippocras.
        cmd = Command()
        db = cmd._get_source_db(which_db='production')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()

    def test_get_source_db_returns_connection_devel(self):
        """Ensure that _get_source_db returns a connector.connection object from the devel db."""
        cmd = Command()
        db = cmd._get_source_db(which_db='devel')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()


class MakeArgsTestCase(CommandTestCase):
    
    def test_make_global_study_args_one_row_make_global_study_obj(self):
        """Get a single row of test data from the database and see if the results from _make_global_study_args can be used to successfully make and save a Global_study object."""
        global_study_query = 'SELECT * FROM global_study;'
        self.cursor.execute(global_study_query)
        row_dict = self.cursor.fetchone()
        global_study_args = self.cmd._make_global_study_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        global_study = GlobalStudy(**global_study_args)
        global_study.save()
        self.assertIsInstance(global_study, GlobalStudy)

    def test_make_study_args_one_row_make_study_obj(self):
        """Get a single row of test data from the database and see if the results from _make_study_args can be used to successfully make and save a Study object."""
        study_query = 'SELECT * FROM study;'
        self.cursor.execute(study_query)
        row_dict = self.cursor.fetchone()
        # Have to make a GlobalStudy first.
        global_study = GlobalStudyFactory.create(i_id=row_dict['global_study_id'])
        #
        study_args = self.cmd._make_study_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        study = Study(**study_args)
        study.save()
        self.assertIsInstance(study, Study)

    def test_make_source_study_version_args_one_row_make_source_study_version_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_study_version_args can be used to successfully make and save a SourceStudyVersion object."""
        source_study_version_query = 'SELECT * FROM source_study_version;'
        self.cursor.execute(source_study_version_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study and study first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=row_dict['accession'], global_study=global_study)
        #
        source_study_version_args = self.cmd._make_source_study_version_args(self.cmd._fix_row(row_dict))
        source_study_version = SourceStudyVersion(**source_study_version_args)
        source_study_version.save()
        self.assertIsInstance(source_study_version, SourceStudyVersion)
        
    def test_make_source_dataset_args_one_row_make_source_dataset_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_dataset_args can be used to successfully make and save a SourceDataset object."""
        source_dataset_query = 'SELECT * FROM source_dataset;'
        self.cursor.execute(source_dataset_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, and source_study_version first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = SourceStudyVersionFactory.create(i_id=row_dict['study_version_id'], study=study)
        source_dataset_args = self.cmd._make_source_dataset_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        # 
        source_dataset = SourceDataset(**source_dataset_args)
        source_dataset.save()
        self.assertIsInstance(source_dataset, SourceDataset)

    def test_make_source_trait_args_one_row_make_source_trait_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_trait_args can be used to successfully make and save a SourceTrait object."""
        source_trait_query = 'SELECT * FROM source_trait;'
        self.cursor.execute(source_trait_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, source_study_version, and source_dataset first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = SourceStudyVersionFactory.create(i_id=1, study=study)
        source_dataset = SourceDatasetFactory.create(i_id=row_dict['dataset_id'], source_study_version=source_study_version)
        # 
        source_trait_args = self.cmd._make_source_trait_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        source_trait = SourceTrait(**source_trait_args)
        source_trait.save()
        self.assertIsInstance(source_trait, SourceTrait)

    def test_make_subcohort_args_one_row_make_subcohort_obj(self):
        """Get a single row of test data from the database and see if the results from _make_subcohort_args can be used to successfully make and save a Subcohort object."""
        subcohort_query = 'SELECT * FROM subcohort;'
        self.cursor.execute(subcohort_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study and study first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=row_dict['study_accession'], global_study=global_study)
        #
        subcohort_args = self.cmd._make_subcohort_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        subcohort = Subcohort(**subcohort_args)
        subcohort.save()
        self.assertIsInstance(subcohort, Subcohort)
        
    def test_make_source_trait_encoded_value_args_one_row_make_source_trait_encoded_value_obj(self):
        """Get a single row of test data from the database and see if the results from _make_source_trait_encoded_value_args can be used to successfully make and save a SourceTraitEncodedValue object."""
        source_trait_encoded_value_query = 'SELECT * FROM source_trait_encoded_values;'
        self.cursor.execute(source_trait_encoded_value_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, source_study_version, source_dataset, and source_trait first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = SourceStudyVersionFactory.create(i_id=1, study=study)
        source_dataset = SourceDatasetFactory.create(i_id=1, source_study_version=source_study_version)
        source_trait = SourceTraitFactory.create(i_trait_id=row_dict['source_trait_id'], source_dataset=source_dataset)
        # 
        source_trait_encoded_value_args = self.cmd._make_source_trait_encoded_value_args(self.cmd._fix_null(self.cmd._fix_bytearray(row_dict)))
        source_trait_encoded_value = SourceTraitEncodedValue(**source_trait_encoded_value_args)
        source_trait_encoded_value.save()
        self.assertIsInstance(source_trait_encoded_value, SourceTraitEncodedValue)


class HelperTestCase(CommandTestCase):
    
    def test_make_model_object_from_args(self):
        """Test that """
        self.cmd._make_model_object_from_args(args={'i_id':5, 'i_name':'global study name'},
                                              model=GlobalStudy,
                                              verbosity=0)
        obj = GlobalStudy.objects.get(pk=5)
        self.assertIsInstance(obj, GlobalStudy)
        

class GetCurrentListsTest(CommandTestCase):
    n = 32
    
    def test_get_current_global_studies(self):
        """Test that Command._get_global_studies() returns the right number of global_study ids."""
        GlobalStudyFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(GlobalStudy)
        self.assertEqual(len(pks), self.n)

    def test_get_current_studies(self):
        """Test that Command._get_current_studies() returns the right number of study ids."""
        StudyFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(Study)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_study_versions(self):
        """Test that Command._get_current_source_study_versions() returns the right number of trait ids."""
        SourceStudyVersionFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(SourceStudyVersion)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_datasets(self):
        """Test that Command._get_current_source_datasets() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)
    
    def test_get_current_source_traits(self):
        """Test that Command._get_current_source_traits() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)

    def test_get_current_subcohorts(self):
        """Test that Command._get_current_subcohorts() returns the right number of trait ids."""
        SubcohortFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(Subcohort)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_trait_encoded_values(self):
        """Test that Command._get_current_source_trait_encoded_values() returns the right number of trait ids."""
        SourceTraitEncodedValueFactory.create_batch(self.n)
        pks = self.cmd._get_current_pks(SourceTraitEncodedValue)
        self.assertEqual(len(pks), self.n)


class IntegrationTest(CommandTestCase):
    """Integration test of the whole management command.
    
    It's very difficult to test just one function at a time here, because of
    all the inter-object relationships and the data being pulled from the
    source database. So just run one big integration test here rather than
    nice unit tests.
    """
    
    def test_import_new_methods_after_partial_db_import(self):
        """Ensure that the whole workflow of the management command works to add objects to the website databse, without limits."""
        pass

    def test_call_command_to_import_whole_db(self):
        """Ensure that calling the command as you would from command line works properly."""
        management.call_command('import_db')
        global_studies_query = 'SELECT COUNT(*) FROM global_study;'
        self.cursor.execute(global_studies_query)
        global_studies_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(global_studies_count, GlobalStudy.objects.count())

        studies_query = 'SELECT COUNT(*) FROM study;'
        self.cursor.execute(studies_query)
        studies_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(studies_count, Study.objects.count())

        source_study_versions_query = 'SELECT COUNT(*) FROM source_study_version;'
        self.cursor.execute(source_study_versions_query)
        source_study_versions_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_study_versions_count, SourceStudyVersion.objects.count())

        source_datasets_query = 'SELECT COUNT(*) FROM source_dataset;'
        self.cursor.execute(source_datasets_query)
        source_datasets_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_datasets_count, SourceDataset.objects.count())

        source_traits_query = 'SELECT COUNT(*) FROM source_trait;'
        self.cursor.execute(source_traits_query)
        source_traits_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_traits_count, SourceTrait.objects.count())

        subcohorts_query = 'SELECT COUNT(*) FROM subcohort;'
        self.cursor.execute(subcohorts_query)
        subcohorts_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(subcohorts_count, Subcohort.objects.count())

        subcohorts_query = 'SELECT COUNT(*),dataset_id FROM source_dataset_subcohorts GROUP BY dataset_id;'
        self.cursor.execute(subcohorts_query)
        for row in self.cursor:
            row = self.cmd._fix_row(row)
            django_count = SourceDataset.objects.get(pk=row['dataset_id']).subcohorts.count()
            self.assertEqual(row['COUNT(*)'], django_count)

        source_trait_encoded_values_query = 'SELECT COUNT(*) FROM source_trait_encoded_values;'
        self.cursor.execute(source_trait_encoded_values_query)
        source_trait_encoded_values_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_trait_encoded_values_count, SourceTraitEncodedValue.objects.count())