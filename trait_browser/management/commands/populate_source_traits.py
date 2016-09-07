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
            (k): (row_dict[k].decode('utf-8')
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
            (k): ('' if row_dict[k] is None
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
            (k): (timezone.make_aware(row_dict[k], timezone.get_current_timezone())
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
    
    def _get_current_source_datasets(self):
        """Get a str list of i_id for SourceDatasets currently in the django site db."""
        return [str(dataset.i_id) for dataset in SourceDataset.objects.all()]
        
    def _get_current_source_traits(self):
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
            a dict of (required_GlobalStudy_attribute: attribute_value) pairs
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
        trait_browser_globalstudy table.
        
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
        global_study = GlobalStudy.objects.get(i_id=row_dict['global_study_id'])
        new_args = {
            'global_study': global_study,
            'i_accession': row_dict['accession'],
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
        # If n_studies is set, filter the list of studies to import.
        study_query = 'SELECT * FROM study'
        if n_studies is not None:
            loaded_global_studies = self._get_current_global_studies()
            study_query += ' WHERE global_study_id IN ({})'.format(','.join(loaded_global_studies))
        cursor.execute(study_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            study_args = self._make_study_args(type_fixed_row)
            add_var = Study(**study_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added study', str(study_args['study_id']))))
        cursor.close()

    def _make_source_study_version_args(self, row_dict):
        """Get args for making a SourceStudyVersion object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceStudyVersion object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceStudyVersion_attribute: attribute_value) pairs
        """
        study = Study.objects.get(i_accession=row_dict['accession'])
        new_args = {
            'study': study,
            'i_id': row_dict['id'],
            'i_accession': row_dict['accession'],
            'i_version': row_dict['version'],
            'i_participant_set': row_dict['participant_set'],
            'i_dbgap_date': row_dict['dbgap_date'],
            'i_is_deprecated': row_dict['is_deprecated'],
            'i_is_prerelease': row_dict['is_prerelease']
        }
        return new_args
    
    def _populate_source_study_versions(self, source_db, n_studies):
        """Add source study version data to the website db models.
        
        This function pulls source study version information from the source db,
        converts it where necessary, and populates entries in the SourceStudyVersion
        model of the trait_browser app. This will fill in the rows of the
        trait_browser_sourcestudyversion table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # If n_studies is set, filter the list of studies to import.
        source_study_version_query = 'SELECT * FROM source_study_version'
        if n_studies is not None:
            loaded_studies = self._get_current_studies()
            source_study_version_query += ' WHERE accession IN ({})'.format(','.join(loaded_studies))
        cursor.execute(source_study_version_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            source_study_version_args = self._make_source_study_version_args(type_fixed_row)
            add_var = SourceStudyVersion(**source_study_version_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added source_study_version', str(source_study_version_args['source_study_version_id']))))
        cursor.close()

    def _make_source_dataset_args(self, row_dict):
        """Get args for making a SourceDataset object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDataset object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceDataset_attribute: attribute_value) pairs
        """
        source_study_version = SourceStudyVersion.objects.get(i_id=row_dict['study_version_id'])
        new_args = {
            'source_study_version': source_study_version,
            'i_id': row_dict['id'],
            'i_accession': row_dict['accession'],
            'i_dbgap_description': row_dict['dbgap_description'],
            'i_dcc_description': row_dict['dcc_description'],
            'i_is_medication_dataset': row_dict['is_medication_dataset'],
            'i_is_subject_file': row_dict['is_subject_file'],
            'i_study_subject_column': row_dict['study_subject_column'],
            'i_version': row_dict['version'],
            'i_visit_code': row_dict['visit_code'],
            'i_visit_number': row_dict['visit_number']
        }
        return new_args
    
    def _populate_source_datasets(self, source_db, n_studies, ):
        """Add source study version data to the website db models.
        
        This function pulls source study version information from the source db,
        converts it where necessary, and populates entries in the SourceDataset
        model of the trait_browser app. This will fill in the rows of the
        trait_browser_sourcestudyversion table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # If n_studies is set, filter the list of studies to import.
        source_dataset_query = 'SELECT * FROM source_dataset'
        if n_studies is not None:
            loaded_studies = self._get_current_studies()
            source_dataset_query += ' WHERE accession IN ({})'.format(','.join(loaded_studies))
        cursor.execute(source_dataset_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            source_dataset_args = self._make_source_dataset_args(type_fixed_row)
            add_var = SourceDataset(**source_dataset_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added source_dataset', str(source_dataset_args['source_dataset_id']))))
        cursor.close()

    def _make_source_trait_args(self, row_dict):
        """Get args for making a SourceTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a SourceTrait object. If there's
        a schema change in the source db, this function may need to be modified.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        """
        source_dataset = SourceDataset.objects.get(i_id=row_dict['dataset_id'])

        new_args = {
            'source_dataset': source_dataset,
            'i_trait_id': row_dict['source_trait_id'],
            'i_trait_name': row_dict['trait_name'],
            'i_description': row_dict['dcc_description'],
            'i_detected_type': row_dict['detected_type'],
            'i_dbgap_type': row_dict['dbgap_type'],
            'i_visit_number': row_dict['visit_number'],
            'i_dataset_id': row_dict['dataset_id'],
            'i_dbgap_variable_accession': row_dict['dbgap_variable_accession'],
            'i_dbgap_variable_version': row_dict['dbgap_variable_version'],
            'i_dbgap_comment': row_dict['dbgap_comment'],
            'i_dbgap_unit': row_dict['dbgap_unit'],
            'i_dbgap_min': row_dict['dbgap_min'],
            'i_dbgap_max': row_dict['dbgap_max'],
            'i_n_records': row_dict['n_records'],
            'i_n_missing': row_dict['n_missing']
        }
        return new_args

    def _populate_source_traits(self, source_db, max_traits, n_studies):
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
            max_traits -- maximum number of traits to retrieve for each study version
            n_studies -- number of global studies to retrieve from the database
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_trait'
        # If max_traits is set, loop through by study version.
        if max_traits is not None:
            loaded_source_study_versions = self._get_current_source_study_versions ()    # list of string study version ids
            for source_study_version_id in loaded_source_study_versions:    # Already filters if n_studies is set.
                datasets_in_version = [str(dataset.i_id) for dataset in SourceDataset.objects.filter(source_study_version__i_id=source_study_version_id).order_by('id')]
                this_query = trait_query + ' WHERE dataset_id IN ({}) LIMIT {}'.format(','.join(datasets_in_version), max_traits)
                cursor.execute(this_query)
                for row in cursor:
                    type_fixed_row = self._fix_bytearray(self._fix_null(row))
                    model_args = self._make_source_trait_args(type_fixed_row)
                    add_var = SourceTrait(**model_args)    # temp SourceTrait to add
                    add_var.save()
                    print(' '.join(('Added source_trait', str(model_args['i_trait_id']))))
        # Otherwise, you can pull out all studies at once.
        else:
            # If n_studies is set, filter the list of traits to those connected to already-loaded datasets.
            if n_studies is not None:
                loaded_source_datasets = self._get_current_source_datasets()    # list of string dataset ids
                trait_query += ' WHERE dataset_id IN ({})'.format(','.join(loaded_source_datasets))
            cursor.execute(trait_query)
            for row in cursor:
                type_fixed_row = self._fix_bytearray(self._fix_null(row))
                model_args = self._make_source_trait_args(type_fixed_row)
                add_var = SourceTrait(**model_args)    # temp SourceTrait to add
                add_var.save()
                print(' '.join(('Added source_trait', str(model_args['i_trait_id']))))
        cursor.close()

    def _make_source_dataset_unique_keys_args(self, row_dict):
        """Get args for making a SourceDatasetUniqueKeys object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDatasetUniqueKeys object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceDatasetUniqueKeys_attribute: attribute_value) pairs
        """
        source_dataset = SourceDataset.objects.get(i_id=row_dict['dataset_id'])
        source_trait = SourceTrait.objects.get(i_trait_id=row_dict['source_trait_id'])
        new_args = {
            'i_id': row_dict['id'],
            'i_is_visit_column': row_dict['is_visit_column'],
        }
        return new_args
    
    def _populate_source_dataset_unique_keys(self, source_db, max_traits, n_studies):
        """Add source study version data to the website db models.
        
        This function pulls source study version information from the source db,
        converts it where necessary, and populates entries in the SourceDatasetUniqueKeys
        model of the trait_browser app. This will fill in the rows of the
        trait_browser_sourcestudyversion table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            max_traits -- maximum number of traits to retrieve for each study version
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # If n_studies OR max_studies is set, filter the list of unique_keys to import.
        source_dataset_unique_keys_query = 'SELECT * FROM source_dataset_unique_keys'
        if n_studies is not None or max_studies is not None:
            loaded_source_traits = self._get_current_source_traits()
            source_dataset_unique_keys_query += ' WHERE source_trait_id IN ({})'.format(','.join(loaded_source_traits))
        cursor.execute(source_dataset_unique_keys_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            source_dataset_unique_keys_args = self._make_source_dataset_unique_keys_args(type_fixed_row)
            add_var = SourceDatasetUniqueKeys(**source_dataset_unique_keys_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added source_dataset_unique_keys', str(source_dataset_unique_keys_args['source_dataset_unique_keys_id']))))
        cursor.close()

    def _make_subcohort_args(self, row_dict):
        """Get args for making a Subcohort object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        Subcohort object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_Subcohort_attribute: attribute_value) pairs
        """
        study = Study.objects.get(i_accession=row_dict['study_accession'])
        new_args = {
            'i_id': row_dict['id'],
            'i_name': row_dict['name']
        }
        return new_args
    
    def _populate_subcohorts(self, source_db, n_studies):
        """Add source study version data to the website db models.
        
        This function pulls source study version information from the source db,
        converts it where necessary, and populates entries in the Subcohort
        model of the trait_browser app. This will fill in the rows of the
        trait_browser_sourcestudyversion table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # If n_studies is set, filter the list of studies to import.
        subcohort_query = 'SELECT * FROM subcohort'
        if n_studies is not None:
            loaded_studies = self._get_current_studies()
            subcohort_query += ' WHERE study_accession IN ({})'.format(','.join(loaded_studies))
        cursor.execute(subcohort_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            subcohort_args = self._make_subcohort_args(type_fixed_row)
            add_var = Subcohort(**subcohort_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added subcohort', str(subcohort_args['subcohort_id']))))
        cursor.close()

    def _make_source_dataset_subcohorts_args(self, row_dict):
        """Get args for making a SourceDatasetSubcohorts object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDatasetSubcohorts object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceDatasetSubcohorts_attribute: attribute_value) pairs
        """
        source_dataset = SourceDataset.objects.get(i_id=row_dict['dataset_id'])
        subcohort = Subcohort.objects.get(i_id=row_dict['subcohort_id'])
        new_args = {
            'i_id': row_dict['id'],
        }
        return new_args
    
    def _populate_source_dataset_subcohorts(self, source_db, n_studies):
        """Add source study version data to the website db models.
        
        This function pulls source study version information from the source db,
        converts it where necessary, and populates entries in the SourceDatasetSubcohorts
        model of the trait_browser app. This will fill in the rows of the
        trait_browser_sourcestudyversion table.
        
        If the n_studies argument is set at the command line, a maximum of
        n_studies will be retrieved from the source database.
        
        Arguments:
            source_db -- an open connection to the source database
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        # If n_studies is set, filter the list of studies to import.
        source_dataset_subcohorts_query = 'SELECT * FROM source_dataset_subcohorts'
        if n_studies is not None:
            loaded_source_datasets = self._get_current_source_datasets()
            source_dataset_subcohorts_query += ' WHERE dataset_id IN ({})'.format(','.join(loaded_source_datasets))
        cursor.execute(source_dataset_subcohorts_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            source_dataset_subcohorts_args = self._make_source_dataset_subcohorts_args(type_fixed_row)
            add_var = SourceDatasetSubcohorts(**source_dataset_subcohorts_args)    # temp Study to add
            add_var.save()
            print(' '.join(('Added subcohort', str(subcohort_args['subcohort_id']))))
        cursor.close()

    def _make_source_trait_encoded_value_args(self, row_dict):
        """Get args for making a SourceTraitEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        source_trait = SourceTrait.objects.get(i_trait_id = row_dict['source_trait_id'])
        new_args = {
            'i_category': row_dict['category'],
            'i_value': row_dict['value'],
            'source_trait': source_trait
        }
        return new_args

    def _populate_encoded_values(self, source_db, max_traits, n_studies):
        """Add encoded value data to the website db models.
        
        This function pulls study information from the source db, converts it
        where necessary, and populates entries in the SourceTraitEncodedValue model of
        the trait_browser app. This will fill in the trait_browser_sourceencodedvalue
        table. Only encoded values for the traits already present in the django
        site db are retrieved from the source db.
        
        Arguments:
            source_db -- an open connection to the source database
            max_traits -- maximum number of traits to retrieve for each study version
            n_studies -- maximum number of studies to retrieve
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        source_trait_encoded_value_query = 'SELECT * FROM source_trait_encoded_values'
        if n_studies is not None or max_traits is not None:
            loaded_source_traits = self._get_current_source_traits
            source_trait_encoded_value_query += ' WHERE source_trait_id IN ({})'.format(','.join(loaded_source_traits))
        # NB: The IN clause of this SQL query might need to be changed later if the number of traits in the db gets too high.
        cursor.execute(source_trait_encoded_value_query)
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            model_args = self._make_source_trait_encoded_value_args(type_fixed_row)
            add_var = SourceTraitEncodedValue(**model_args)    # temp SourceTraitEncodedValue to add
            add_var.save()
            print(' '.join(('Added encoded value for', str(type_fixed_row['source_trait_id']))))
        cursor.close()

    # Methods to actually do the management command.
    def add_arguments(self, parser):
        """Add custom command line arguments to this management command."""
        parser.add_argument('--n_studies', action='store', type=int,
                            help='Number of global studies to import from source_db.')
        parser.add_argument('--max_traits', action='store', type=int,
                            help='Maximum number of traits to import FOR EACH STUDY VERSION.')
        # parser.add_argument('--max_study_versions', action='store', type=int,
        #                     help='Maximum number of versions to import for each study.')
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
        source_db = self._get_source_db(which_db=options['which_db'])
        
        self._populate_global_studies(source_db, options['n_studies'])
        self._populate_studies(source_db, options['n_studies'])
        self._populate_source_study_versions(source_db, options['n_studies'])
        self._populate_source_datasets(source_db, options['n_studies'])
        self._populate_source_traits(source_db, options['max_traits'], options['n_traits'])
        self._populate_source_dataset_unique_keys(source_db, options['max_traits'], options['n_traits'])
        self._populate_subcohorts(source_db, options['n_traits'])
        self._populate_source_dataset_subcohorts(source_db, options['n_traits'])
        self._populate_source_trait_encoded_values(source_db, options['max_traits'], options['n_traits'])
        
        source_db.close()