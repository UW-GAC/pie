"""Management commands for the trait_browser app.

management commands added:
    populate_source_traits -- fills the SourceTrait, Study, and
        SourceEncodedValue tables with data from the source database

Requires the CNF_PATH setting from the specified settings module.
"""

# References:
# [python - Good ways to import data into Django - Stack Overflow](http://stackoverflow.com/questions/14504585/good-ways-to-import-data-into-django)
# [Providing initial data for models | Django documentation | Django](https://docs.djangoproject.com/en/1.8/howto/initial-data/)

from datetime import datetime
import socket

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings

import mysql.connector

from trait_browser.models import SourceTrait, SourceEncodedValue, Study


class Command(BaseCommand):
    """Management command to pull initial data from the source phenotype db."""

    help ='Populate the Study, SourceTrait, and EncodedValue models with a query to the source db'

    def _get_snuffles(self, test=True, cnf_path=settings.CNF_PATH):
        """Get a connection to the source phenotype db.
        
        Arguments:
            test -- boolean; whether to connect to a test db or not
            cnf_path -- string; path to the mySQL config file with db connection
                settings
        
        Returns:
            a mysql.connector open db connection
        """
        if test:
            test_string = '_test'
        else:
            test_string = '_production'
        cnf_group = ['client', 'mysql_topmed_readonly' + test_string]
        cnx = mysql.connector.connect(option_files=cnf_path, option_groups=cnf_group, charset='latin1', use_unicode=False)
        # TODO add a try/except block here in case the db connection fails.
        return cnx
    
    def _fix_bytearray(self, row_dict):
        """Convert byteArrays into decoded strings.
            
        mysql.connector returns all character data from a database as a
        bytearray python type. This is because of the different ways that python2
        and python3 handle strings and they didn't want to have to maintain
        separate code for the different python versions. This function takes a
        row of data from a database connection and converts all of the bytearray
        objects into strings by decoding the bytearrays with utf-8.
        
        Reference: https://dev.mysql.com/doc/relnotes/connector-python/en/news-2-0-0.html
        
        Arguments:
            row_dict -- a dictionary for one row of data, obtained from
                cursor.fetchone or iterating over cursor.fetchall (where the
                connection for the cursor has dictionary=True)

        Returns:
            a dictionary with identical values to row_dict, where all bytearrays
            are now string type
        """
        fixed_row = {
            (k) : (row_dict[k].decode('utf-8')
            if isinstance(row_dict[k], bytearray)
            else row_dict[k]) for k in row_dict
        }
        return fixed_row
    
    def _fix_null(self, row_dict):
        """Convert None values (NULL in the db) to empty strings.
        
        mysql.connector returns all NULL values from a database as None. However,
        Django stores NULL values as empty strings. This function converts results
        from a database call containing None to have empty strings instead.
        
        Arguments:
            row_dict -- a dictionary for one row of data, obtained from
                cursor.fetchone or iterating over cursor.fetchall (where the
                connection for the cursor has dictionary=True)
        
        Returns:
            a dictionary with identical values to row_dict, where all Nones have
            been replaced with empty strings
        """
        fixed_row = {
            (k) : ('' if row_dict[k] is None
            else row_dict[k]) for k in row_dict
        }
        return fixed_row
    
    def _fix_timezone(self, row_dict):
        """Add timezone awareness to datetime objects.
        
        mysql.connector appropriately returns date and time type values from a
        database as datetime type. However, these datetime objects are not
        connected to the current timezone setting of the Django site. This function
        adds timezone settings to each datetime object in a row of data
        retrieved from a database.
        
        Arguments:
            row_dict -- a dictionary for one row of data, obtained from
                cursor.fetchone or iterating over cursor.fetchall (where the
                connection for the cursor has dictionary=True)
        Returns:
            a dictionary with identical values to row_dict, where all datetime
            objects are now timezone aware
        """
        fixed_row = {
            (k) : (timezone.make_aware(row_dict[k], timezone.get_current_timezone())
            if isinstance(row_dict[k], datetime)
            else row_dict[k]) for k in row_dict
        }
        return fixed_row

    def _make_study_args(self, row_dict):
        """Get args for making a Study object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a Study
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_StudyTrait_attribute: attribute_value) pairs
        """
        new_args = {
            'study_id': row_dict['study_id'],
            'dbgap_id': row_dict['dbgap_id'],
            'name': row_dict['study_name']
        }
        return new_args
    
    def _populate_studies(self, source_db):
        """Add study data to the website db models.
        
        This function pulls study information from the source db, converts it
        where necessary, and populates entries in the Study model of the
        trait_browser app. This will fill in the rows of the trait_browser_study
        table.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_query = 'SELECT * FROM study'
        cursor.execute(study_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            study_args = self._make_study_args(type_fixed_row)
            add_var = Study(**study_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added study', str(study_args['study_id']))))
        cursor.close()

    def _make_source_trait_args(self, row_dict):
        """Get args for making a SourceTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a SourceTrait object. If there's
        a schema change in the source db, this function
        may need to be modified.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        """
        study = Study.objects.get(study_id=row_dict['study_id'])
        phs_string = '%s.v%d.p%d' % (study.dbgap_id,
                                     row_dict['dbgap_study_version'],
                                     row_dict['dbgap_participant_set'])

        new_args = {
            'dcc_trait_id': row_dict['source_trait_id'],
            'name': row_dict['trait_name'],
            'description': row_dict['dcc_description'],
            'data_type': row_dict['data_type'],
            'unit': row_dict['dbgap_unit'],
            'study': study,
            'phs_string': phs_string,
            'phv_string': row_dict['dbgap_variable_id']
        }
        return new_args

    def _populate_source_traits(self, source_db):
        """Add source trait data to the website db models.
        
        This function pulls source trait data from the source db, converts it
        where necessary, and populates entries in the SourceTrait model of the
        trait_browser app. This will fill in the rows of the trait_browser_sourcetrait
        table.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_variable_metadata LIMIT 400;'
        cursor.execute(trait_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            model_args = self._make_source_trait_args(type_fixed_row)
            add_var = SourceTrait(**model_args)    # temp SourceTrait to add
            add_var.save()
            print(' '.join(('Added trait', str(model_args['dcc_trait_id']))))
        cursor.close()

    def _make_source_encoded_value_args(self, row_dict):
        """Get args for making a SourceEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        new_args = {
            'category': row_dict['category'],
            'value': row_dict['value'],
            'source_trait': SourceTrait.objects.get(dcc_trait_id = row_dict['source_trait_id'])
        }
        return new_args

    def _populate_encoded_values(self, source_db):
        """Add encoded value data to the website db models.
        
        This function pulls study information from the source db, converts it
        where necessary, and populates entries in the SourceEncodedValue model of
        the trait_browser app. This will fill in the trait_browser_sourceencodedvalue
        table.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_encoded_values LIMIT 400;'
        cursor.execute(trait_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            model_args = self._make_source_encoded_value_args(type_fixed_row)
            add_var = SourceEncodedValue(**model_args)    # temp SourceEncodedValue to add
            add_var.save()
            print(' '.join(('Added encoded value for', str(type_fixed_row['source_trait_id']))))
        cursor.close()

    def handle(self, *args, **options):
        """Handle the main functions of this management command.
        
        Get a connection to the source db, populate Study objects, populate
        SourceTrait objects, and finally populate SourceEncodedValue objects.
        Then close the connection to the db.
        
        Arguments:
            **args and **options are handled as per the superclass handling; these
            argument dicts will pass on command line options
        """
        snuffles_db = self._get_snuffles(test=True)
        self._populate_studies(snuffles_db)
        self._populate_source_traits(snuffles_db)
        self._populate_encoded_values(snuffles_db)
        snuffles_db.close()