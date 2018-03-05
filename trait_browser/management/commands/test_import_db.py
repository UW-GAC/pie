"""Test the classes and functions in the populate_source_traits management command.

This test module won't run with the usual Django test command, because it's
in an unusual location. Instead, you must specify the path containing this
test module to get these tests to run.

Usage:
./manage.py test trait_browser/management/commands

This test module runs several unit tests and one integration test.
"""

from datetime import datetime, timedelta
from os.path import exists, join
from os import listdir, stat
from re import compile
from shutil import rmtree
from subprocess import call
from tempfile import mkdtemp
from time import sleep

import mysql.connector
# Use the mysql-connector-python-rf package from pypi.
# (Advice via this SO post http://stackoverflow.com/q/34168651/2548371)
from django.conf import settings
from django.core import management
from django.test import TestCase
from django.utils import timezone

from trait_browser.management.commands.import_db import Command, HUNIT_QUERY, STRING_TYPES
from trait_browser.management.commands.db_factory import fake_row_dict
from trait_browser import factories
from trait_browser import models


CMD = Command()
ORIGINAL_BACKUP_DIR = settings.DBBACKUP_STORAGE_OPTIONS['location']
TEST_DATA_DIR = 'trait_browser/source_db_test_data'
DBGAP_RE = compile(r'(?P<dbgap_id>phs\d{6}\.v\d+?\.pht\d{6}\.v\d+?)')


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


def load_test_source_db_data(filename):
    """Load the data from a specific test data set into the devel source db.

    Arguments:
        filename (str): name of the .sql mysql dump file, found in TEST_DATA_DIR
    """
    filepath = join(TEST_DATA_DIR, filename)
    # if verbose: print('Loading test data from ' + filepath + ' ...')
    mysql_load = ['mysql', '--defaults-file={}'.format(join(settings.SITE_ROOT, settings.CNF_PATH)),
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
    update_cmd = "UPDATE {} SET {}='{}' WHERE {}={};".format(
        table_name, update_field, new_value, where_field, where_value)
    # print(update_cmd)
    cursor.execute(update_cmd)
    source_db.commit()
    cursor.close()
    source_db.close()


def set_backup_dir():
    """Create a new temp dir and change the dbbackup setting to use it."""
    backup_dir = mkdtemp()
    settings.DBBACKUP_STORAGE_OPTIONS['location'] = backup_dir
    return backup_dir


def cleanup_backup_dir():
    """Remove the temp dir that was created to hold backups and revert the setting."""
    rmtree(settings.DBBACKUP_STORAGE_OPTIONS['location'])
    settings.DBBACKUP_STORAGE_OPTIONS['location'] = ORIGINAL_BACKUP_DIR


# Mixins.
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

    def check_imported_pks_match(self, pk_names, tables, models):
        """Check that imported primary keys match those from the appropriate source db table."""
        for source_pk, table_name, model in zip(pk_names, tables, models):
            # print(source_pk, table_name, model)
            query = 'SELECT {} FROM {}'.format(source_pk, table_name)
            self.cursor.execute(query)
            source_ids = [str(row[source_pk]) for row in self.cursor.fetchall()]
            self.assertEqual(sorted(source_ids), sorted(CMD._get_current_pks(model)))

    def check_imported_values_match(self, make_args_functions, tables, models):
        """Check that values for imported fields match those from the appropriate source db table."""
        for make_args, table_name, model in zip(make_args_functions, tables, models):
            # print(table_name, model)
            query = 'SELECT * FROM {}'.format(table_name)
            self.cursor.execute(query)
            for row in self.cursor:
                field_types = {el[0]: el[1] for el in self.cursor.description}
                model_args = make_args(CMD._fix_row(row, field_types))
                django_obj = model.objects.get(pk=model_args[model._meta.pk.name])
                for field in model_args:
                    self.assertEqual(getattr(django_obj, field), model_args[field], msg='Field: {}'.format(field))

    def check_imported_m2m_relations_match(self, m2m_tables, group_by_fields, concat_fields, parent_models,
                                           m2m_att_names):
        """Check that imported ManyToMany fields match those from the appropriate M2M source db table."""
        for table, group, concat, model, m2m_att in zip(m2m_tables, group_by_fields, concat_fields, parent_models,
                                                        m2m_att_names):
            query = 'SELECT GROUP_CONCAT({}) AS id_list,{} FROM {} GROUP BY {}'.format(concat, group, table, group)
            # print(table, group, concat, model, m2m_att)
            # print(query)
            self.cursor.execute(query)
            for row in self.cursor:
                field_types = {el[0]: el[1] for el in self.cursor.description}
                row = CMD._fix_row(row, field_types)
                source_ids = [int(i) for i in row['id_list'].split(',')]
                django_ids = [obj.pk for obj in getattr(model.objects.get(pk=row[group]), m2m_att).all()]
                self.assertEqual(sorted(source_ids), sorted(django_ids))


# TestCase superclasses (contain no tests).
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


class BaseTestDataReloadingTestCase(OpenCloseDBMixin, TestCase):
    """Superclass to test importing commands on the base.sql test source db data for every test method."""

    def setUp(self):
        """Load the base test data, once for each test method."""
        # Run the OpenCloseDBMixin setUp method.
        super(BaseTestDataReloadingTestCase, self).setUp()
        # Clean out the devel db and load the first test dataset.
        # By default, all tests will use dataset 1.
        clean_devel_db()
        load_test_source_db_data('base.sql')


# Tests that don't require test data.
class TestFunctionsTest(TestCase):
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
        field_types = {el[0]: el[1] for el in cursor.description}
        row = CMD._fix_row(row, field_types)
        cursor.close()
        source_db.close()
        self.assertEqual(row[update_field], new_val)
        clean_devel_db()

    # Turns out this is just a bad test, because it will fail monumentally if you use a different
    # version of mysqldump than was used to make the first test data.
    # def test_load_test_source_db_data(self):
    #     """Loading a test data set works as expected."""
    #     # clean the db, load the test data, do a mysqldump to a file, then read in
    #     # the two dump files, make some adjustments, and then compare the file contents.
    #     clean_devel_db()
    #     file_name = 'base.sql'
    #     test_file = join(TEST_DATA_DIR, file_name)
    #     load_test_source_db_data(file_name)
    #     # Parse the name of the devel db out of the mysql conf file.
    #     cnf_path = join(settings.SITE_ROOT, settings.CNF_PATH)
    #     with open(cnf_path) as f:
    #         cnf = f.readlines()
    #     statement_lines = [i for (i, line) in enumerate(cnf) if line.startswith('[')]
    #     devel_line = [i for (i, line) in enumerate(cnf) if line.startswith('[mysql_topmed_pheno_full_devel]')][0]
    #     next_statement_line = [i for i in statement_lines if i > devel_line][0]
    #     devel_lines = [x for x in range(len(cnf)) if (x >= devel_line) and (x < next_statement_line)]
    #     devel_db_line = [x for x in cnf[min(devel_lines):max(devel_lines)] if x.startswith('database = ')][0]
    #     devel_db_name = devel_db_line.replace('database = ', '').strip('\n')
    #     # Make the mysqldump command.
    #     tmp_file = 'tmp.sql'
    #     tmp_file_path = join(settings.SITE_ROOT, TEST_DATA_DIR, tmp_file)
    #     # Now do a mysqldump to the same file.
    #     mysqldump = ['mysqldump', '--defaults-file={}'.format(cnf_path),
    #                  '--defaults-group-suffix=_topmed_pheno_full_devel', '--opt',
    #                  devel_db_name, '>', tmp_file]
    #     return_code = call(' '.join(mysqldump), shell=True, cwd=join(settings.SITE_ROOT, TEST_DATA_DIR))
    #     if return_code != 0:
    #         raise ValueError('Something went wrong with the mysqldump command.')
    #     # Get the file contents to compare.
    #     with open(test_file, 'r') as f:
    #         test_file_contents = f.readlines()
    #     with open(tmp_file_path, 'r') as f:
    #         tmp_file_contents = f.readlines()
    #     # Delete lines that are expected to differ between the dump files.
    #     bad_words = ['DEFINER', 'Distrib', 'Host', 'Dump completed on', 'SET FOREIGN_KEY_CHECKS =']
    #     for word in bad_words:
    #         test_file_contents = [l for l in test_file_contents if word not in l]
    #         tmp_file_contents = [l for l in tmp_file_contents if word not in l]
    #     # Compare the files and delete the tmp file.
    #     self.assertEqual(tmp_file_contents, test_file_contents)
    #     remove(tmp_file_path)


class DbFixersTest(TestCase):
    """Tests of the _fix_[something] methods."""

    def test_fix_bytearray_no_bytearrays_left(self):
        """Bytearrays from the row_dict are converted to strings."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        for k in fixed_row:
            self.assertNotIsInstance(fixed_row[k], bytearray)

    def test_fix_bytearray_only_bytearrays_altered(self):
        """The non-bytearray values from the row_dict are not altered by _fix_bytearray."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_bytearray(row)
        bytearray_keys = [k for k in row.keys() if isinstance(row[k], bytearray)]
        other_keys = [k for k in row.keys() if not isinstance(row[k], bytearray)]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])

    def test_fix_bytearray_to_string(self):
        """The bytearray values from the row_dict are converted to string type."""
        row, types = fake_row_dict()
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
        row = {'a': 1, 'b': 'foobar', 'c': 1.56, 'd': datetime(2000, 1, 1)}
        fixed_row = CMD._fix_bytearray(row)
        self.assertDictEqual(row, fixed_row)

    def test_fix_null_no_none_left(self):
        """None is completely removed by _fix_null for string types."""
        types = {str(i): i for i in STRING_TYPES}
        row = {str(i): None for i in STRING_TYPES}
        fixed_row = CMD._fix_null(row, types)
        for k in fixed_row:
            self.assertIsNotNone(fixed_row[k])

    def test_fix_null_only_none_altered(self):
        """Only dict values of None are altered."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_null(row, types)
        none_keys = [k for k in row.keys() if row[k] is None]
        other_keys = [k for k in row.keys() if row[k] is not None]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k])

    def test_fix_null_only_string_types_altered(self):
        """Only None values for string type fields are altered."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_null(row, types)
        none_string_keys = [k for k in row.keys() if row[k] is None and types[k] in STRING_TYPES]
        other_keys = [k for k in row.keys() if k not in none_string_keys]
        for k in other_keys:
            self.assertEqual(row[k], fixed_row[k], msg='Field: {}'.format(k))

    def test_fix_null_string_fields_to_empty_string(self):
        """Dict values of None for each string type field are changed to empty strings."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_null(row, types)
        none_string_keys = [k for (k, t) in zip(row.keys(), types) if row[k] is None and t in STRING_TYPES]
        other_keys = [k for k in row.keys() if k not in none_string_keys]
        for k in none_string_keys:
            self.assertEqual(fixed_row[k], '')

    def test_fix_null_no_nones(self):
        """A dict containing no Nones is unchanged by _fix_null."""
        row = {'a': 1, 'b': 'foobar', 'c': 1.56, 'd': datetime(2000, 1, 1)}
        types = {field: t for (t, field) in zip(row, STRING_TYPES)}
        fixed_row = CMD._fix_null(row, types)
        self.assertDictEqual(row, fixed_row)

    def test_fix_null_empty_dict(self):
        """An empty dict is unchanged by _fix_null."""
        row = {}
        types = {}
        fixed_row = CMD._fix_null(row, types)
        self.assertDictEqual(row, fixed_row)

    def test_fix_null_date_stays_none(self):
        """Dict values of datetime and timestamp type are left as None."""
        row, types = fake_row_dict()
        row['datetime'] = None
        row['timestamp'] = None
        fixed_row = CMD._fix_null(row, types)
        self.assertIsNone(fixed_row['datetime'])
        self.assertIsNone(fixed_row['timestamp'])

    def test_fix_null_boolean_stays_none(self):
        """Dict values of boolean (tiny int) type are left as None."""
        row, types = fake_row_dict()
        row['boolean'] = None
        fixed_row = CMD._fix_null(row, types)
        self.assertIsNone(fixed_row['boolean'])

    def test_fix_timezone_result_is_aware(self):
        """The resulting datetimes from _fix_timezone are in fact timezone aware."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if isinstance(row[k], datetime):
                self.assertTrue(fixed_row[k].tzinfo is not None and
                                fixed_row[k].tzinfo.utcoffset(fixed_row[k]) is not None)

    def test_fix_timezone_only_datetimes_altered(self):
        """Non-datetime objects in the dict are not altered by _fix_timezone."""
        row, types = fake_row_dict()
        fixed_row = CMD._fix_timezone(row)
        for k in row:
            if not isinstance(row[k], datetime):
                self.assertEqual(row[k], fixed_row[k])

    def test_fix_timezone_still_datetime(self):
        """Datetime objects in the dict are still of datetime type after conversion by _fix_timezone."""
        row, types = fake_row_dict()
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
        row = {'a': 1, 'b': 'foobar', 'c': 1.56, 'd': None, 'e': bytearray('foobar', 'utf-8')}
        fixed_row = CMD._fix_timezone(row)
        self.assertDictEqual(fixed_row, row)


class GetDbTest(TestCase):
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


class DbLockingTest(TestCase):
    """Tests of the functions to lock the source db."""

    def test_lock_source_db_does_not_fail(self):
        source_db = CMD._get_source_db(which_db='devel', permissions='full')
        CMD._lock_source_db(source_db)

    def test_unlock_source_db_does_not_fail(self):
        source_db = CMD._get_source_db(which_db='devel', permissions='full')
        CMD._lock_source_db(source_db)
        CMD._unlock_source_db(source_db)

    # TODO: write tests that ensure the lock works
    # Could use this decorator from pytest-timeout package
    # @pytest.mark.timeout(180)


class M2MHelperTest(TestCase):
    """Tests of the helper functions for importing and updating m2m tables."""

    def test_break_m2m_link(self):
        """Removes a child model from its parent M2M field."""
        htsv = factories.HarmonizedTraitSetVersionFactory.create()
        reason = factories.AllowedUpdateReasonFactory.create()
        htsv.update_reasons.add(reason)
        CMD._break_m2m_link(
            models.HarmonizedTraitSetVersion, htsv.pk, models.AllowedUpdateReason, reason.pk, 'update_reasons')
        self.assertNotIn(reason, htsv.update_reasons.all())

    def test_make_m2m_link(self):
        """Adds a child model to its parent M2M field."""
        htsv = factories.HarmonizedTraitSetVersionFactory.create()
        reason = factories.AllowedUpdateReasonFactory.create()
        htsv.update_reasons.add(reason)
        CMD._make_m2m_link(
            models.HarmonizedTraitSetVersion, htsv.pk, models.AllowedUpdateReason, reason.pk, 'update_reasons')
        self.assertIn(reason, htsv.update_reasons.all())

    def test_import_new_m2m_field(self):
        pass

    def test_update_m2m_field(self):
        pass


class ImportHelperTest(TestCase):
    """Tests of the _import_[source|harmonized]_tables helper methods."""

    def test_import_source_tables(self):
        pass

    def test_import_harmonized_tables(self):
        pass


class UpdateHelperTest(TestCase):
    """Tests of the _update_[source|harmonized]_tables helper methods."""

    def test_update_source_tables(self):
        pass

    def test_update_harmonized_tables(self):
        pass


class GetCurrentListsTest(TestCase):
    """Tests of _get_current_pks with each possible model."""

    n = 32

    def test_get_current_global_studies(self):
        """Returns the right number of global_study ids."""
        factories.GlobalStudyFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.GlobalStudy)
        self.assertEqual(len(pks), self.n)

    def test_get_current_studies(self):
        """Returns the right number of study ids."""
        factories.StudyFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.Study)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_study_versions(self):
        """Returns the right number of source study version ids."""
        factories.SourceStudyVersionFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.SourceStudyVersion)
        self.assertEqual(len(pks), self.n)

    def test_get_current_subcohorts(self):
        """Returns the right number of subcohort ids."""
        factories.SubcohortFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.Subcohort)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_datasets(self):
        """Returns the right number of source dataset ids."""
        factories.SourceTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.SourceTrait)
        self.assertEqual(len(pks), self.n)

    def test_get_current_harmonized_trait_sets(self):
        """Returns the right number of harmonized trait sets."""
        factories.HarmonizedTraitSetFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.HarmonizedTraitSet)
        self.assertEqual(len(pks), self.n)

    def test_get_current_allowed_update_reasons(self):
        """Returns the right number of allowed update reason ids."""
        factories.AllowedUpdateReasonFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.AllowedUpdateReason)
        self.assertEqual(len(pks), self.n)

    def test_get_current_harmonized_trait_set_versions(self):
        """Returns the right number of harmonized trait set versions."""
        factories.HarmonizedTraitSetVersionFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.HarmonizedTraitSetVersion)
        self.assertEqual(len(pks), self.n)

    def test_get_current_harmonization_units(self):
        """Returns the right number of hamronization units."""
        factories.HarmonizationUnitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.HarmonizationUnit)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_traits(self):
        """Returns the right number of source trait ids."""
        factories.AllowedUpdateReasonFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.AllowedUpdateReason)
        self.assertEqual(len(pks), self.n)

    def test_get_current_harmonized_traits(self):
        """Returns the right number of harmonized trait ids."""
        factories.HarmonizedTraitFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.HarmonizedTrait)
        self.assertEqual(len(pks), self.n)

    def test_get_current_source_trait_encoded_values(self):
        """Returns the right number of source trait encoded value ids."""
        factories.SourceTraitEncodedValueFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.SourceTraitEncodedValue)
        self.assertEqual(len(pks), self.n)

    def test_get_current_harmonized_trait_encoded_values(self):
        """Returns the right number of harmonized trait encoded value ids."""
        factories.HarmonizedTraitEncodedValueFactory.create_batch(self.n)
        pks = CMD._get_current_pks(models.HarmonizedTraitEncodedValue)
        self.assertEqual(len(pks), self.n)


# Tests that require test data.
class SetDatasetNamesTest(BaseTestDataTestCase):
    """Tests of the _set_dataset_names method."""

    def test_dataset_name_after_import(self):
        """The dataset_name field is a valid-ish string after running an import."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        source_dataset_names = models.SourceDataset.objects.all().values_list('dataset_name', flat=True)
        # None of the dataset_names are empty strings anymore.
        self.assertNotIn('', source_dataset_names)
        # None of the dataset names have a phs.v.pht.v string in them.
        self.assertFalse(any([DBGAP_RE.search(name) for name in source_dataset_names]))
        # None of the dataset names have any directory path in them.
        self.assertFalse(any(['/' in name for name in source_dataset_names]))

    def test_dbgap_filename_after_import(self):
        """The dbgap_filename field is a valid-ish string after running an import."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        source_dataset_files = models.SourceDataset.objects.all().values_list('dbgap_filename', flat=True)
        # None of the dataset_names are empty strings anymore.
        self.assertNotIn('', source_dataset_files)
        # All of the file names have a phs.v.pht.v string in them.
        self.assertTrue(all([DBGAP_RE.search(name) for name in source_dataset_files]))
        # None of the file names have any directory path in them.
        self.assertFalse(any(['/' in name for name in source_dataset_files]))


class MakeArgsTest(BaseTestDataTestCase):
    """Tests of the _make_[model]_args functions."""

    def test_make_global_study_args_one_row_make_global_study_obj(self):
        """A GlobalStudy can be created from the args made from a row of test data."""
        global_study_query = 'SELECT * FROM global_study;'
        self.cursor.execute(global_study_query)
        row_dict = self.cursor.fetchone()
        field_types = {el[0]: el[1] for el in self.cursor.description}
        global_study_args = CMD._make_global_study_args(CMD._fix_row(row_dict, field_types))
        global_study = models.GlobalStudy(**global_study_args)
        global_study.save()
        self.assertIsInstance(global_study, models.GlobalStudy)

    def test_make_study_args_one_row_make_study_obj(self):
        """A Study can be created from the args made from a row of test data."""
        study_query = 'SELECT * FROM study;'
        self.cursor.execute(study_query)
        row_dict = self.cursor.fetchone()
        # Have to make a models.GlobalStudy first.
        global_study = factories.GlobalStudyFactory.create(i_id=row_dict['global_study_id'])
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        study_args = CMD._make_study_args(CMD._fix_row(row_dict, field_types))
        study = models.Study(**study_args)
        study.save()
        self.assertIsInstance(study, models.Study)

    def test_make_source_study_version_args_one_row_make_source_study_version_obj(self):
        """A SourceStudyVersion can be created from the args made from a row of test data."""
        source_study_version_query = 'SELECT * FROM source_study_version;'
        self.cursor.execute(source_study_version_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study and study first.
        global_study = factories.GlobalStudyFactory.create(i_id=1)
        study = factories.StudyFactory.create(i_accession=row_dict['accession'], global_study=global_study)
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        source_study_version_args = CMD._make_source_study_version_args(CMD._fix_row(row_dict, field_types))
        source_study_version = models.SourceStudyVersion(**source_study_version_args)
        source_study_version.save()
        self.assertIsInstance(source_study_version, models.SourceStudyVersion)

    def test_make_subcohort_args_one_row_make_subcohort_obj(self):
        """A Subcohort can be created from the args made from a row of test data."""
        subcohort_query = 'SELECT * FROM subcohort;'
        self.cursor.execute(subcohort_query)
        row_dict = self.cursor.fetchone()
        # Have to make a models.GlobalStudy first.
        global_study = factories.GlobalStudyFactory.create(i_id=row_dict['global_study_id'])
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        subcohort_args = CMD._make_subcohort_args(CMD._fix_row(row_dict, field_types))
        subcohort = models.Subcohort(**subcohort_args)
        subcohort.save()
        self.assertIsInstance(subcohort, models.Subcohort)

    def test_make_source_dataset_args_one_row_make_source_dataset_obj(self):
        """A SourceDataset can be created from the args made from a row of test data."""
        source_dataset_query = 'SELECT * FROM source_dataset;'
        self.cursor.execute(source_dataset_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, and source_study_version first.
        global_study = factories.GlobalStudyFactory.create(i_id=1)
        study = factories.StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = factories.SourceStudyVersionFactory.create(
            i_id=row_dict['study_version_id'], study=study)
        field_types = {el[0]: el[1] for el in self.cursor.description}
        source_dataset_args = CMD._make_source_dataset_args(CMD._fix_row(row_dict, field_types))
        #
        source_dataset = models.SourceDataset(**source_dataset_args)
        source_dataset.save()
        self.assertIsInstance(source_dataset, models.SourceDataset)

    def test_make_harmonized_trait_set_args_one_row_make_harmonized_trait_set_obj(self):
        """A HarmonizedTraitSet can be created from the args made from a row of test data."""
        harmonized_trait_set_query = 'SELECT * FROM harmonized_trait_set;'
        self.cursor.execute(harmonized_trait_set_query)
        row_dict = self.cursor.fetchone()
        field_types = {el[0]: el[1] for el in self.cursor.description}
        harmonized_trait_set_args = CMD._make_harmonized_trait_set_args(CMD._fix_row(row_dict, field_types))
        #
        harmonized_trait_set = models.HarmonizedTraitSet(**harmonized_trait_set_args)
        harmonized_trait_set.save()
        self.assertIsInstance(harmonized_trait_set, models.HarmonizedTraitSet)

    def test_make_allowed_update_reason_args_one_row_make_allowed_update_reason_obj(self):
        """A AllowedUpdateReason can be created from the args made from a row of test data."""
        allowed_update_reason_query = 'SELECT * FROM allowed_update_reason;'
        self.cursor.execute(allowed_update_reason_query)
        row_dict = self.cursor.fetchone()
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        allowed_update_reason_args = CMD._make_allowed_update_reason_args(CMD._fix_row(row_dict, field_types))
        allowed_update_reason = models.AllowedUpdateReason(**allowed_update_reason_args)
        allowed_update_reason.save()
        self.assertIsInstance(allowed_update_reason, models.AllowedUpdateReason)

    def test_make_harmonized_trait_set_version_args_one_row_make_harmonized_trait_set_version_obj(self):
        """A HarmonizedTraitSetVersion can be created from the args made from a row of test data."""
        harmonized_trait_set_version_query = 'SELECT * FROM harmonized_trait_set_version;'
        self.cursor.execute(harmonized_trait_set_version_query)
        row_dict = self.cursor.fetchone()
        # Have to make a HarmonizedTraitSet first.
        harmonized_trait_set = factories.HarmonizedTraitSetFactory.create(i_id=row_dict['harmonized_trait_set_id'])
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        harmonized_trait_set_version_args = CMD._make_harmonized_trait_set_version_args(
            CMD._fix_row(row_dict, field_types))
        harmonized_trait_set_version = models.HarmonizedTraitSetVersion(**harmonized_trait_set_version_args)
        harmonized_trait_set_version.save()
        self.assertIsInstance(harmonized_trait_set_version, models.HarmonizedTraitSetVersion)

    def test_make_source_trait_args_one_row_make_source_trait_obj(self):
        """A SourceTrait can be created from the args made from a row of test data."""
        source_trait_query = 'SELECT * FROM source_trait;'
        self.cursor.execute(source_trait_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, source_study_version, and source_dataset first.
        global_study = factories.GlobalStudyFactory.create(i_id=1)
        study = factories.StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = factories.SourceStudyVersionFactory.create(i_id=1, study=study)
        source_dataset = factories.SourceDatasetFactory.create(
            i_id=row_dict['dataset_id'], source_study_version=source_study_version)
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        source_trait_args = CMD._make_source_trait_args(CMD._fix_row(row_dict, field_types))
        source_trait = models.SourceTrait(**source_trait_args)
        source_trait.save()
        self.assertIsInstance(source_trait, models.SourceTrait)

    def test_make_harmonized_trait_args_one_row_make_harmonized_trait_obj(self):
        """A HarmonizedTrait can be created from the args made from a row of test data."""
        harmonized_trait_query = 'SELECT * FROM harmonized_trait;'
        self.cursor.execute(harmonized_trait_query)
        row_dict = self.cursor.fetchone()
        # Have to make harmonized_trait_set first.
        harmonized_trait_set_version = factories.HarmonizedTraitSetVersionFactory.create(
            i_id=row_dict['harmonized_trait_set_version_id'])
        #
        field_types = {el[0]: el[1] for el in self.cursor.description}
        harmonized_trait_args = CMD._make_harmonized_trait_args(CMD._fix_row(row_dict, field_types))
        harmonized_trait = models.HarmonizedTrait(**harmonized_trait_args)
        harmonized_trait.save()
        self.assertIsInstance(harmonized_trait, models.HarmonizedTrait)

    def test_make_source_trait_encoded_value_args_one_row_make_source_trait_encoded_value_obj(self):
        """A SourceTraitEncodedValue can be created from the args made from a row of test data."""
        source_trait_encoded_value_query = 'SELECT * FROM source_trait_encoded_values;'
        self.cursor.execute(source_trait_encoded_value_query)
        row_dict = self.cursor.fetchone()
        # Have to make global study, study, source_study_version, source_dataset, and source_trait first.
        global_study = factories.GlobalStudyFactory.create(i_id=1)
        study = factories.StudyFactory.create(i_accession=1, global_study=global_study)
        source_study_version = factories.SourceStudyVersionFactory.create(i_id=1, study=study)
        source_dataset = factories.SourceDatasetFactory.create(i_id=1, source_study_version=source_study_version)
        source_trait = factories.SourceTraitFactory.create(
            i_trait_id=row_dict['source_trait_id'], source_dataset=source_dataset)
        field_types = {el[0]: el[1] for el in self.cursor.description}
        fixed_row = CMD._fix_row(row_dict, field_types)
        source_trait_encoded_value_args = CMD._make_source_trait_encoded_value_args(fixed_row)
        source_trait_encoded_value = models.SourceTraitEncodedValue(**source_trait_encoded_value_args)
        source_trait_encoded_value.save()
        self.assertIsInstance(source_trait_encoded_value, models.SourceTraitEncodedValue)

    def test_make_harmonized_trait_encoded_value_args_one_row_make_harmonized_trait_encoded_value_obj(self):
        """A HarmonizedTraitEncodedValue can be created from the args made from a row of test data."""
        # Get a single harmonized_trait_encoded_value from the source db
        harmonized_trait_encoded_value_query = 'SELECT * FROM harmonized_trait_encoded_values;'
        self.cursor.execute(harmonized_trait_encoded_value_query)
        row_dict = self.cursor.fetchone()
        # Get information for the harmonized_trait the encoded value is connected to.
        harmonized_trait_query = 'SELECT * FROM harmonized_trait WHERE harmonized_trait_id = {};'.format(
            row_dict['harmonized_trait_id'])
        self.cursor.execute(harmonized_trait_query)
        harmonized_trait_row_dict = self.cursor.fetchone()
        # Make a harmonized_trait and harmonized_trait_set before trying to make the encoded value object.
        harmonized_trait = factories.HarmonizedTraitFactory.create(
            i_trait_id=row_dict['harmonized_trait_id'],
            harmonized_trait_set_version__i_id=harmonized_trait_row_dict['harmonized_trait_set_version_id'])
        # Make the encoded value object.
        field_types = {el[0]: el[1] for el in self.cursor.description}
        fixed_row = CMD._fix_row(row_dict, field_types)
        harmonized_trait_encoded_value_args = CMD._make_harmonized_trait_encoded_value_args(fixed_row)
        harmonized_trait_encoded_value = models.HarmonizedTraitEncodedValue(**harmonized_trait_encoded_value_args)
        harmonized_trait_encoded_value.save()
        self.assertIsInstance(harmonized_trait_encoded_value, models.HarmonizedTraitEncodedValue)


class HelperTest(BaseTestDataTestCase):
    """Tests of the helper functions from import_db.Command()."""

    def test_make_table_query(self):
        """Makes a valid query."""
        query = CMD._make_table_query(source_table='study')
        self.cursor.execute(query)
        self.assertIsNotNone(self.cursor.fetchone())

    def test_make_table_query_with_filter(self):
        """Makes a valid query."""
        query = CMD._make_table_query(
            source_table='study', filter_field='accession', filter_values=['286'], filter_not=False)
        self.cursor.execute(query)
        self.assertIsNotNone(self.cursor.fetchone())

    def test_make_table_query_with_not_filter(self):
        """Makes a valid query."""
        query = CMD._make_table_query(
            source_table='study', filter_field='accession', filter_values=['286'], filter_not=True)
        self.cursor.execute(query)
        self.assertIsNotNone(self.cursor.fetchone())

    def test_make_table_query_filter_values_empty(self):
        """Makes a valid query when filter_values is empty."""
        query = CMD._make_table_query(
            source_table='study', filter_field='accession', filter_values=[], filter_not=False)
        self.cursor.execute(query)
        self.assertIsNone(self.cursor.fetchone())

    def test_make_global_study_from_args(self):
        """_make_model_object_from_args works to make a global study."""
        CMD._make_model_object_from_args(
            model_args={'i_id': 5, 'i_name': 'global study name', 'i_date_added': timezone.now(),
                        'i_date_changed': timezone.now()},
            model=models.GlobalStudy)
        obj = models.GlobalStudy.objects.get(pk=5)
        self.assertIsInstance(obj, models.GlobalStudy)

    def test_make_model_object_per_query_row_global_study(self):
        """Makes a study object for every row in a query result."""
        # Test with global_study because it is not dependent on any other models.
        query = 'SELECT * FROM global_study'
        CMD._make_model_object_per_query_row(
            source_db=self.source_db, query=query, make_args=CMD._make_global_study_args,
            **{'model': models.GlobalStudy})
        self.cursor.execute(query)
        ids = [row['id'] for row in self.cursor.fetchall()]
        imported_ids = [gs.i_id for gs in models.GlobalStudy.objects.all()]
        self.assertEqual(sorted(ids), sorted(imported_ids))

    def test_make_query_for_new_rows(self):
        """Makes a query that properly returns new rows of data from the study table."""
        self.cursor.execute('SELECT * FROM study')
        all_accessions = [row['accession'] for row in self.cursor.fetchall()]
        old_pks = all_accessions[0:1]
        query = CMD._make_query_for_new_rows('study', 'accession', [str(el) for el in old_pks])
        self.cursor.execute(query)
        retrieved_accessions = [row['accession'] for row in self.cursor.fetchall()]
        for phs in all_accessions:
            if phs in old_pks:
                self.assertNotIn(phs, retrieved_accessions)
            else:
                self.assertIn(phs, retrieved_accessions)

    # def test_make_args_mapping(self):
        # Testing this function generically is not worth it, since it's already
        # tested specifically multiple times in the MakeArgsTestCase

    def test_import_new_data_global_study(self):
        """Imports data from the global_study correctly into the models.GlobalStudy model."""
        new_global_study_pks = CMD._import_new_data(source_db=self.source_db,
                                                    source_table='global_study',
                                                    source_pk='id',
                                                    model=models.GlobalStudy,
                                                    make_args=CMD._make_global_study_args)
        self.cursor.execute('SELECT * FROM global_study')
        pks_in_db = [row['id'] for row in self.cursor.fetchall()]
        imported_pks = [gs.pk for gs in models.GlobalStudy.objects.all()]
        self.assertEqual(pks_in_db, imported_pks)

    def test_make_query_for_rows_to_update_global_study(self):
        """Returns a query that contains only the updated rows."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        # Data about how to make the update in the source db.
        model = models.GlobalStudy
        model_instance = model.objects.all()[0]
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        # Make the update in the source db.
        old_pks = CMD._get_current_pks(models.GlobalStudy)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        # Make the query.
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        updated_query = CMD._make_query_for_rows_to_update(
            source_db_table_name, model, old_pks, source_db_pk_name, changed_greater=True)
        self.cursor.execute(updated_query)
        updates = self.cursor.fetchall()
        self.assertTrue(len(updates) == 1)
        field_types = {el[0]: el[1] for el in self.cursor.description}
        updated_row = CMD._fix_row(updates[0], field_types)
        self.assertEqual(updated_row[field_to_update], new_value)
        self.assertEqual(updated_row[source_db_pk_name], model_instance.pk)

    def test_update_model_object_from_args_global_study(self):
        """Makes updates to a global study from model_args dict."""
        global_study = factories.GlobalStudyFactory.create()
        old_name = global_study.i_name
        new_name = global_study.i_name + '_modified'
        model_args = {'i_id': global_study.pk, 'i_name': new_name}
        CMD._update_model_object_from_args(model_args, models.GlobalStudy, expected=True)
        global_study.refresh_from_db()
        self.assertEqual(global_study.i_name, new_name)

    # def test_update_model_object_per_query_row(self):
        # A test of this function would be almost exactly like the tests in the
        # UpdateModelsTestCase, so I'm not writing another one here...

    def test_update_existing_data_global_study(self):
        """Updates in global_study are imported."""
        # Have to clean and reload the db because of updates in previous tests.
        clean_devel_db()
        load_test_source_db_data('base.sql')
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        # Change the data in the source db.
        model = models.GlobalStudy
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')
        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        # Need to open the db and cursor again...
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # This update is not technically expected, but get rid of the warning.
        global_study_update_count = CMD._update_existing_data(
            source_db=self.source_db, source_table='global_study', source_pk='id', model=models.GlobalStudy,
            make_args=CMD._make_global_study_args, expected=True)
        # Check that modified date > created date, and name is set to new value.
        model_instance.refresh_from_db()
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)


class BackupTest(BaseTestDataTestCase):
    """Tests to make sure backing up the Django db in handle() is working right."""

    def test_backup_is_created(self):
        """Backup dump file is created in the expected directory."""
        set_backup_dir()
        # No initial fake data in the test db is needed here. Backing up an empty db works fine.
        # Import data from the source db.
        management.call_command('import_db', '--which_db=devel')
        # Does the backup dir exist?
        self.assertTrue(exists(settings.DBBACKUP_STORAGE_OPTIONS['location']))
        # Is there a single compressed dump file in there?
        backup_files = listdir(settings.DBBACKUP_STORAGE_OPTIONS['location'])
        self.assertTrue(len(backup_files) == 1)
        self.assertTrue(backup_files[0].endswith('.dump.gz'))
        # Is a reasonable size that would indicate it's not empty?
        file_size = stat(join(settings.DBBACKUP_STORAGE_OPTIONS['location'], backup_files[0])).st_size
        self.assertTrue(1000000000 > file_size > 100)
        cleanup_backup_dir()

    def test_backup_can_be_restored(self):
        """A saved backup can be used to restore the db to it's previous state."""
        # TODO: Couldn't get the dbrestore command to work, so leaving this for later.
        return None
        set_backup_dir()

        # Import data from the source db.
        management.call_command('import_db', '--which_db=devel')
        # Restore from the backup file.

        # Make a new backup file after the restore.

        # Is the contents of the new backup the same as the old?

        cleanup_backup_dir()


class SpecialQueryTest(BaseTestDataTestCase):
    """Test the special queries saved as constant variables in import_db."""

    def test_HUNIT_QUERY(self):
        """HUNIT_QUERY returns good results."""
        self.cursor.execute(HUNIT_QUERY)
        results = self.cursor.fetchall()
        self.assertTrue(len(results) == 16)  # Change if changing test data.
        self.assertIn('harmonized_trait_id', results[0].keys())
        self.assertIn('harmonization_unit_id', results[0].keys())


class UpdateModelsTest(BaseTestDataTestCase):
    """Tests of the update functions with updates to each possible source_db table."""

    # Source trait updates.
    def test_update_global_study(self):
        """Updates in global_study are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.GlobalStudy
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_study(self):
        """Updates in study are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.Study
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'study'
        field_to_update = 'study_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_source_study_version(self):
        """Updates in source_study_version are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceStudyVersion
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_study_version'
        field_to_update = 'is_deprecated'
        new_value = not getattr(model_instance, 'i_' + field_to_update)
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_source_dataset(self):
        """Updates in source_dataset table are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceDataset
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_dataset'
        field_to_update = 'dbgap_description'
        new_value = 'asdgsdfg'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_subcohort(self):
        """Updates in subcohort are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.Subcohort
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'subcohort'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_source_trait(self):
        """Updates in source_trait table are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceTrait
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_trait'
        field_to_update = 'dbgap_comment'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'source_trait_id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_source_trait_encoded_value(self):
        """Updates in source_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceTraitEncodedValue
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    # Harmonized trait updates.
    def test_update_harmonized_trait_set(self):
        """Updates to harmonized_trait_set are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitSet
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_set'
        field_to_update = 'trait_set_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_harmonized_trait_set_version(self):
        """Updates to harmonized_trait_set_version are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitSetVersion
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_set_version'
        field_to_update = 'harmonized_by'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_allowed_update_reason(self):
        """Updates to allowed_update_reason are NOT imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.AllowedUpdateReason
        model_instance = model.objects.all()[0]
        source_db_table_name = 'allowed_update_reason'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # There should NOT be any imported updates.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))

    def test_update_harmonization_unit(self):
        """Updates to harmonization_unit are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizationUnit
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonization_unit'
        field_to_update = 'tag'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_harmonized_trait(self):
        """Updates to harmonized_trait are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTrait
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'harmonized_trait_id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertTrue(model_instance.modified > old_mod_time)

    def test_update_harmonized_trait_encoded_value(self):
        """Updates to harmonized_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitEncodedValue
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertTrue(model_instance.modified > old_mod_time)

    # M2M link updates.
    def test_update_added_harmonized_trait_set_version_update_reasons(self):
        """A new reason link to an existing harmonized_trait_set_version is imported after an update."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick an allowed reason to create a new link to in the source db.
        reason = models.AllowedUpdateReason.objects.get(pk=1)
        # Find a harmonized_trait_set_version that this reason isn't linked to yet.
        linked_hts_versions = reason.harmonizedtraitsetversion_set.all()
        possible_hts_versions = models.HarmonizedTraitSetVersion.objects.all()
        unlinked_hts_versions = set(possible_hts_versions) - set(linked_hts_versions)
        if len(unlinked_hts_versions) < 1:
            raise ValueError('The allowed update reason is already linked to all possible datasets.')
        hts_version_to_link = list(unlinked_hts_versions)[0]
        # Create a new hts_version-allowed_reason link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        add_reason_link_query = """INSERT INTO harmonized_trait_set_version_update_reason (reason_id,
                                   harmonized_trait_set_version_id, date_added)
                                   VALUES ({}, {}, '{}');""".format(
            reason.pk, hts_version_to_link.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_reason_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen reason is now linked to the hts_version that was picked, in the Django db.
        reason.refresh_from_db()
        hts_version_to_link.refresh_from_db()
        self.assertTrue(hts_version_to_link in reason.harmonizedtraitsetversion_set.all())
        self.assertTrue(reason in hts_version_to_link.update_reasons.all())

    def test_update_removed_harmonized_trait_set_version_update_reasons(self):
        """A harmonized_trait_set_version - reason link that is no longer in the source db is removed after update."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a hts_version to remove the link to in the source db.
        hts_version_to_unlink = models.HarmonizedTraitSetVersion.objects.filter(i_version=2).order_by('?').first()
        reason_to_unlink = hts_version_to_unlink.update_reasons.all().order_by('?').first()
        # Remove the link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        remove_reason_link_query = """DELETE FROM harmonized_trait_set_version_update_reason WHERE
                                      harmonized_trait_set_version_id={} AND
                                      reason_id={}""".format(hts_version_to_unlink.pk, reason_to_unlink.pk)
        self.cursor.execute(remove_reason_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen reason is not linked to the hts_version now, in the Django db.
        reason_to_unlink.refresh_from_db()
        hts_version_to_unlink.refresh_from_db()
        self.assertFalse(hts_version_to_unlink in reason_to_unlink.harmonizedtraitsetversion_set.all())
        self.assertFalse(reason_to_unlink in hts_version_to_unlink.update_reasons.all())

    def test_update_add_component_source_traits(self):
        """A new component source trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_source_traits__in=[source_trait]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_source_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertTrue(htrait_to_link in source_trait.source_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_link in source_trait.source_component_of_harmonization_unit.all())

    def test_update_remove_component_source_traits(self):
        """A deleted component source trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_source_traits=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_source_trait = hunit_to_unlink.component_source_traits.all().order_by('?').first()
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_source_trait WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_source_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_source_trait.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertFalse(htrait_to_unlink in component_source_trait.source_component_of_harmonized_trait.all())
        self.assertFalse(hunit_to_unlink in component_source_trait.source_component_of_harmonization_unit.all())

    def test_update_add_component_batch_traits(self):
        """A new component batch trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_batch_traits__in=[source_trait]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_batch_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertTrue(htrait_to_link in source_trait.batch_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_link in source_trait.batch_component_of_harmonization_unit.all())

    def test_update_remove_component_batch_traits(self):
        """A deleted component batch trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a batch trait to remove a link to in the batch db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_batch_traits=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_batch_trait = hunit_to_unlink.component_batch_traits.all().order_by('?').first()
        # Open batch db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component batch trait link.
        remove_component_trait_query = """DELETE FROM component_batch_trait WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_batch_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_batch_trait.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertFalse(htrait_to_unlink in component_batch_trait.batch_component_of_harmonized_trait.all())
        self.assertFalse(hunit_to_unlink in component_batch_trait.batch_component_of_harmonization_unit.all())

    def test_update_add_component_age_traits(self):
        """A new component source trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_age_traits__in=[source_trait]))[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_age_trait (harmonization_unit_id, component_trait_id,
                                       date_added) values ('{}', '{}', '{}')""".format(
            hunit_to_link.i_id, source_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertTrue(hunit_to_link in source_trait.age_component_of_harmonization_unit.all())

    def test_update_remove_component_age_traits(self):
        """A deleted component age trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_age_traits=None).order_by('?').first()
        component_age_trait = hunit_to_unlink.component_age_traits.all().order_by('?').first()
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_age_trait WHERE harmonization_unit_id={} AND
                                          component_trait_id={}""".format(
            hunit_to_unlink.pk, component_age_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_age_trait.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertFalse(hunit_to_unlink in component_age_trait.age_component_of_harmonization_unit.all())

    def test_update_add_component_harmonized_trait_set_versions(self):
        """New component harmonized trait links to existing harmonized trait and harmonization unit are imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a harmonized trait set to create a new link to in the source db.
        harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.get(pk=1)
        # Find a harmonization_unit which this harmonized trait set isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(
                component_harmonized_trait_set_versions__in=[harmonized_trait_set_version]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_harmonized_trait_set (harmonized_trait_id,
                                       harmonization_unit_id, component_trait_set_version_id, date_added) values
                                       ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, harmonized_trait_set_version.i_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        harmonized_trait_set_version.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertTrue(htrait_to_link in harmonized_trait_set_version.harmonized_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_link in harmonized_trait_set_version.harmonized_component_of_harmonization_unit.all())

    def test_update_remove_component_harmonized_trait_set_versions(self):
        """Deleted component harmonized trait links to a harmonized trait and a harmonization unit are removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(
            component_harmonized_trait_set_versions=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_harmonized_trait_set_version = hunit_to_unlink.component_harmonized_trait_set_versions.all().order_by('?').first()  # noqa: E501
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_harmonized_trait_set WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_set_version_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_harmonized_trait_set_version.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_harmonized_trait_set_version.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertFalse(
            htrait_to_unlink in component_harmonized_trait_set_version.harmonized_component_of_harmonized_trait.all())
        self.assertFalse(
            hunit_to_unlink in component_harmonized_trait_set_version.harmonized_component_of_harmonization_unit.all())


class ImportNoUpdateTest(BaseTestDataTestCase):
    """Tests that updated source data is NOT imported when the --import_only flag is used."""

    # Source trait updates.
    def test_no_update_global_study(self):
        """Updates in global_study are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.GlobalStudy
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'global_study'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_study(self):
        """Updates in study are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.Study
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'study'
        field_to_update = 'study_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_source_study_version(self):
        """Updates in source_study_version are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceStudyVersion
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_study_version'
        field_to_update = 'is_deprecated'
        new_value = not getattr(model_instance, 'i_' + field_to_update)
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_source_dataset(self):
        """Updates in source_dataset table are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceDataset
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_dataset'
        field_to_update = 'dbgap_description'
        new_value = 'asdgsdfg'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_subcohort(self):
        """Updates in subcohort are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.Subcohort
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'subcohort'
        field_to_update = 'name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_source_trait(self):
        """Updates in source_trait table are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceTrait
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_trait'
        field_to_update = 'dbgap_comment'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'source_trait_id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_source_trait_encoded_value(self):
        """Updates in source_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.SourceTraitEncodedValue
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'source_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    # Harmonized trait updates.
    def test_no_update_harmonized_trait_set(self):
        """Updates to harmonized_trait_set are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitSet
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_set'
        field_to_update = 'trait_set_name'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_harmonized_trait_set_version(self):
        """Updates to harmonized_trait_set_version are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitSetVersion
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_set_version'
        field_to_update = 'harmonized_by'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_allowed_update_reason(self):
        """Updates to allowed_update_reason are NOT imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.AllowedUpdateReason
        model_instance = model.objects.all()[0]
        source_db_table_name = 'allowed_update_reason'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # There should NOT be any imported updates.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))

    def test_no_update_harmonization_unit(self):
        """Updates to harmonization_unit are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizationUnit
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonization_unit'
        field_to_update = 'tag'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_harmonized_trait(self):
        """Updates to harmonized_trait are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTrait
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait'
        field_to_update = 'description'
        new_value = 'asdfghjkl'
        source_db_pk_name = 'harmonized_trait_id'

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_description'))
        self.assertFalse(model_instance.modified > old_mod_time)

    def test_no_update_harmonized_trait_encoded_value(self):
        """Updates to harmonized_trait_encoded_values are imported."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()

        model = models.HarmonizedTraitEncodedValue
        model_instance = model.objects.all()[0]
        old_mod_time = model_instance.modified
        source_db_table_name = 'harmonized_trait_encoded_values'
        field_to_update = 'value'
        new_value = 'asdfghjkl'
        source_db_pk_name = model_instance._meta.pk.name.replace('i_', '')

        sleep(1)
        change_data_in_table(source_db_table_name, field_to_update, new_value, source_db_pk_name, model_instance.pk)
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        model_instance.refresh_from_db()
        # Check that modified date > created date, and name is set to new value.
        self.assertNotEqual(new_value, getattr(model_instance, 'i_' + field_to_update))
        self.assertFalse(model_instance.modified > old_mod_time)

    # M2M link updates.
    def test_no_update_added_harmonized_trait_set_version_update_reasons(self):
        """A new reason link to an existing harmonized_trait_set_version is imported after an update."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick an allowed reason to create a new link to in the source db.
        reason = models.AllowedUpdateReason.objects.get(pk=1)
        # Find a harmonized_trait_set_version that this reason isn't linked to yet.
        linked_hts_versions = reason.harmonizedtraitsetversion_set.all()
        possible_hts_versions = models.HarmonizedTraitSetVersion.objects.all()
        unlinked_hts_versions = set(possible_hts_versions) - set(linked_hts_versions)
        if len(unlinked_hts_versions) < 1:
            raise ValueError('The allowed update reason is already linked to all possible datasets.')
        hts_version_to_link = list(unlinked_hts_versions)[0]
        # Create a new hts_version-allowed_reason link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        add_reason_link_query = """INSERT INTO harmonized_trait_set_version_update_reason (reason_id,
                                   harmonized_trait_set_version_id, date_added)
                                   VALUES ({}, {}, '{}');""".format(
            reason.pk, hts_version_to_link.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_reason_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen reason is now linked to the hts_version that was picked, in the Django db.
        reason.refresh_from_db()
        hts_version_to_link.refresh_from_db()
        self.assertFalse(hts_version_to_link in reason.harmonizedtraitsetversion_set.all())
        self.assertFalse(reason in hts_version_to_link.update_reasons.all())

    def test_no_update_removed_harmonized_trait_set_version_update_reasons(self):
        """A harmonized_trait_set_version - reason link that is no longer in the source db is removed after update."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a hts_version to remove the link to in the source db.
        hts_version_to_unlink = models.HarmonizedTraitSetVersion.objects.filter(i_version=2).order_by('?').first()
        reason_to_unlink = hts_version_to_unlink.update_reasons.all().order_by('?').first()
        # Remove the link in the source db.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        remove_reason_link_query = """DELETE FROM harmonized_trait_set_version_update_reason WHERE
                                      harmonized_trait_set_version_id={} AND
                                      reason_id={}""".format(hts_version_to_unlink.pk, reason_to_unlink.pk)
        self.cursor.execute(remove_reason_link_query)
        self.source_db.commit()
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen reason is not linked to the hts_version now, in the Django db.
        reason_to_unlink.refresh_from_db()
        hts_version_to_unlink.refresh_from_db()
        self.assertTrue(hts_version_to_unlink in reason_to_unlink.harmonizedtraitsetversion_set.all())
        self.assertTrue(reason_to_unlink in hts_version_to_unlink.update_reasons.all())

    def test_no_update_add_component_source_traits(self):
        """A new component source trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_source_traits__in=[source_trait]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_source_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertFalse(htrait_to_link in source_trait.source_component_of_harmonized_trait.all())
        self.assertFalse(hunit_to_link in source_trait.source_component_of_harmonization_unit.all())

    def test_no_update_remove_component_source_traits(self):
        """A deleted component source trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_source_traits=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_source_trait = hunit_to_unlink.component_source_traits.all().order_by('?').first()
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_source_trait WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_source_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_source_trait.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertTrue(htrait_to_unlink in component_source_trait.source_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_unlink in component_source_trait.source_component_of_harmonization_unit.all())

    def test_no_update_add_component_batch_traits(self):
        """A new component batch trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_batch_traits__in=[source_trait]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_batch_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertFalse(htrait_to_link in source_trait.batch_component_of_harmonized_trait.all())
        self.assertFalse(hunit_to_link in source_trait.batch_component_of_harmonization_unit.all())

    def test_no_update_remove_component_batch_traits(self):
        """A deleted component batch trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a batch trait to remove a link to in the batch db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_batch_traits=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_batch_trait = hunit_to_unlink.component_batch_traits.all().order_by('?').first()
        # Open batch db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component batch trait link.
        remove_component_trait_query = """DELETE FROM component_batch_trait WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_batch_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_batch_trait.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertTrue(htrait_to_unlink in component_batch_trait.batch_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_unlink in component_batch_trait.batch_component_of_harmonization_unit.all())

    def test_no_update_add_component_age_traits(self):
        """A new component source trait link to an existing harmonized trait is imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to create a new link to in the source db.
        source_trait = models.SourceTrait.objects.get(pk=1)
        # Find a harmonization_unit which this source trait isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_age_traits__in=[source_trait]))[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_age_trait (harmonization_unit_id, component_trait_id,
                                       date_added) values ('{}', '{}', '{}')""".format(
            hunit_to_link.i_id, source_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        source_trait.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertFalse(hunit_to_link in source_trait.age_component_of_harmonization_unit.all())

    def test_no_update_remove_component_age_traits(self):
        """A deleted component age trait link is removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(component_age_traits=None).order_by('?').first()
        component_age_trait = hunit_to_unlink.component_age_traits.all().order_by('?').first()
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_age_trait WHERE harmonization_unit_id={} AND
                                          component_trait_id={}""".format(
            hunit_to_unlink.pk, component_age_trait.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_age_trait.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertTrue(hunit_to_unlink in component_age_trait.age_component_of_harmonization_unit.all())

    def test_no_update_add_component_harmonized_trait_set_versions(self):
        """New component harmonized trait links to existing harmonized trait and harmonization unit are imported."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a harmonized trait set to create a new link to in the source db.
        harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.get(pk=1)
        # Find a harmonization_unit which this harmonized trait set isn't linked to already
        hunit_to_link = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(
                component_harmonized_trait_set_versions__in=[harmonized_trait_set_version]))[0]
        # Find a harmonized trait from within this harmonization unit.
        htrait_to_link = hunit_to_link.harmonizedtrait_set.all()[0]
        # Prep for altering the devel db.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Add source_trait as a component trait of harmonization unit and harmonized trait in the source db.
        add_component_trait_query = """INSERT INTO component_harmonized_trait_set (harmonized_trait_id,
                                       harmonization_unit_id, component_trait_set_version_id, date_added) values
                                       ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link.i_trait_id, hunit_to_link.i_id, harmonized_trait_set_version.i_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        last_id = self.cursor.fetchone()['last']
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the chosen source trait is now linked to the correct harmonization unit and harmonized trait.
        harmonized_trait_set_version.refresh_from_db()
        htrait_to_link.refresh_from_db()
        hunit_to_link.refresh_from_db()
        self.assertFalse(
            htrait_to_link in harmonized_trait_set_version.harmonized_component_of_harmonized_trait.all())
        self.assertFalse(
            hunit_to_link in harmonized_trait_set_version.harmonized_component_of_harmonization_unit.all())

    def test_no_update_remove_component_harmonized_traits(self):
        """Deleted component harmonized trait links to a harmonized trait and a harmonization unit are removed."""
        # Run the initial db import.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Pick a source trait to remove a link to in the source db.
        hunit_to_unlink = models.HarmonizationUnit.objects.exclude(
            component_harmonized_trait_set_versions=None).order_by('?').first()
        htrait_to_unlink = hunit_to_unlink.harmonizedtrait_set.all().order_by('?').first()
        component_harmonized_trait_set_version = hunit_to_unlink.component_harmonized_trait_set_versions.all().order_by('?').first()  # noqa: E501
        # Open source db with full privileges.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Remove a component source trait link.
        remove_component_trait_query = """DELETE FROM component_harmonized_trait_set WHERE harmonized_trait_id={} AND
                                          harmonization_unit_id={} AND component_trait_set_version_id={}""".format(
            htrait_to_unlink.pk, hunit_to_unlink.pk, component_harmonized_trait_set_version.pk)
        self.cursor.execute(remove_component_trait_query)
        self.source_db.commit()
        # Close the db connection.
        self.cursor.close()
        self.source_db.close()
        # Now run the update commands.
        management.call_command('import_db', '--which_db=devel', '--import_only', '--verbosity=0', '--no_backup')
        # Check that the link between these two models is now gone.
        component_harmonized_trait_set_version.refresh_from_db()
        htrait_to_unlink.refresh_from_db()
        hunit_to_unlink.refresh_from_db()
        self.assertTrue(
            htrait_to_unlink in component_harmonized_trait_set_version.harmonized_component_of_harmonized_trait.all())
        self.assertTrue(
            hunit_to_unlink in component_harmonized_trait_set_version.harmonized_component_of_harmonization_unit.all())


# Tests that run import_db from start to finish.
class IntegrationTest(BaseTestDataReloadingTestCase):
    """Integration test of the whole management command.

    It's very difficult to test just one function at a time here, because of
    all the inter-object relationships and the data being pulled from the
    source database. So just run one big integration test here rather than
    nice unit tests.
    """

    def test_imported_ids_match_source_ids(self):
        """import_db imports all of the primary keys for each model."""
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        # Check all of the regular models.
        pk_names = (
            'id',
            'accession',
            'id',
            'id',
            'id',
            'id',
            'id',
            'id',
            'id',
            'source_trait_id',
            'harmonized_trait_id',
            'id',
            'id',
        )
        tables = (
            'global_study',
            'study',
            'source_study_version',
            'subcohort',
            'source_dataset',
            'harmonized_trait_set',
            'allowed_update_reason',
            'harmonized_trait_set_version',
            'harmonization_unit',
            'source_trait',
            'harmonized_trait',
            'source_trait_encoded_values',
            'harmonized_trait_encoded_values',
        )
        model_names = (
            models.GlobalStudy,
            models.Study,
            models.SourceStudyVersion,
            models.Subcohort,
            models.SourceDataset,
            models.HarmonizedTraitSet,
            models.AllowedUpdateReason,
            models.HarmonizedTraitSetVersion,
            models.HarmonizationUnit,
            models.SourceTrait,
            models.HarmonizedTrait,
            models.SourceTraitEncodedValue,
            models.HarmonizedTraitEncodedValue,
        )
        self.check_imported_pks_match(pk_names, tables, model_names)
        # Check all of the M2M relationships.
        m2m_tables = (
            'component_source_trait',
            'component_harmonized_trait_set',
            'component_batch_trait',
            'component_age_trait',
            'component_source_trait',
            'component_harmonized_trait_set',
            'component_batch_trait',
            'harmonized_trait_set_version_update_reason',
        )
        group_by_fields = (
            'harmonized_trait_id',
            'harmonized_trait_id',
            'harmonized_trait_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonized_trait_set_version_id',
        )
        concat_fields = (
            'component_trait_id',
            'component_trait_set_version_id',
            'component_trait_id',
            'component_trait_id',
            'component_trait_id',
            'component_trait_set_version_id',
            'component_trait_id',
            'reason_id',
        )
        parent_models = (
            models.HarmonizedTrait,
            models.HarmonizedTrait,
            models.HarmonizedTrait,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizedTraitSetVersion,
        )
        m2m_att_names = (
            'component_source_traits',
            'component_harmonized_trait_set_versions',
            'component_batch_traits',
            'component_age_traits',
            'component_source_traits',
            'component_harmonized_trait_set_versions',
            'component_batch_traits',
            'update_reasons',
        )
        self.check_imported_m2m_relations_match(
            m2m_tables, group_by_fields, concat_fields, parent_models, m2m_att_names)
        # Load a new study and run all of these checks again.
        self.cursor.close()
        self.source_db.close()
        load_test_source_db_data('new_study.sql')
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Check all of the regular models again.
        self.check_imported_pks_match(pk_names, tables, model_names)
        # Check all of the M2M relationships again.
        self.check_imported_m2m_relations_match(
            m2m_tables, group_by_fields, concat_fields, parent_models, m2m_att_names)

    def test_updated_data_from_every_table(self):
        """Every kind of update is detected and imported by import_db."""
        # This test is largely just all of the methods from UpdateModelsTestCase all put together.
        # Initial call of the import command.
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        t1 = timezone.now()
        new_value = 'asdfghjkl'  # Use this value to reset things in multiple models.
        # Close the db connections because change_data_in_table() opens new connections.
        # This does not affect the .cursor and .source_db attributes in other functions.
        self.cursor.close()
        self.source_db.close()
        # Update the global study table.
        global_study = models.GlobalStudy.objects.all()[0]
        sleep(1)
        change_data_in_table(
            'global_study', 'name', new_value, global_study._meta.pk.name.replace('i_', ''), global_study.pk)
        # Update the study table.
        study = models.Study.objects.all()[0]
        change_data_in_table('study', 'study_name', new_value, study._meta.pk.name.replace('i_', ''), study.pk)
        # Update the source study version table.
        source_study_version = models.SourceStudyVersion.objects.all()[0]
        new_is_deprecated = not source_study_version.i_is_deprecated
        change_data_in_table(
            'source_study_version', 'is_deprecated', new_is_deprecated,
            source_study_version._meta.pk.name.replace('i_', ''), source_study_version.pk)
        # Update source dataset table.
        source_dataset = models.SourceDataset.objects.all()[0]
        new_description = '23oriuam.sadflkj'
        change_data_in_table(
            'source_dataset', 'dbgap_description', new_description, source_dataset._meta.pk.name.replace('i_', ''),
            source_dataset.pk)
        # Update the subcohort table.
        subcohort = models.Subcohort.objects.get(pk=1)
        change_data_in_table('subcohort', 'name', new_value, subcohort._meta.pk.name.replace('i_', ''), subcohort.pk)
        # Update source trait table.
        source_trait = models.SourceTrait.objects.all()[0]
        change_data_in_table('source_trait', 'dbgap_comment', new_value, 'source_trait_id', source_trait.pk)
        # Update source trait encoded values table.
        sev = models.SourceTraitEncodedValue.objects.all()[0]
        change_data_in_table(
            'source_trait_encoded_values', 'value', new_value, sev._meta.pk.name.replace('i_', ''), sev.pk)
        # Update harmonized trait set table.
        harmonized_trait_set = models.HarmonizedTraitSet.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_set', 'trait_set_name', new_value, harmonized_trait_set._meta.pk.name.replace('i_', ''),
            harmonized_trait_set.pk)
        # Update harmonized trait set version table.
        harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_set_version', 'harmonized_by',
            new_value, harmonized_trait_set_version._meta.pk.name.replace('i_', ''), harmonized_trait_set_version.pk
        )
        # Don't update allowed update reason table, because it should NOT change.
        # Update harmonization unit table.
        harmonization_unit = models.HarmonizationUnit.objects.all()[0]
        change_data_in_table(
            'harmonization_unit', 'tag', new_value, harmonization_unit._meta.pk.name.replace('i_', ''),
            harmonization_unit.pk
        )
        # Update harmonized trait table.
        harmonized_trait = models.HarmonizedTrait.objects.all()[0]
        change_data_in_table('harmonized_trait', 'description', new_value, 'harmonized_trait_id', harmonized_trait.pk)
        # Update harmonized trait encoded values table.
        hev = models.HarmonizedTraitEncodedValue.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_encoded_values', 'value', new_value, hev._meta.pk.name.replace('i_', ''), hev.pk)

        # Prep for doing updates for m2m tables.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)

        # Add a component source trait.
        component_source_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_source = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_source_traits__in=[component_source_trait]))[0]
        htrait_to_link_source = hunit_to_link_source.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_source_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_source.i_trait_id, hunit_to_link_source.i_id, component_source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        # Add a component batch trait.
        component_batch_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_batch = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_batch_traits__in=[component_batch_trait]))[0]
        htrait_to_link_batch = hunit_to_link_batch.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_batch_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_batch.i_trait_id, hunit_to_link_batch.i_id, component_batch_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        # Add a component age trait.
        component_age_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_age = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_age_traits__in=[component_age_trait]))[0]
        add_component_trait_query = """INSERT INTO component_age_trait (harmonization_unit_id, component_trait_id,
                                       date_added) values ('{}', '{}', '{}')""".format(
            hunit_to_link_age.i_id, component_age_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        # Add a component harmonized trait set version.
        component_harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.order_by('?').first()
        hunit_to_link_harmonized = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(
                component_harmonized_trait_set_versions__in=[component_harmonized_trait_set_version]))[0]
        htrait_to_link_harmonized = hunit_to_link_harmonized.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_harmonized_trait_set (harmonized_trait_id,
                                       harmonization_unit_id, component_trait_set_version_id, date_added) values
                                       ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_harmonized.i_trait_id, hunit_to_link_harmonized.i_id,
            component_harmonized_trait_set_version.i_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.cursor.execute(add_component_trait_query)
        # Add an update reason to a harmonized trait set version.
        reason_to_link = models.AllowedUpdateReason.objects.get(pk=1)
        linked_hts_versions = reason_to_link.harmonizedtraitsetversion_set.all()
        possible_hts_versions = models.HarmonizedTraitSetVersion.objects.all()
        unlinked_hts_versions = set(possible_hts_versions) - set(linked_hts_versions)
        hts_version_to_link_reason = list(unlinked_hts_versions)[0]
        add_reason_link_query = """INSERT INTO harmonized_trait_set_version_update_reason (reason_id,
                                   harmonized_trait_set_version_id, date_added)
                                   VALUES ({}, {}, '{}');""".format(
            reason_to_link.pk, hts_version_to_link_reason.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_reason_link_query)

        self.source_db.commit()

        # Close the db connection.
        self.cursor.close()
        self.source_db.close()

        # Run the update command.
        management.call_command('import_db', '--which_db=devel', '--update_only', '--verbosity=0', '--no_backup')

        # Refresh models from the db.
        global_study.refresh_from_db()
        study.refresh_from_db()
        source_study_version.refresh_from_db()
        source_dataset.refresh_from_db()
        subcohort.refresh_from_db()
        source_trait.refresh_from_db()
        sev.refresh_from_db()
        harmonized_trait_set.refresh_from_db()
        harmonized_trait_set_version.refresh_from_db()
        harmonization_unit.refresh_from_db()
        harmonized_trait.refresh_from_db()
        hev.refresh_from_db()

        component_source_trait.refresh_from_db()
        htrait_to_link_source.refresh_from_db()
        hunit_to_link_source.refresh_from_db()

        component_batch_trait.refresh_from_db()
        htrait_to_link_batch.refresh_from_db()
        hunit_to_link_batch.refresh_from_db()

        component_age_trait.refresh_from_db()
        hunit_to_link_age.refresh_from_db()

        component_harmonized_trait_set_version.refresh_from_db()
        htrait_to_link_harmonized.refresh_from_db()
        hunit_to_link_harmonized.refresh_from_db()

        reason_to_link.refresh_from_db()
        hts_version_to_link_reason.refresh_from_db()

        # Check that modified date > created date, values are updated, for each model.
        self.assertEqual(new_value, global_study.i_name)
        self.assertTrue(global_study.modified > t1)

        self.assertEqual(new_value, study.i_study_name)
        self.assertTrue(study.modified > t1)

        self.assertEqual(new_is_deprecated, source_study_version.i_is_deprecated)
        self.assertTrue(source_study_version.modified > t1)

        self.assertEqual(new_description, source_dataset.i_dbgap_description)
        self.assertTrue(source_dataset.modified > t1)

        self.assertEqual(new_value, subcohort.i_name)
        self.assertTrue(subcohort.modified > t1)

        self.assertEqual(new_value, source_trait.i_dbgap_comment)
        self.assertTrue(source_trait.modified > t1)

        self.assertEqual(new_value, sev.i_value)
        self.assertTrue(sev.modified > t1)

        self.assertEqual(new_value, harmonized_trait_set.i_trait_set_name)
        self.assertTrue(harmonized_trait_set.modified > t1)

        self.assertEqual(new_value, harmonized_trait_set_version.i_harmonized_by)
        self.assertTrue(harmonized_trait_set_version.modified > t1)

        self.assertEqual(new_value, harmonization_unit.i_tag)
        self.assertTrue(harmonization_unit.modified > t1)

        self.assertEqual(new_value, harmonized_trait.i_description)
        self.assertTrue(harmonized_trait.modified > t1)

        self.assertEqual(new_value, hev.i_value)
        self.assertTrue(hev.modified > t1)

        self.assertTrue(htrait_to_link_source in component_source_trait.source_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_link_source in component_source_trait.source_component_of_harmonization_unit.all())

        self.assertTrue(htrait_to_link_batch in component_batch_trait.batch_component_of_harmonized_trait.all())
        self.assertTrue(hunit_to_link_batch in component_batch_trait.batch_component_of_harmonization_unit.all())

        self.assertTrue(hunit_to_link_age in component_age_trait.age_component_of_harmonization_unit.all())

        self.assertTrue(htrait_to_link_harmonized in component_harmonized_trait_set_version.harmonized_component_of_harmonized_trait.all())  # noqa: E501
        self.assertTrue(hunit_to_link_harmonized in component_harmonized_trait_set_version.harmonized_component_of_harmonization_unit.all())  # noqa: E501

        self.assertTrue(reason_to_link in hts_version_to_link_reason.update_reasons.all())
        self.assertTrue(hts_version_to_link_reason in reason_to_link.harmonizedtraitsetversion_set.all())

    def test_values_match_after_all_updates(self):
        """All imported field values match those in the source db after making updates to the source db."""
        # Initial import of the test data (with visit).
        management.call_command('import_db', '--which_db=devel', '--no_backup')

        # Prepare for making changes in the devel database.
        # Close the db connections because change_data_in_table() opens new connections.
        self.cursor.close()
        self.source_db.close()

        # Copy/paste the upper part from test_updated_data_from_every_table and copy/paste the lower part from
        # test_imported_ids_match_source_ids

        # Make updates of every kind in the devel db.
        new_value = 'asdfghjkl'  # Use this value to reset things in multiple models.
        # Update the global study table.
        global_study = models.GlobalStudy.objects.all()[0]
        sleep(1)
        change_data_in_table(
            'global_study', 'name', new_value, global_study._meta.pk.name.replace('i_', ''), global_study.pk)
        # Update the study table.
        study = models.Study.objects.all()[0]
        change_data_in_table('study', 'study_name', new_value, study._meta.pk.name.replace('i_', ''), study.pk)
        # Update the source study version table.
        source_study_version = models.SourceStudyVersion.objects.all()[0]
        new_is_deprecated = not source_study_version.i_is_deprecated
        change_data_in_table(
            'source_study_version', 'is_deprecated', new_is_deprecated,
            source_study_version._meta.pk.name.replace('i_', ''), source_study_version.pk)
        # Update source dataset table.
        source_dataset = models.SourceDataset.objects.all()[0]
        new_description = '23oriuam.sadflkj'
        change_data_in_table(
            'source_dataset', 'dbgap_description', new_description, source_dataset._meta.pk.name.replace('i_', ''),
            source_dataset.pk)
        # Update the subcohort table.
        subcohort = models.Subcohort.objects.get(pk=1)
        change_data_in_table('subcohort', 'name', new_value, subcohort._meta.pk.name.replace('i_', ''), subcohort.pk)
        # Update source trait table.
        source_trait = models.SourceTrait.objects.all()[0]
        change_data_in_table('source_trait', 'dbgap_comment', new_value, 'source_trait_id', source_trait.pk)
        # Update source trait encoded values table.
        sev = models.SourceTraitEncodedValue.objects.all()[0]
        change_data_in_table(
            'source_trait_encoded_values', 'value', new_value, sev._meta.pk.name.replace('i_', ''), sev.pk)
        # Update harmonized trait set table.
        harmonized_trait_set = models.HarmonizedTraitSet.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_set', 'trait_set_name', new_value, harmonized_trait_set._meta.pk.name.replace('i_', ''),
            harmonized_trait_set.pk)
        # Update harmonized trait set version table.
        harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_set_version', 'harmonized_by',
            new_value, harmonized_trait_set_version._meta.pk.name.replace('i_', ''), harmonized_trait_set_version.pk
        )
        # Don't update allowed update reason table, because it should NOT change.
        # Update harmonization unit table.
        harmonization_unit = models.HarmonizationUnit.objects.all()[0]
        change_data_in_table(
            'harmonization_unit', 'tag', new_value, harmonization_unit._meta.pk.name.replace('i_', ''),
            harmonization_unit.pk
        )
        # Update harmonized trait table.
        harmonized_trait = models.HarmonizedTrait.objects.all()[0]
        change_data_in_table('harmonized_trait', 'description', new_value, 'harmonized_trait_id', harmonized_trait.pk)
        # Update harmonized trait encoded values table.
        hev = models.HarmonizedTraitEncodedValue.objects.all()[0]
        change_data_in_table(
            'harmonized_trait_encoded_values', 'value', new_value, hev._meta.pk.name.replace('i_', ''), hev.pk)

        # Prep for doing updates for m2m tables.
        self.source_db = get_devel_db(permissions='full')
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)

        # Add a component source trait.
        component_source_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_source = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_source_traits__in=[component_source_trait]))[0]
        htrait_to_link_source = hunit_to_link_source.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_source_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_source.i_trait_id, hunit_to_link_source.i_id, component_source_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        # Add a component batch trait.
        component_batch_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_batch = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_batch_traits__in=[component_batch_trait]))[0]
        htrait_to_link_batch = hunit_to_link_batch.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_batch_trait (harmonized_trait_id, harmonization_unit_id,
                                       component_trait_id, date_added) values ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_batch.i_trait_id, hunit_to_link_batch.i_id, component_batch_trait.i_trait_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        # Add a component age trait.
        component_age_trait = models.SourceTrait.objects.order_by('?').first()
        hunit_to_link_age = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(component_age_traits__in=[component_age_trait]))[0]
        add_component_trait_query = """INSERT INTO component_age_trait (harmonization_unit_id, component_trait_id,
                                       date_added) values ('{}', '{}', '{}')""".format(
            hunit_to_link_age.i_id, component_age_trait.i_trait_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_component_trait_query)
        self.source_db.commit()
        self.cursor.execute('SELECT LAST_INSERT_ID() AS last')
        # Add a component harmonized trait set version.
        component_harmonized_trait_set_version = models.HarmonizedTraitSetVersion.objects.order_by('?').first()
        hunit_to_link_harmonized = models.HarmonizationUnit.objects.exclude(
            i_id__in=models.HarmonizationUnit.objects.filter(
                component_harmonized_trait_set_versions__in=[component_harmonized_trait_set_version]))[0]
        htrait_to_link_harmonized = hunit_to_link_harmonized.harmonized_trait_set_version.harmonizedtrait_set.all()[0]
        add_component_trait_query = """INSERT INTO component_harmonized_trait_set (harmonized_trait_id,
                                       harmonization_unit_id, component_trait_set_version_id, date_added) values
                                       ('{}', '{}', '{}', '{}')""".format(
            htrait_to_link_harmonized.i_trait_id, hunit_to_link_harmonized.i_id,
            component_harmonized_trait_set_version.i_id,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.cursor.execute(add_component_trait_query)
        # Add an update reason to a harmonized trait set version.
        reason_to_link = models.AllowedUpdateReason.objects.get(pk=1)
        linked_hts_versions = reason_to_link.harmonizedtraitsetversion_set.all()
        possible_hts_versions = models.HarmonizedTraitSetVersion.objects.all()
        unlinked_hts_versions = set(possible_hts_versions) - set(linked_hts_versions)
        hts_version_to_link_reason = list(unlinked_hts_versions)[0]
        add_reason_link_query = """INSERT INTO harmonized_trait_set_version_update_reason (reason_id,
                                   harmonized_trait_set_version_id, date_added)
                                   VALUES ({}, {}, '{}');""".format(
            reason_to_link.pk, hts_version_to_link_reason.i_id, timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.cursor.execute(add_reason_link_query)

        self.source_db.commit()

        # Close the full privileges db connection, and reopen as read-only.
        self.cursor.close()
        self.source_db.close()
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)

        # Get the updates.
        management.call_command('import_db', '--which_db=devel', '--no_backup', '--verbosity=0')

        # Check all of the regular models.
        make_args_functions = (
            CMD._make_global_study_args,
            CMD._make_study_args,
            CMD._make_source_study_version_args,
            CMD._make_subcohort_args,
            CMD._make_source_dataset_args,
            CMD._make_harmonized_trait_set_args,
            CMD._make_allowed_update_reason_args,
            CMD._make_harmonized_trait_set_version_args,
            CMD._make_harmonization_unit_args,
            CMD._make_source_trait_args,
            CMD._make_harmonized_trait_args,
            CMD._make_source_trait_encoded_value_args,
            CMD._make_harmonized_trait_encoded_value_args,
        )
        tables = (
            'global_study',
            'study',
            'source_study_version',
            'subcohort',
            'source_dataset',
            'harmonized_trait_set',
            'allowed_update_reason',
            'harmonized_trait_set_version',
            'harmonization_unit',
            'source_trait',
            'harmonized_trait',
            'source_trait_encoded_values',
            'harmonized_trait_encoded_values',
        )
        model_names = (
            models.GlobalStudy,
            models.Study,
            models.SourceStudyVersion,
            models.Subcohort,
            models.SourceDataset,
            models.HarmonizedTraitSet,
            models.AllowedUpdateReason,
            models.HarmonizedTraitSetVersion,
            models.HarmonizationUnit,
            models.SourceTrait,
            models.HarmonizedTrait,
            models.SourceTraitEncodedValue,
            models.HarmonizedTraitEncodedValue,
        )
        self.check_imported_values_match(make_args_functions, tables, model_names)
        # Check all of the M2M relationships.
        m2m_tables = (
            'component_source_trait',
            'component_harmonized_trait_set',
            'component_batch_trait',
            'component_age_trait',
            'component_source_trait',
            'component_harmonized_trait_set',
            'component_batch_trait',
            'harmonized_trait_set_version_update_reason',
        )
        group_by_fields = (
            'harmonized_trait_id',
            'harmonized_trait_id',
            'harmonized_trait_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonization_unit_id',
            'harmonized_trait_set_version_id',
        )
        concat_fields = (
            'component_trait_id',
            'component_trait_set_version_id',
            'component_trait_id',
            'component_trait_id',
            'component_trait_id',
            'component_trait_set_version_id',
            'component_trait_id',
            'reason_id',
        )
        parent_models = (
            models.HarmonizedTrait,
            models.HarmonizedTrait,
            models.HarmonizedTrait,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizationUnit,
            models.HarmonizedTraitSetVersion,
        )
        m2m_att_names = (
            'component_source_traits',
            'component_harmonized_trait_set_versions',
            'component_batch_traits',
            'component_age_traits',
            'component_source_traits',
            'component_harmonized_trait_set_versions',
            'component_batch_traits',
            'update_reasons',
        )
        self.check_imported_m2m_relations_match(
            m2m_tables, group_by_fields, concat_fields, parent_models, m2m_att_names)

        # Load a new study and run all of these checks again.
        self.cursor.close()
        self.source_db.close()
        load_test_source_db_data('new_study.sql')
        management.call_command('import_db', '--which_db=devel', '--no_backup')
        self.source_db = get_devel_db()
        self.cursor = self.source_db.cursor(buffered=True, dictionary=True)
        # Check all of the regular models again.
        self.check_imported_values_match(make_args_functions, tables, model_names)
        # Check all of the M2M relationships again.
        self.check_imported_m2m_relations_match(
            m2m_tables, group_by_fields, concat_fields, parent_models, m2m_att_names)
