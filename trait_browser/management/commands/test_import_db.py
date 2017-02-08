"""Test the classes and functions in the populate_source_traits management command.

This test module won't run with the usual Django test command, because it's
in an unusual location. Instead, you must specify the path containing this
test module to get these tests to run.

Usage:
./manage.py test trait_browser/management/commands

This test module runs several unit tests and one integration test.
"""

from datetime import datetime, timedelta
from os.path import join
from os import remove
from subprocess import call

import mysql.connector
# Use the mysql-connector-python-rf package from pypi (advice via this SO post http://stackoverflow.com/q/34168651/2548371)
from django.conf import settings
from django.core import management
from django.test import TestCase
from django.utils import timezone

from trait_browser.management.commands.import_db import Command
from trait_browser.management.commands.db_factory import fake_row_dict
from trait_browser.factories import GlobalStudyFactory, HarmonizedTraitFactory, HarmonizedTraitEncodedValueFactory, HarmonizedTraitSetFactory, SourceDatasetFactory, SourceStudyVersionFactory, SourceTraitFactory, SourceTraitEncodedValueFactory, StudyFactory, SubcohortFactory
from trait_browser.models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort

CMD = Command()

def get_devel_db(permissions='readonly'):
    """Get a connection to the devel source db.
    
    Arguments:
        permissions (str): 'readonly' or 'full'
    
    Returns:
        connection to the MySQL devel db
    """
    return CMD._get_source_db(which_db='devel', permissions=permissions)

def clean_devel_db():
    """Remove all existing data from the devel source db.
    
    For each table in a 'show tables' query, remove all of the data in the table
    by using the truncate command.
    """
    # if verbose: print('Getting source db connection ...')
    source_db = get_devel_db(permissions='full')
    cursor = source_db.cursor(buffered=True, dictionary=False)
    # if verbose: print('Emptying current data from devel source db ...')
    cursor.execute('SHOW TABLES;')
    tables = [el[0].decode('utf-8') for el in cursor.fetchall()]
    tables.remove('schema_changes')
    tables = [el for el in tables if not el.startswith('view_')]
    # Turn off foreign key checks.
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
    # Remove data from each table. 
    for t in tables:
        cursor.execute('TRUNCATE {};'.format(t))
    # Turn foreign key checks back on.
    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
    cursor.close()
    source_db.close()
    
TEST_DATA_DIR = 'trait_browser/source_db_test_data'
def load_test_source_db_data(filename):
    """Load the data from a specific test data set into the devel source db.
    
    Arguments:
        filename (str): name of the .sql mysql dump file, found in TEST_DATA_DIR
    """
    filepath = join(TEST_DATA_DIR, filename)
    # if verbose: print('Loading test data from ' + filepath + ' ...')
    mysql_load = ['mysql', '--defaults-file={}'.format(settings.CNF_PATH),
                 '--defaults-group-suffix=_topmed_pheno_full_devel', '<', filepath]
    return_code = call(' '.join(mysql_load), shell=True, cwd=settings.SITE_ROOT)
    if return_code == 1:
        raise ValueError('MySQL failed to load test data.')
    # else:
    #     if verbose: print('Test data loaded ...')

def change_data_in_table(table_name, update_field, new_value, where_field, where_value):
    """Run an UPDATE command in the devel db using arguments about what to change.
    
    Arguments:
        table_name (str): name of the source db table to UPDATE
        update_field (str): name of the source db field to SET
        new_value (str): new value to set the update_field field to
        where_field (str): field name to use in the WHERE clause of the UPDATE
            command; probably should be the pk field name
        where_value (str): the value of the where_field to set new values for
    """
    source_db = get_devel_db(permissions='full')
    cursor = source_db.cursor(buffered=True)
    update_cmd = "UPDATE {} SET {}='{}' WHERE {}={};".format(table_name, update_field, new_value, where_field, where_value)
    # print(update_cmd)
    cursor.execute(update_cmd)
    source_db.commit()
    cursor.close()
    source_db.close()


class OpenCloseDBMixin(object):
    """Mixin to add setUp and tearDown methods to TestCases.
    
    setUp opens a new db connection and tearDown closes the connection.
    """

    def setUp(self):
        """Get a new source db connection for each test."""
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
    
    def tearDown(self):
        """Close the source db connection at the end of each test."""
        self.cursor.close()
        self.source_db.close()


class TestFunctionsTestCase(TestCase):
    """Tests of the helper functions used by this test script."""
    
    def test_clean_devel_db(self):
        """Test that clean_devel_db() leaves the devel db with 0 rows in each table."""
        load_test_source_db_data('base.sql')
        clean_devel_db()
        source_db = get_devel_db(permissions='full')
        cursor = source_db.cursor(buffered=True, dictionary=False)
        cursor.execute('SHOW TABLES;')
        tables = [el[0].decode('utf-8') for el in cursor.fetchall()]
        tables.remove('schema_changes')
        tables = [el for el in tables if not el.startswith('view_')]
        for tab in tables:
            row_count_query = 'SELECT COUNT(*) FROM {};'.format(tab)
            cursor.execute(row_count_query)
            row_count = cursor.fetchone()[0]
            self.assertEqual(row_count, 0)
        cursor.close()
        source_db.close()
    
    def test_change_data_in_table(self):
        """change_data_in_table successfully makes a change in the devel source db."""
        clean_devel_db()
        load_test_source_db_data('base.sql')
        table = 'global_study'
        update_field = 'name'
        new_val = 'TEST'
        where_field = 'id'
        where_value = 1
        change_data_in_table(table, update_field, new_val, where_field, where_value)
        source_db = get_devel_db()
        cursor = source_db.cursor(buffered=True, dictionary=True)
        cursor.execute('SELECT * FROM {} WHERE {}={};'.format(table, where_field, where_value))
        row = cursor.fetchone()
        row = CMD._fix_row(row)
        cursor.close()
        source_db.close()
        self.assertEqual(row[update_field], new_val)
        clean_devel_db()
    
    def test_load_test_source_db_data(self):
        """Loading a test data set works as expected."""
        # clean the db, load the test data, do a mysqldump to a file, then read in
        # the two dump files, make some adjustments, and then compare the file contents.
        clean_devel_db()
        file_name = 'base.sql'
        test_file = join(TEST_DATA_DIR, file_name)
        load_test_source_db_data(file_name)
        # Parse the name of the devel db out of the mysql conf file.
        with open(settings.CNF_PATH) as f:
            cnf = f.readlines()
        statement_lines = [i for (i, line) in enumerate(cnf) if line.startswith('[')]
        devel_line = [i for (i, line) in enumerate(cnf) if line.startswith('[mysql_topmed_pheno_full_devel]')][0]
        next_statement_line = [i for i in statement_lines if i > devel_line][0]
        devel_lines = [x for x in range(len(cnf)) if (x >= devel_line) and (x < next_statement_line)]
        devel_db_line = [x for x in cnf[min(devel_lines):max(devel_lines)] if x.startswith('database = ')][0]
        devel_db_name = devel_db_line.replace('database = ', '').strip('\n')
        # Make the mysqldump command.
        tmp_file = 'tmp.sql'
        tmp_file_path = join(settings.SITE_ROOT, TEST_DATA_DIR, tmp_file)
        # Now do a mysqldump to the same file.
        mysqldump = ['mysqldump', '--defaults-file={}'.format(settings.CNF_PATH),
                     '--defaults-group-suffix=_topmed_pheno_full_devel', '--opt',
                     devel_db_name, '>', tmp_file]
        return_code = call(' '.join(mysqldump), shell=True, cwd=join(settings.SITE_ROOT, TEST_DATA_DIR))
        if return_code != 0:
            raise ValueError('Something went wrong with the mysqldump command.')
        # Get the file contents to compare.
        with open(test_file, 'r') as f:
            test_file_contents = f.readlines()
        with open(tmp_file_path, 'r') as f:
            tmp_file_contents = f.readlines()
        # Delete lines that are expected to differ between the dump files.
        bad_words = ['DEFINER', 'Distrib', 'Host', 'Dump completed on', 'SET FOREIGN_KEY_CHECKS =']
        for word in bad_words:
            test_file_contents = [l for l in test_file_contents if word not in l]
            tmp_file_contents = [l for l in tmp_file_contents if word not in l]
        # Compare the files and delete the tmp file.
        self.assertEqual(tmp_file_contents, test_file_contents)
        remove(tmp_file_path) 


class BaseTestDataTestCase(OpenCloseDBMixin, TestCase):
    """Superclass to test importing commands on the base.sql test source db data."""
    
    @classmethod
    def setUpClass(cls):
        """Load the base test data, once for all tests."""
        # Run the TestCase setUpClass method.
        super(BaseTestDataTestCase, cls).setUpClass()
        # Clean out the devel db and load the first test dataset.
        # By default, all tests will use dataset 1.
        clean_devel_db()
        load_test_source_db_data('base.sql')


class VisitTestDataTestCase(OpenCloseDBMixin, TestCase):
    """Tests that need visit data to already be added to the source db test data."""
    
    @classmethod
    def setUpClass(cls):
        """Load the base+visit test data once for all of the tests."""
        # Run the TestCase setUpClass method.
        super(VisitTestDataTestCase, cls).setUpClass()
        # Clean out the devel db and load the first test dataset.
        # By default, all tests will use dataset 1.
        clean_devel_db()
        load_test_source_db_data('base_plus_visit.sql')


class VisitTestCase(VisitTestDataTestCase):
    """Tests that require visit data from the get-go."""
    
    def test_make_subcohort_args_one_row_make_subcohort_obj(self):
        """Get a single row of test data from the database and see if the results from _make_subcohort_args can be used to successfully make and save a Subcohort object."""
        subcohort_query = 'SELECT * FROM subcohort;'
        self.cursor.execute(subcohort_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study and study first.
        global_study = GlobalStudyFactory.create(i_id=1)
        study = StudyFactory.create(i_accession=row_dict['study_accession'], global_study=global_study)
        #
        subcohort_args = CMD._make_subcohort_args(CMD._fix_row(row_dict))
        subcohort = Subcohort(**subcohort_args)
        subcohort.save()
        self.assertIsInstance(subcohort, Subcohort)


class DbFixersTestCase(TestCase):
    """Tests of the _fix_[something] methods."""

    def test_fix_bytearray_no_bytearrays_left(self):
        """Bytearrays from the row_dict are converted to strings."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        for k in fixed_row:
            self.assertNotIsInstance(fixed_row[k], bytearray)
    
    def test_fix_bytearray_only_bytearrays_altered(self):
        """The non-bytearray values from the row_dict are not altered by _fix_bytearray."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])

    def test_fix_bytearray_to_string(self):
        """The bytearray values from the row_dict are converted to string type."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in bytearray_keys:
            self.assertIsInstance(fixed_row[k], str)
        
    def test_fix_bytearray_empty_bytearray(self):
        """The _fix_bytearray function works on an empty bytearray."""
        row = {'empty_bytearray': bytearray('', 'utf-8')}
        fixed_row = CMD._fix_bytearray(row)
        self.assertEqual(fixed_row['empty_bytearray'], '')
    
    def test_fix_bytearray_non_utf8(self):
        """_fix_bytearray works on a bytearray with a different encoding that utf-8."""
        row = {'ascii_bytearray': bytearray('foobar', 'ascii')}
        fixed_row = CMD._fix_bytearray(row)
        self.assertEqual(fixed_row['ascii_bytearray'], 'foobar')
    
    def test_fix_bytearray_empty_dict(self):
        """_fix_bytearray works on an empty dictionary."""
        row = {}
        fixed_row = CMD._fix_bytearray(row)
        self.assertDictEqual(fixed_row, {})
    
    def test_fix_bytearray_no_bytearrays(self):
        """The row_dict is unchanged when _fix_bytearray is given a dict with no bytearrays in it."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        fixed_row = CMD._fix_bytearray(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_no_none_left(self):
        """None is completely removed by _fix_null."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        for k in fixed_row:
            self.assertIsNotNone(fixed_row[k])
    
    def test_fix_null_only_none_altered(self):
        """Only dict values of None are altered."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_null_to_empty_string(self):
        """Dict values of None are changed to empty strings."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in none_keys:
            self.assertEqual(fixed_row[k], '')
    
    def test_fix_null_no_nones(self):
        """A dict containing no Nones is unchanged by _fix_null."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        fixed_row = CMD._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_empty_dict(self):
        """An empty dict is unchanged by _fix_null."""
        row = {}
        fixed_row = CMD._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_timezone_result_is_aware(self):
        """The resulting datetimes from _fix_timezone are in fact timezone aware."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(fixed_row[k].tzinfo is not None and
                                fixed_row[k].tzinfo.utcoffset(fixed_row[k]) is not None)
    
    def test_fix_timezone_only_datetimes_altered(self):
        """Non-datetime objects in the dict are not altered by _fix_timezone."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if not isinstance(row[k], datetime):
                self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_timezone_still_datetime(self):
        """Datetime objects in the dict are still of datetime type after conversion by _fix_timezone."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(isinstance(fixed_row[k], datetime))
    
    def test_fix_timezone_empty_dict(self):
        """_fix_timezone works properly on (doesn't alter) an empty dictionary input."""
        row = {}
        fixed_row = CMD._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)
    
    def test_fix_timezone_no_datetimes(self):
        """A dict containing no datetime objects is unaltered by _fix_timezone."""
        row = {
            'a':1,
            'b':'foobar',
            'c':1.56,
            'd': None,
            'e':bytearray('foobar', 'utf-8')
        }
        fixed_row = CMD._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)
    

class GetDbTestCase(TestCase):
    """Tests of the _get_db() utility function."""
    
    def test_get_source_db_returns_connection_test(self):
        """Ensure that _get_source_db returns a connector.connection object from the test db."""
        db = CMD._get_source_db(which_db='test')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()
    
    def test_get_source_db_returns_connection_production(self):
        """Ensure that _get_source_db returns a connector.connection object from the production db."""
        # TODO: make sure this works after Robert finished setting up the new topmed db on hippocras.
        db = CMD._get_source_db(which_db='production')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()

    def test_get_source_db_returns_connection_devel(self):
        """Ensure that _get_source_db returns a connector.connection object from the devel db."""
        db = CMD._get_source_db(which_db='devel')
        self.assertIsInstance(db, mysql.connector.MySQLConnection)
        db.close()
        
    def test_source_db_timezone_is_utc(self):
        """The timezone of the source_db MySQL connection is UTC."""
        db = CMD._get_source_db(which_db='devel')
        cursor = db.cursor()
        cursor.execute("SELECT TIMEDIFF(NOW(), CONVERT_TZ(NOW(), @@session.time_zone, '+00:00'))")
        timezone_offset = cursor.fetchone()[0]
        self.assertEqual(timedelta(0), timezone_offset)


class MakeArgsTestCase(BaseTestDataTestCase):
    """Tests of the _make_[model]_args functions."""
    
    def test_make_global_study_args_one_row_make_global_study_obj(self):
        """Get a single row of test data from the database and see if the results from _make_global_study_args can be used to successfully make and save a Global_study object."""
        global_study_query = 'SELECT * FROM global_study;'
        self.cursor.execute(global_study_query)
        row_dict = self.cursor.fetchone()
        global_study_args = CMD._make_global_study_args(CMD._fix_row(row_dict))
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
        study_args = CMD._make_study_args(CMD._fix_row(row_dict))
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
        source_study_version_args = CMD._make_source_study_version_args(CMD._fix_row(row_dict))
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
        source_dataset_args = CMD._make_source_dataset_args(CMD._fix_row(row_dict))
        # 
        source_dataset = SourceDataset(**source_dataset_args)
        source_dataset.save()
        self.assertIsInstance(source_dataset, SourceDataset)

    def test_make_harmonized_trait_set_args_one_row_make_harmonized_trait_set_obj(self):
        """Get a single row of test data from the database and see if the results from _make_harmonized_trait_set_args can be used to successfully make and save a SourceDataset object."""
        harmonized_trait_set_query = 'SELECT * FROM harmonized_trait_set;'
        self.cursor.execute(harmonized_trait_set_query)
        row_dict = self.cursor.fetchone()
        harmonized_trait_set_args = CMD._make_harmonized_trait_set_args(CMD._fix_row(row_dict))
        # 
        harmonized_trait_set = HarmonizedTraitSet(**harmonized_trait_set_args)
        harmonized_trait_set.save()
        self.assertIsInstance(harmonized_trait_set, HarmonizedTraitSet)

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
        source_trait_args = CMD._make_source_trait_args(CMD._fix_row(row_dict))
        source_trait = SourceTrait(**source_trait_args)
        source_trait.save()
        self.assertIsInstance(source_trait, SourceTrait)

    def test_make_harmonized_trait_args_one_row_make_harmonized_trait_obj(self):
        """Get a single row of test data from the database and see if the results from _make_harmonized_trait_args can be used to successfully make and save a SourceTrait object."""
        harmonized_trait_query = 'SELECT * FROM harmonized_trait;'
        self.cursor.execute(harmonized_trait_query)
        row_dict = self.cursor.fetchone()
        # Have to make harmonized_trait_set first.
        harmonized_trait_set = HarmonizedTraitSetFactory.create(i_id=row_dict['harmonized_trait_set_id'])
        # 
        harmonized_trait_args = CMD._make_harmonized_trait_args(CMD._fix_row(row_dict))
        harmonized_trait = HarmonizedTrait(**harmonized_trait_args)
        harmonized_trait.save()
        self.assertIsInstance(harmonized_trait, HarmonizedTrait)

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
        source_trait_encoded_value_args = CMD._make_source_trait_encoded_value_args(CMD._fix_row(row_dict))
        source_trait_encoded_value = SourceTraitEncodedValue(**source_trait_encoded_value_args)
        source_trait_encoded_value.save()
        self.assertIsInstance(source_trait_encoded_value, SourceTraitEncodedValue)
        
    def test_make_harmonized_trait_encoded_value_args_one_row_make_harmonized_trait_encoded_value_obj(self):
        """Get a single row of test data from the database and see if the results from _make_harmonized_trait_encoded_value_args can be used to successfully make and save a HarmonizedTraitEncodedValue object."""
        # Get a single harmonized_trait_encoded_value from the source db
        harmonized_trait_encoded_value_query = 'SELECT * FROM harmonized_trait_encoded_values;'
        self.cursor.execute(harmonized_trait_encoded_value_query)
        row_dict = self.cursor.fetchone()
        # Get information for the harmonized_trait the encoded value is connected to.
        harmonized_trait_set_query = 'SELECT * FROM harmonized_trait WHERE harmonized_trait_id = {};'.format(row_dict['harmonized_trait_id'])
        self.cursor.execute(harmonized_trait_set_query)
        harmonized_trait_row_dict = self.cursor.fetchone()
        # Make a harmonized_trait and harmonized_trait_set before trying to make the encoded value object.
        harmonized_trait_set = HarmonizedTraitSetFactory.create(i_id=harmonized_trait_row_dict['harmonized_trait_set_id'])
        harmonized_trait = HarmonizedTraitFactory.create(i_trait_id=row_dict['harmonized_trait_id'], harmonized_trait_set=harmonized_trait_set)
        # Make the encoded value object.
        harmonized_trait_encoded_value_args = CMD._make_harmonized_trait_encoded_value_args(CMD._fix_row(row_dict))
        harmonized_trait_encoded_value = HarmonizedTraitEncodedValue(**harmonized_trait_encoded_value_args)
        harmonized_trait_encoded_value.save()
        self.assertIsInstance(harmonized_trait_encoded_value, HarmonizedTraitEncodedValue)


class ImportHelperTestCase(TestCase):
    """Tests of the helper functions from import_db.Command()."""
    
    def test_make_global_study_from_args(self):
        """_make_model_object_from_args works to make a global study."""
        CMD._make_model_object_from_args(args={'i_id':5, 'i_name':'global study name', 'i_date_added': timezone.now(), 'i_date_changed':timezone.now()},
                                              model=GlobalStudy)
        obj = GlobalStudy.objects.get(pk=5)
        self.assertIsInstance(obj, GlobalStudy)
        
    def test_make_table_query(self):
        pass
    
    def test_make_model_object_per_query_row(self):
        pass
    
    def test_make_query_for_new_rows(self):
        pass
        
    def test_make_args_mapping(self):
        pass
    
    def test_import_new_data(self):
        pass
    
    def test_make_query_for_rows_to_update(self):
        pass
    
    def test_update_model_object_from_args(self):
        pass
    
    def test_update_model_object_per_query_row(self):
        pass
    
    def test_update_existing_data(self):
        pass
    

class M2MHelperTestCase(TestCase):
    """Tests of the helper functions for importing and updating m2m tables."""
    
    def test_import_new_m2m_field(self):
        pass
    
    def test_update_m2m_field(self):
        pass
    
    def test_make_m2m_link(self):
        pass

class ImportHelperTestCase(TestCase):
    """Tests of the _import_[source|harmonized]_tables helper methods."""
    
    def test_import_source_tables(self):
        pass
    
    def test_import_harmonized_tables(self):
        pass


class UpdateHelperTestCase(TestCase):
    """Tests of the _update_[source|harmonized]_tables helper methods."""
    
    def test_update_source_tables(self):
        pass
    
    def test_update_harmonized_tables(self):
        pass


class GetCurrentListsTest(TestCase):
    """Tests of _get_current_pks with each possible model."""
    n = 32
    
    def test_get_current_global_studies(self):
        """Test that Command._get_global_studies() returns the right number of global_study ids."""
        GlobalStudyFactory.create_batch(self.n)
        pks = CMD._get_current_pks(GlobalStudy)
        self.assertEqual(len(pks), self.n)

    def test_get_current_studies(self):
        """Test that Command._get_current_studies() returns the right number of study ids."""
        StudyFactory.create_batch(self.n)
        pks = CMD._get_current_pks(Study)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_study_versions(self):
        """Test that Command._get_current_source_study_versions() returns the right number of trait ids."""
        SourceStudyVersionFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceStudyVersion)
        self.assertEqual(len(pks), self.n)

    def test_get_current_subcohorts(self):
        """Test that Command._get_current_subcohorts() returns the right number of trait ids."""
        SubcohortFactory.create_batch(self.n)
        pks = CMD._get_current_pks(Subcohort)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_datasets(self):
        """Test that Command._get_current_source_datasets() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)
    
    def test_get_current_harmonized_trait_set(self):
        pass
    
    def test_get_current_source_traits(self):
        """Test that Command._get_current_source_traits() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)
    
    def test_get_current_harmonized_trait(self):
        pass
    
    def test_get_current_source_trait_encoded_values(self):
        """Test that Command._get_current_source_trait_encoded_values() returns the right number of trait ids."""
        SourceTraitEncodedValueFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTraitEncodedValue)
        self.assertEqual(len(pks), self.n)
    
    def test_get_current_harmonized_trait_encoded_values(self):
        pass


class UpdateModelsTestCase(VisitTestDataTestCase):
    """Tests of the update functions with updates to each possible source_db table."""
    
    # Source trait updates.
    def test_update_global_study(self):
        """Updates in global_study are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = GlobalStudy
        model_instance = model.objects.all()[0]
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)
    
    def test_update_study(self):
        """Updates in study are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = Study
        model_instance = model.objects.all()[0]
        source_db_table_name = 'study'
        field_to_update = 'study_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_source_study_version(self):
        """Updates in source_study_version are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceStudyVersion
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_study_version'
        field_to_update = 'is_deprecated'
        new_value = not getattr(model_instance, 'i_'+field_to_update)
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_source_dataset(self):
        """Updates in source_dataset table are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceDataset
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_dataset'
        field_to_update = 'visit_code'
        new_value = 'one_visit_per_file'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_source_trait(self):
        """Updates in source_trait table are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceTrait
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_trait'
        field_to_update = 'dcc_description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'source_trait_id'
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertTrue(model_instance.modified > t1)

    def test_update_subcohort(self):
        """Updates in subcohort are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = Subcohort
        model_instance = model.objects.all()[0]
        source_db_table_name = 'subcohort'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_source_trait_encoded_value(self):
        """Updates in source_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceTraitEncodedValue
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_source_dataset_subcohorts(self):
        """A new subcohort link to an existing source dataset is imported after an update."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel')
        # Pick a subcohort to create a new link to in the source db.
        subcohorts = Subcohort.objects.all()
        sc = subcohorts[0]
        # Find a dataset which this subcohort isn't linked to already
        linked_datasets = sc.sourcedataset_set.all()
        possible_datasets = SourceDataset.objects.filter(source_study_version__study = sc.study)
        unlinked_datasets = set(possible_datasets) - set(linked_datasets)
        if len(unlinked_datasets) < 1:
            raise ValueError('The subcohort is already linked to all possible datasets.')
        dataset_to_link = list(unlinked_datasets)[0]
        # Create a new dataset-subcohort link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        add_subcohort_link_query = "INSERT INTO source_dataset_subcohorts (dataset_id, subcohort_id, date_added) VALUES ({}, {}, '{}');".format(sc.i_id, dataset_to_link.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_subcohort_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only')
        # Check that the chosen subcohort is now linked to the dataset that was picked, in the Django db.
        sc.refresh_from_db()
        dataset_to_link.refresh_from_db()
        self.assertTrue(dataset_to_link in sc.sourcedataset_set.all())

    # Harmonized trait updates.
    def test_update_harmonized_trait_set(self):
        """Updates to harmonized_trait_set are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTraitSet
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait_set'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_harmonized_trait(self):
        """Updates to harmonized_trait are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTrait
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'harmonized_trait_id'
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertTrue(model_instance.modified > t1)

    def test_update_harmonized_trait_encoded_value(self):
        """Updates to harmonized_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTraitEncodedValue
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertTrue(model_instance.modified > t1)

    def test_update_component_source_traits(self):
        """A new component source trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel')
        # Pick a source trait to create a new link to in the source db.
        source_trait = SourceTrait.objects.get(pk=1)
        # Find a harmonized_trait which this source trait isn't linked to already
        for x in range(1, 100):
            htrait_set = HarmonizedTraitSet.objects.get(pk=x)
            if htrait_set not in source_trait.harmonizedtraitset_set.all():
                break
        # Add source_trait as a component trait of htrait_set in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Have to add a harmonized function here first...
        self.cursor.execute("INSERT INTO harmonized_function (function_definition) values ('return(dataset)');")
        self.source_db.commit()
        add_component_trait_query = "INSERT INTO component_source_trait (harmonized_trait_set_id, harmonized_function_id, component_trait_id, date_added) VALUES ({}, 1, {}, '{}');".format(htrait_set.i_id, source_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only')
        # Check that the chosen subcohort is now linked to the dataset that was picked, in the Django db.
        source_trait.refresh_from_db()
        htrait_set.refresh_from_db()
        self.assertTrue(htrait_set in source_trait.harmonizedtraitset_set.all())


class ImportNoUpdateTestCase(VisitTestDataTestCase):
    """Tests that updated source data is NOT imported when the --import_only flag is used."""
    
    # Source trait updates.
    def test_no_update_on_import_global_study(self):
        """Updates in global_study are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = GlobalStudy
        model_instance = model.objects.all()[0]
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)
    
    def test_no_update_on_import_study(self):
        """Updates in study are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = Study
        model_instance = model.objects.all()[0]
        source_db_table_name = 'study'
        field_to_update = 'study_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_source_study_version(self):
        """Updates in source_study_version are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceStudyVersion
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_study_version'
        field_to_update = 'is_deprecated'
        new_value = not getattr(model_instance, 'i_'+field_to_update)
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_source_dataset(self):
        """Updates in source_dataset are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceDataset
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_dataset'
        field_to_update = 'visit_code'
        new_value = 'one_visit_per_file'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_source_trait(self):
        """Updates in source_trait are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceTrait
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_trait'
        field_to_update = 'dcc_description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'source_trait_id'
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_subcohort(self):
        """Updates in subcohort are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = Subcohort
        model_instance = model.objects.all()[0]
        source_db_table_name = 'subcohort'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_source_trait_encoded_value(self):
        """Updates in source_trait_encoded_values are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = SourceTraitEncodedValue
        model_instance = model.objects.all()[0]
        source_db_table_name = 'source_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_source_dataset_subcohorts(self):
        """Updates in source_dataset_subcohorts are not imported with --import_only."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel')
        # Pick a subcohort to create a new link to in the source db.
        subcohorts = Subcohort.objects.all()
        sc = subcohorts[0]
        # Find a dataset which this subcohort isn't linked to already
        linked_datasets = sc.sourcedataset_set.all()
        possible_datasets = SourceDataset.objects.filter(source_study_version__study = sc.study)
        unlinked_datasets = set(possible_datasets) - set(linked_datasets)
        if len(unlinked_datasets) < 1:
            raise ValueError('The subcohort is already linked to all possible datasets.')
        dataset_to_link = list(unlinked_datasets)[0]
        # Create a new dataset-subcohort link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        add_subcohort_link_query = "INSERT INTO source_dataset_subcohorts (dataset_id, subcohort_id, date_added) VALUES ({}, {}, '{}');".format(sc.i_id, dataset_to_link.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_subcohort_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only')
        # Check that the chosen subcohort is now linked to the dataset that was picked, in the Django db.
        sc.refresh_from_db()
        dataset_to_link.refresh_from_db()
        self.assertFalse(dataset_to_link in sc.sourcedataset_set.all())

    # Harmonized trait updates.
    def test_no_update_on_import_harmonized_trait_set(self):
        """Updates in harmonized_trait_set are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTraitSet
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait_set'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_harmonized_trait(self):
        """Updates in harmonized_trait are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTrait
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'harmonized_trait_id'
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_harmonized_trait_encoded_value(self):
        """Updates in harmonized_trait_encoded_values are not imported with --import_only."""
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        
        model = HarmonizedTraitEncodedValue
        model_instance = model.objects.all()[0]
        source_db_table_name = 'harmonized_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_'+field_to_update))
        self.assertFalse(model_instance.modified > t1)

    def test_no_update_on_import_component_source_traits(self):
        """Updates in component_source_trait are not imported with --import_only."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel')
        # Pick a source trait to create a new link to in the source db.
        source_trait = SourceTrait.objects.get(pk=1)
        # Find a harmonized_trait which this source trait isn't linked to already
        for x in range(1, 100):
            htrait_set = HarmonizedTraitSet.objects.get(pk=x)
            if htrait_set not in source_trait.harmonizedtraitset_set.all():
                break
        # Add source_trait as a component trait of htrait_set in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Have to add a harmonized function here first...
        self.cursor.execute("INSERT INTO harmonized_function (function_definition) values ('return(dataset)');")
        self.source_db.commit()
        add_component_trait_query = "INSERT INTO component_source_trait (harmonized_trait_set_id, harmonized_function_id, component_trait_id, date_added) VALUES ({}, 1, {}, '{}');".format(htrait_set.i_id, source_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only')
        # Check that the chosen subcohort is now linked to the dataset that was picked, in the Django db.
        source_trait.refresh_from_db()
        htrait_set.refresh_from_db()
        self.assertFalse(htrait_set in source_trait.harmonizedtraitset_set.all())


class IntegrationTest(VisitTestDataTestCase):
    """Integration test of the whole management command.
    
    It's very difficult to test just one function at a time here, because of
    all the inter-object relationships and the data being pulled from the
    source database. So just run one big integration test here rather than
    nice unit tests.
    """

    def test_handle_with_visit_data(self):
        """Calling import_db imports the correct number of each model type."""
        management.call_command('import_db', '--which_db=devel')
        # GlobalStudy
        global_studies_query = 'SELECT COUNT(*) FROM global_study;'
        self.cursor.execute(global_studies_query)
        global_studies_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(global_studies_count, GlobalStudy.objects.count())
        # Study
        studies_query = 'SELECT COUNT(*) FROM study;'
        self.cursor.execute(studies_query)
        studies_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(studies_count, Study.objects.count())
        # SourceStudyVersion
        source_study_versions_query = 'SELECT COUNT(*) FROM source_study_version;'
        self.cursor.execute(source_study_versions_query)
        source_study_versions_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_study_versions_count, SourceStudyVersion.objects.count())
        # SourceDataset
        source_datasets_query = 'SELECT COUNT(*) FROM source_dataset;'
        self.cursor.execute(source_datasets_query)
        source_datasets_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_datasets_count, SourceDataset.objects.count())
        # SourceTrait
        source_traits_query = 'SELECT COUNT(*) FROM source_trait;'
        self.cursor.execute(source_traits_query)
        source_traits_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_traits_count, SourceTrait.objects.count())
        #Subcohort
        subcohorts_query = 'SELECT COUNT(*) FROM subcohort;'
        self.cursor.execute(subcohorts_query)
        subcohorts_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(subcohorts_count, Subcohort.objects.count())
        # SourceDataset.subcohorts
        subcohorts_m2m_query = 'SELECT COUNT(*),dataset_id FROM source_dataset_subcohorts GROUP BY dataset_id;'
        self.cursor.execute(subcohorts_m2m_query)
        for row in self.cursor:
            row = CMD._fix_row(row)
            django_count = SourceDataset.objects.get(pk=row['dataset_id']).subcohorts.count()
            self.assertEqual(row['COUNT(*)'], django_count)
        # SourceTraitEncodedValue
        source_trait_encoded_values_query = 'SELECT COUNT(*) FROM source_trait_encoded_values;'
        self.cursor.execute(source_trait_encoded_values_query)
        source_trait_encoded_values_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_trait_encoded_values_count, SourceTraitEncodedValue.objects.count())
        # TODO: Add tests for harmonized tables, especially m2m tables.

    def test_handle_with_updated_data(self):
        """Every kind of update is detected and imported by import_db."""
        # This test is largely just all of the methods from UpdateModelsTestCase all put together.
        # Initial call of the import command.
        management.call_command('import_db', '--which_db=devel')
        t1 = timezone.now() # Save a time to compare to modified date.
        new_value = 'asdfghjkl' # Use this value to reset things in multiple models.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        # Update the global study table.
        global_study = GlobalStudy.objects.all()[0]
        change_data_in_table('global_study', 'name', new_value, global_study._meta.pk.name.replace('i_', ''), global_study.pk)
        # Update the study table.
        study = Study.objects.all()[0]
        change_data_in_table('study', 'study_name', new_value, study._meta.pk.name.replace('i_', ''), study.pk)
        # Update the source study version table.
        source_study_version = SourceStudyVersion.objects.all()[0]
        new_is_deprecated = not source_study_version.i_is_deprecated
        change_data_in_table('source_study_version', 'is_deprecated', new_is_deprecated, source_study_version._meta.pk.name.replace('i_', ''), source_study_version.pk)
        # Update source dataset table.
        source_dataset = SourceDataset.objects.all()[0]
        new_visit_code = 'one_visit_per_file'
        change_data_in_table('source_dataset', 'visit_code', new_visit_code, source_dataset._meta.pk.name.replace('i_', ''), source_dataset.pk)
        # Update source trait table.
        source_trait = SourceTrait.objects.all()[0]
        change_data_in_table('source_trait', 'dcc_description', new_value, 'source_trait_id', source_trait.pk)
        # Update the subcohort table.
        subcohort = Subcohort.objects.all()[0]
        change_data_in_table('subcohort', 'name', new_value, subcohort._meta.pk.name.replace('i_', ''), subcohort.pk)
        # Update source trait encoded values table.
        sev = SourceTraitEncodedValue.objects.all()[0]
        change_data_in_table('source_trait_encoded_values', 'value', new_value, sev._meta.pk.name.replace('i_', ''), sev.pk)
        # Update harmonized trait set table.
        harmonized_trait_set = HarmonizedTraitSet.objects.all()[0]
        change_data_in_table('harmonized_trait_set', 'description', new_value, harmonized_trait_set._meta.pk.name.replace('i_', ''), harmonized_trait_set.pk)
        # Update harmonized trait table.
        harmonized_trait = HarmonizedTrait.objects.all()[0]
        change_data_in_table('harmonized_trait', 'description', new_value, 'harmonized_trait_id', harmonized_trait.pk)
        # Update harmonized trait encoded values table.
        hev = HarmonizedTraitEncodedValue.objects.all()[0]
        change_data_in_table('harmonized_trait_encoded_values', 'value', new_value, hev._meta.pk.name.replace('i_', ''), hev.pk)
        
        # Prep for doing updates for m2m tables.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Find a dataset which this subcohort isn't linked to already
        linked_datasets = subcohort.sourcedataset_set.all()
        possible_datasets = SourceDataset.objects.filter(source_study_version__study = subcohort.study)
        unlinked_datasets = set(possible_datasets) - set(linked_datasets)
        if len(unlinked_datasets) < 1:
            raise ValueError('The subcohort is already linked to all possible datasets.')
        dataset_to_link = list(unlinked_datasets)[0]
        # Create a new dataset-subcohort link in the source db.
        add_subcohort_link_query = "INSERT INTO source_dataset_subcohorts (dataset_id, subcohort_id, date_added) VALUES ({}, {}, '{}');".format(subcohort.i_id, dataset_to_link.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_subcohort_link_query)
        self.source_db.commit()
        # Find a harmonized_trait_set which the source trait isn't linked to already
        for x in range(1, 100):
            htrait_set = HarmonizedTraitSet.objects.get(pk=x)
            if htrait_set not in source_trait.harmonizedtraitset_set.all():
                break
        # Add source_trait as a component trait of htrait_set in the source db.
        # Have to add a harmonized function here first...
        self.cursor.execute("INSERT INTO harmonized_function (function_definition) values ('return(dataset)');")
        self.source_db.commit()
        add_component_trait_query = "INSERT INTO component_source_trait (harmonized_trait_set_id, harmonized_function_id, component_trait_id, date_added) VALUES ({}, 1, {}, '{}');".format(htrait_set.i_id, source_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()

        # Run the update command.
        management.call_command('import_db', '--which_db=devel', '--update_only')

        # Refresh models from the db. 
        global_study.refresh_from_db()
        study.refresh_from_db()
        source_study_version.refresh_from_db()
        source_dataset.refresh_from_db()
        source_trait.refresh_from_db()
        subcohort.refresh_from_db()
        sev.refresh_from_db()
        harmonized_trait_set.refresh_from_db()
        harmonized_trait.refresh_from_db()
        hev.refresh_from_db()
        dataset_to_link.refresh_from_db()
        htrait_set.refresh_from_db()
        
        # Check that modified date > created date, values are updated, for each model.
        self.assertEqual(new_value, global_study.i_name)
        self.assertTrue(global_study.modified > t1)
    
        self.assertEqual(new_value, study.i_study_name)
        self.assertTrue(study.modified > t1)

        self.assertEqual(new_is_deprecated, source_study_version.i_is_deprecated)
        self.assertTrue(source_study_version.modified > t1)

        self.assertEqual(new_visit_code, source_dataset.i_visit_code)
        self.assertTrue(source_dataset.modified > t1)

        self.assertEqual(new_value, source_trait.i_description)
        self.assertTrue(source_trait.modified > t1)

        self.assertEqual(new_value, subcohort.i_name)
        self.assertTrue(subcohort.modified > t1)

        self.assertEqual(new_value, sev.i_value)
        self.assertTrue(sev.modified > t1)

        self.assertEqual(new_value, harmonized_trait_set.i_description)
        self.assertTrue(harmonized_trait_set.modified > t1)

        self.assertEqual(new_value, harmonized_trait.i_description)
        self.assertTrue(harmonized_trait.modified > t1)

        self.assertEqual(new_value, hev.i_value)
        self.assertTrue(hev.modified > t1)
        
        self.assertTrue(dataset_to_link in subcohort.sourcedataset_set.all())
        self.assertTrue(htrait_set in source_trait.harmonizedtraitset_set.all())

    def test_handle_with_new_study_added(self):
        """New data and updates are properly imported after a new study is added."""
        pass

