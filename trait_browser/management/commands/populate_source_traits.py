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

from .models import (GlobalStudy, Study, SourceStudyVersion, Subcohort,
                     SourceDataset, SourceDatasetSubcohorts, SourceDatasetUniqueKeys, 
                     SourceTrait, SourceTraitEncodedValue )


class Command(BaseCommand):
    """Management command to pull initial data from the source phenotype db."""

    help ='Populate the db models with a query to the source db (snuffles).'

    def _get_source_db(self, which_db, cnf_path=settings.CNF_PATH):
        """Get a connection to the source phenotype db.
        
        Arguments:
            test -- boolean; whether to connect to a test db or not
            cnf_path -- string; path to the mySQL config file with db connection
                settings
        
        Returns:
            a mysql.connector open db connection
        """
        if which_db == 'test':
            test_string = '_test'
        elif which_db == 'production':
            test_string = '_production'
        cnf_group = ['client', 'mysql_topmed_readonly' + test_string]
        cnx = mysql.connector.connect(option_files=cnf_path, option_groups=cnf_group, charset='latin1', use_unicode=False)
        # TODO add a try/except block here in case the db connection fails.
        return cnx
    
    # Helper methods for data munging.
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

    # Methods to find out which objects are already in the db.
    def _get_current_global_studies(self):
        """Get a str list of i_id for GlobalStudies currently in the django site db."""
        return [str(gstudy.i_id) for gstudy in GlobalStudy.objects.all()]

    def _get_current_studies(self):
        """Get a str list of i_accession for Studies currently in the django site db."""
        return [str(study.i_accession) for study in Study.objects.all()]
    
    def _get_current_source_study_versions(self):
        """Get a str list of i_id for SourceStudyVersions currently in the django site db."""
        return [str(study_version.i_id) for study_version in SourceStudyVersion.objects.all()]
    
    def _get_current_datasets(self):
        """Get a str list of i_id for SourceDatasets currently in the django site db."""
        return [str(dataset.i_id) for dataset in SourceDataset.objects.all()]
        
    def _get_current_traits(self):
        """Get a str list of i_trait_id for SourceTraits currently in the django site db."""
        return [str(trait.i_trait_id) for trait in SourceTrait.objects.all()]

    # Methods to fill in django db objects from the source db.
    def _make_global_study_args(self, row_dict):
        """Get args for making a GlobalStudy object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a GlobalStudy
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_Study_attribute: attribute_value) pairs
        """
        new_args = {
            'i_id': row_dict['id'],
            'i_name': row_dict['name']
        }
        return new_args

    def _populate_global_studies(self, source_db, n_studies):
        """Add global study data to the website db models.
        
        This function pulls GlobalStudy information from the source db, converts it
        where necessary, and populates entries in the GlobalStudy model of the
        trait_browser app. This will fill in the rows of the
        trait_browser_global_study table.
        
        If the n_studies argument is set at the command line, that is the maximum
        number of global studies that will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of global studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        global_study_query = 'SELECT * FROM global_study'
        # Add a limit statement if n_studies is set.
        if n_studies is not None:
            global_study_query += ' LIMIT {}'.format(n_studies)
        cursor.execute(global_study_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            global_study_args = self._make_global_study_args(type_fixed_row)
            add_var = GlobalStudy(**global_study_args)    # temp GlobalStudy to add
            add_var.save()
            print(' '.join(('Added global_study', str(global_study_args['global_study_id']))))
        cursor.close()

    def _make_study_args(self, row_dict):
        """Get args for making a Study object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a Study
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_Study_attribute: attribute_value) pairs
        """
        new_args = {
            'i_accession': row_dict['accession'],
            'global_study_id': row_dict['global_study'],
            'i_study_name': row_dict['study_name']
        }
        return new_args
    
    def _populate_studies(self, source_db, n_studies):
        """Add study data to the website db models.
        
        This function pulls study information from the source db, converts it
        where necessary, and populates entries in the Study model of the
        trait_browser app. This will fill in the rows of the trait_browser_study
        table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_query = 'SELECT * FROM study'
        # Add a limit statement if n_studies is set.
        if n_studies is not None:
            study_query += ' LIMIT {}'.format(n_studies)
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

        new_args = {
            'dcc_trait_id': row_dict['source_trait_id'],
            'name': row_dict['trait_name'],
            'description': row_dict['dcc_description'],
            'data_type': row_dict['data_type'],
            'unit': row_dict['dbgap_unit'],
            'study': study,
            'phv': int(row_dict['dbgap_variable_id'].replace('phv', '')),
            'pht': int(row_dict['dbgap_dataset_id'].replace('pht', '')),
            'study_version': row_dict['dbgap_study_version'],
            'dataset_version': row_dict['dbgap_dataset_version'],
            'variable_version': row_dict['dbgap_variable_version'],
            'participant_set': row_dict['dbgap_participant_set'],
        }
        return new_args

    def _populate_source_traits(self, source_db, n_traits):
        """Add source trait data to the website db models.
        
        This function pulls source trait data from the source db, converts it
        where necessary, and populates entries in the SourceTrait model of the
        trait_browser app. This will fill in the rows of the trait_browser_sourcetrait
        table.
        
        This function retrieves only those SourceTraits whose study_id foreign key
        is already loaded into the django site db. If the n_traits argument is set
        at the command line, a maximum of n_traits trait records will be retrieved
        from the source db. This necessitates running a separate query for each
        study id. In contrast, if n_traits is not set, only one query will be run.
        
        Arguments:
            source_db -- an open connection to the source database
            n_traits -- maximum number of traits to retrieve for each study
                found in the site db
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_ids = self._get_current_studies()    # list of string study ids
        # If there's a per-study trait limit, loop over studies with a LIMIT statement.
        if n_traits is not None:
            for pk in study_ids:
                trait_query = "SELECT * FROM source_variable_metadata WHERE study_id={} LIMIT {}".format(pk, n_traits)
                cursor.execute(trait_query)
                for row in cursor:
                    type_fixed_row = self._fix_bytearray(self._fix_null(row))
                    model_args = self._make_source_trait_args(type_fixed_row)
                    add_var = SourceTrait(**model_args)    # temp SourceTrait to add
                    add_var.save()
                    print(' '.join(('Added trait', str(model_args['dcc_trait_id']))))
        # Without n_traits, you can pull out all studies at once.
        else:
            study_ids = ','.join(study_ids)    # csv study_id string
            trait_query = 'SELECT * FROM source_variable_metadata WHERE study_id IN ({})'.format(study_ids)
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
        table. Only encoded values for the traits already present in the django
        site db are retrieved from the source db.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # Only retrieve the values for SourceTraits that were retrieved already.
        current_traits = self._get_current_traits()
        trait_query = 'SELECT * FROM source_encoded_values WHERE source_trait_id IN ({})'.format(','.join(current_traits))
        # TODO: The IN clause of this SQL query might need to be changed later if
        # the number of traits in the db gets too high.
        cursor.execute(trait_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            model_args = self._make_source_encoded_value_args(type_fixed_row)
            add_var = SourceEncodedValue(**model_args)    # temp SourceEncodedValue to add
            add_var.save()
            print(' '.join(('Added encoded value for', str(type_fixed_row['source_trait_id']))))
        cursor.close()

    def add_arguments(self, parser):
        """Add custom command line arguments to this management command."""
        parser.add_argument('--n_studies', action='store', type=int,
                            help='Maximum number of studies to import from source_db.')
        parser.add_argument('--max_traits', action='store', type=int,
                            help='Maximum number of traits to import FOR EACH STUDY VERSION.')
        parser.add_argument('--max_study_versions', action='store', type=int,
                            help='Maximum number of versions to import for each study.')
        parser.add_argument('--which_db', action='store', type=str,
                            choices=['test', 'production'], default='test',
                            help='Which source database to connect to for retrieving source data.')
        parser.add_argument('--only_update_existing', action='store_true', type=bool,
                            help='Only update the db records that are already in the db, and do not add new ones.')

    def handle(self, *args, **options):
        """Handle the main functions of this management command.
        
        Get a connection to the source db, populate Study objects, populate
        SourceTrait objects, and finally populate SourceEncodedValue objects.
        Then close the connection to the db.
        
        Arguments:
            **args and **options are handled as per the superclass handling; these
            argument dicts will pass on command line options
        """
        source_db_db = self._get_source_db(which_db=options['which_db'])
        
        self._populate_global_studies(source_db_db, options['n_studies'])
        self._populate_studies(source_db_db)
        self._populate_source_study_versions(source_db_db)
        self._populate_source_datasets(source_db_db)
        self._populate_source_traits(source_db_db, options['n_traits'])
        self._populate_source_trait_encoded_values(source_db_db)
        self._populate_source_dataset_unique_keys(source_db_db)
        self._populate_subcohorts(source_db_db)
        self._populate_source_dataset_subcohorts(source_db_db)
        
        source_db_db.close()