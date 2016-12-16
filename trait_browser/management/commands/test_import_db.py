"""Test the classes and functions in the populate_source_traits management command.

This test module won't run with the usual Django test command, because it's
in an unusual location. Instead, you must specify the path containing this
test module to get these tests to run.

Usage:
./manage.py test trait_browser/management/commands

This test module runs several unit tests and one integration test.
"""

from datetime import datetime
from os.path import join
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
    """Get a connection to the devel source db."""
    return CMD._get_source_db(which_db='devel', permissions=permissions)

def clean_devel_db(verbose=False):
    """Remove all existing data from the devel source db."""
    if verbose: print('Getting source db connection ...')
    source_db = get_devel_db(permissions='full')
    cursor = source_db.cursor(buffered=True, dictionary=False)
    if verbose: print('Emptying current data from devel source db ...')
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
def load_test_source_db_data(filename, verbose=False):
    """
    Load the data from a specific test data set into the devel source db.
    
    Args:
        filename -- name of the .sql mysql dump file, found in TEST_DATA_DIR
    """
    filepath = join(TEST_DATA_DIR, filename)
    if verbose: print('Loading test data from ' + filepath + ' ...')
    mysql_load = ['mysql', '--defaults-file={}'.format(settings.CNF_PATH),
                 '--defaults-group-suffix=_topmed_pheno_full_devel', '<', filepath]
    return_code = call(' '.join(mysql_load), shell=True, cwd=settings.SITE_ROOT)
    if return_code == 1:
        raise ValueError('MySQL failed to load test data.')
    else:
        if verbose: print('Test data loaded ...')

def change_data_in_table(table_name, update_field, new_value, where_field, where_value):
    source_db = get_devel_db(permissions='full')
    cursor = source_db.cursor(buffered=True)
    update_cmd = "UPDATE {} SET {}='{}' WHERE {}={};".format(table_name, update_field, new_value, where_field, where_value)
    cursor.execute(update_cmd)
    source_db.commit()
    cursor.close()
    source_db.close()

class BaseTestDataTestCase(TestCase):
    """Superclass to test importing commands on the base.sql test source db data."""
    
    @classmethod
    def setUpClass(cls):
        # Run the TestCase setUpClass method.
        super(BaseTestDataTestCase, cls).setUpClass()
        # Clean out the devel db and load the first test dataset.
        # By default, all tests will use dataset 1.
        clean_devel_db(verbose=True)
        load_test_source_db_data('base.sql', verbose=True)
    
    def setUp(self):
        """ """
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
    
    def tearDown(self):
        """ """
        self.cursor.close()
        self.source_db.close()


class VisitTestDataTestCase(TestCase):
    """Tests that need visit data to already be added to the source db test data."""
    
    @classmethod
    def setUpClass(cls):
        # Run the TestCase setUpClass method.
        super(VisitTestDataTestCase, cls).setUpClass()
        # Clean out the devel db and load the first test dataset.
        # By default, all tests will use dataset 1.
        clean_devel_db(verbose=True)
        load_test_source_db_data('base_plus_visit.sql', verbose=True)
    
    def setUp(self):
        """ """
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
    
    def tearDown(self):
        """ """
        self.cursor.close()
        self.source_db.close()


class VisitTestCase(VisitTestDataTestCase):
    
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

    def test_fix_bytearray_no_bytearrays_left(self):
        """Test that bytearrays from the row_dict are converted to strings."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        for k in fixed_row:
            self.assertNotIsInstance(fixed_row[k], bytearray)
    
    def test_fix_bytearray_only_bytearrays_altered(self):
        """Ensure that the non-bytearray values from the row_dict are not altered by _fix_bytearray."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])

    def test_fix_bytearray_to_string(self):
        """Ensure that the bytearray values from the row_dict are converted to string type."""
        row = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in bytearray_keys:
            self.assertIsInstance(fixed_row[k], str)
        
    def test_fix_bytearray_empty_bytearray(self):
        """Ensure that the _fix_bytearray function works on an empty bytearray."""
        row = {'empty_bytearray': bytearray('', 'utf-8')}
        fixed_row = CMD._fix_bytearray(row)
        self.assertEqual(fixed_row['empty_bytearray'], '')
    
    def test_fix_bytearray_non_utf8(self):
        """Ensure that _fix_bytearray works on a bytearray with a different encoding that utf-8."""
        row = {'ascii_bytearray': bytearray('foobar', 'ascii')}
        fixed_row = CMD._fix_bytearray(row)
        self.assertEqual(fixed_row['ascii_bytearray'], 'foobar')
    
    def test_fix_bytearray_empty_dict(self):
        """Ensure that _fix_bytearray works on an empty dictionary."""
        row = {}
        fixed_row = CMD._fix_bytearray(row)
        self.assertDictEqual(fixed_row, {})
    
    def test_fix_bytearray_no_bytearrays(self):
        """Ensure that the row_dict is unchanged when _fix_bytearray is given a dict with no bytearrays in it."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        fixed_row = CMD._fix_bytearray(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_no_none_left(self):
        """Ensure that None is completely removed by _fix_null."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        for k in fixed_row:
            self.assertIsNotNone(fixed_row[k])
    
    def test_fix_null_only_none_altered(self):
        """Ensure that only dict values of None are altered."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_null_to_empty_string(self):
        """Ensure that the dict values of None are changed to empty strings."""
        row = fake_row_dict()
        fixed_row = CMD._fix_null(row)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in none_keys:
            self.assertEqual(fixed_row[k], '')
    
    def test_fix_null_no_nones(self):
        """Ensure that a dict containing no Nones is unchanged by _fix_null."""
        row = {'a':1, 'b':'foobar', 'c':1.56, 'd': datetime(2000, 1, 1)}
        fixed_row = CMD._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_null_empty_dict(self):
        """Ensure that an empty dict is unchanged by _fix_null."""
        row = {}
        fixed_row = CMD._fix_null(row)
        self.assertDictEqual(row, fixed_row)
    
    def test_fix_timezone_result_is_aware(self):
        """Ensure that the resulting datetimes from _fix_timezone are in fact timezone aware."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(fixed_row[k].tzinfo is not None and
                                fixed_row[k].tzinfo.utcoffset(fixed_row[k]) is not None)
    
    def test_fix_timezone_only_datetimes_altered(self):
        """Ensure that non-datetime objects in the dict are not altered by _fix_timezone."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if not isinstance(row[k], datetime):
                self.assertEqual(row[k], fixed_row[k])
    
    def test_fix_timezone_still_datetime(self):
        """Ensure that datetime objects in the dict are still of datetime type after conversion by _fix_timezone."""
        row = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(isinstance(fixed_row[k], datetime))
    
    def test_fix_timezone_empty_dict(self):
        """Ensure that _fix_timezone works properly on (doesn't alter) an empty dictionary input."""
        row = {}
        fixed_row = CMD._fix_timezone(row)
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
        fixed_row = CMD._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)
    

class GetDbTestCase(TestCase):
    
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


class MakeArgsTestCase(BaseTestDataTestCase):
    
    def test_make_global_study_args_one_row_make_global_study_obj(self):
        """Get a single row of test data from the database and see if the results from _make_global_study_args can be used to successfully make and save a Global_study object."""
        global_study_query = 'SELECT * FROM global_study;'
        self.cursor.execute(global_study_query)
        row_dict = self.cursor.fetchone()
        global_study_args = CMD._make_global_study_args(CMD._fix_null(CMD._fix_bytearray(row_dict)))
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


class HelperTestCase(TestCase):
    
    def test_make_model_object_from_args(self):
        """Test that """
        CMD._make_model_object_from_args(args={'i_id':5, 'i_name':'global study name'},
                                              model=GlobalStudy,
                                              verbosity=0)
        obj = GlobalStudy.objects.get(pk=5)
        self.assertIsInstance(obj, GlobalStudy)
        

class GetCurrentListsTest(TestCase):
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

    def test_get_current_source_datasets(self):
        """Test that Command._get_current_source_datasets() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)
    
    def test_get_current_source_traits(self):
        """Test that Command._get_current_source_traits() returns the right number of trait ids."""
        SourceTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTrait)
        self.assertEqual(len(pks), self.n)

    def test_get_current_subcohorts(self):
        """Test that Command._get_current_subcohorts() returns the right number of trait ids."""
        SubcohortFactory.create_batch(self.n)
        pks = CMD._get_current_pks(Subcohort)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_trait_encoded_values(self):
        """Test that Command._get_current_source_trait_encoded_values() returns the right number of trait ids."""
        SourceTraitEncodedValueFactory.create_batch(self.n)
        pks = CMD._get_current_pks(SourceTraitEncodedValue)
        self.assertEqual(len(pks), self.n)


class IntegrationTest(VisitTestDataTestCase):
    """Integration test of the whole management command.
    
    It's very difficult to test just one function at a time here, because of
    all the inter-object relationships and the data being pulled from the
    source database. So just run one big integration test here rather than
    nice unit tests.
    """

    def test_handle_with_visit_data(self):
        """Ensure that calling the command as you would from command line works properly."""
        management.call_command('import_db', '--which_db=devel')
        
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
            row = CMD._fix_row(row)
            django_count = SourceDataset.objects.get(pk=row['dataset_id']).subcohorts.count()
            self.assertEqual(row['COUNT(*)'], django_count)

        source_trait_encoded_values_query = 'SELECT COUNT(*) FROM source_trait_encoded_values;'
        self.cursor.execute(source_trait_encoded_values_query)
        source_trait_encoded_values_count = self.cursor.fetchone()['COUNT(*)']
        self.assertEqual(source_trait_encoded_values_count, SourceTraitEncodedValue.objects.count())

    def test_handle_with_updated_data(self):
        """Ensure that calling the command as you would from command line works properly."""
        pass

    def test_handle_with_new_study_added(self):
        """Ensure that the whole workflow of the management command works to add objects to the website databse, without limits."""
        pass

