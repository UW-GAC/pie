"""Management commands for the trait_browser app.

management commands added:
    import_new_source_traits -- fills the SourceTrait, Study, and
        SourceEncodedValue tables with data from the source database

Requires the CNF_PATH setting from the specified settings module.
"""

# References:
# [python - Good ways to import data into Django - Stack Overflow](http://stackoverflow.com/questions/14504585/good-ways-to-import-data-into-django)
# [Providing initial data for models | Django documentation | Django](https://docs.djangoproject.com/en/1.8/howto/initial-data/)

from datetime import datetime
import mysql.connector
import socket

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings

from trait_browser.models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class Command(BaseCommand):
    """Management command to pull initial data from the source phenotype db."""

    help ='Import_new the db models with a query to the source db (snuffles).'

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
    
    def _make_model_object_from_args(self, args, model, verbosity):
        """Make an instance of a model object using arguments.
        
        Arguments:
            args: dict of 'field_name': 'field_value' pairs, used to make a model object instance
            model: the model class to use to make a model object instance
        """
        obj = model(**args)
        obj.save()
        if verbosity == 3:
            print('Added {}'.format(obj))
    
    def _make_model_object_per_query_row(self, source_db, query, make_args, model, verbosity):
        """Make a model object instance from each row of a query's results.
        
        Arguments:
            source_db: a mysql.connector open db connection 
            query: str containing a query to send to the open db
            make_args: function to convert a db query result row to args for making a model object
            model: the model class to use to make a model object instance
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        cursor.execute(query)
        for row in cursor:
            args = make_args_function(row)
            self._make_model_object_from_args(args, model, verbosity=verbosity)
        cursor.close()
    
    def _make_query_for_new_rows(self, table_name, pk_name, old_pks, verbosity):
        """Make a query for new rows from the given table.
        
        Arguments:
            table_name: str name of the table in the source db
            pk_name: str name of the primary key column in the source db
            old_pks: list of str pk values that are already imported into the website db
        
        Returns:
            str query that will yield new source db rows that haven't been imported
            to the website db yet
        """
        query = 'SELECT * FROM {}'.format(table_name)
        if len(old_pks) > 0:
            query += ' WHERE {} NOT IN ({})'.format(pk_name, ','.join(old_pks))
        return query
    
    def _get_new_pks(self, old_pks, get_current_pks):
        """Get the list of primary keys that have been added to the website db.
        
        Arguments:
            old_pks: list of str primary key values that were already added to the website db
            get_current_pks: function that will return a str list of pks for this model/table
        
        Returns:
            list of str primary key values for new entries added to the website db
        """
        new_pks = list(set(get_current_pks()) - set(old_pks))
        return new_pks
    
    def _import_new_data(self, source_db, table_name, pk_name, model, make_args, get_current_pks, verbosity):
        """Import new data into the website db from the source db from a given table, into a given model.
        
        Arguments:
            source_db: a mysql.connector open db connection 
            table_name: str name of the table in the source db
            pk_name: str name of the primary key column in the source db
            model: the model class to use to make a model object instance
            make_args: function to convert a db query result row to args for making a model object
            get_current_pks: function that will return a str list of pks for this model/table
        """
        old_pks = get_current_pks()
        new_rows_query = self._make_query_for_new_rows(table_name, pk_name, old_pks, verbosity)
        self._make_model_object_per_query_row(source_db, new_rows_query, make_args, model, verbosity)
        new_pks = self._get_new_pks(old_pks, get_current_pks)
        return new_pks

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
    
    def _fix_row(self, row_dict):
        """Helper function to run all of the fixers."""
        return self._fix_timezone(self._fix_bytearray(self._fix_null(row_dict)))

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
    
    def _get_current_subcohorts(self):
        """Get a str list of i_id for Subcohorts currently in the django site db."""
        return [str(sc.i_id) for sc in Subcohort.objects.all()]

    def _get_current_source_trait_encoded_values(self):
        """Get a str list of i_id for source_trait_encoded_values currently in the django site db."""
        return [str(ev.i_id) for ev in SourceTraitEncodedValue.objects.all()]
    
    # Methods to make object-instantiating args from a row of the source db data.
    def _make_global_study_args(self, row_dict):
        """Get args for making a GlobalStudy object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a GlobalStudy
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_GlobalStudy_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
        new_args = {
            'i_id': row_dict['id'],
            'i_name': row_dict['name']
        }
        return new_args

    def _make_study_args(self, row_dict):
        """Get args for making a Study object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a Study
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_Study_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
        global_study = GlobalStudy.objects.get(i_id=row_dict['global_study_id'])
        new_args = {
            'global_study': global_study,
            'i_accession': row_dict['accession'],
            'i_study_name': row_dict['study_name']
        }
        return new_args
    
    def _make_source_study_version_args(self, row_dict):
        """Get args for making a SourceStudyVersion object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceStudyVersion object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceStudyVersion_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
        study = Study.objects.get(i_accession=row_dict['accession'])
        new_args = {
            'study': study,
            'i_id': row_dict['id'],
            'i_version': row_dict['version'],
            'i_participant_set': row_dict['participant_set'],
            'i_dbgap_date': row_dict['dbgap_date'],
            'i_is_deprecated': row_dict['is_deprecated'],
            'i_is_prerelease': row_dict['is_prerelease']
        }
        return new_args
    
    def _make_source_dataset_args(self, row_dict):
        """Get args for making a SourceDataset object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDataset object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceDataset_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
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
    
    def _make_source_trait_args(self, row_dict):
        """Get args for making a SourceTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a SourceTrait object. If there's
        a schema change in the source db, this function may need to be modified.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
        source_dataset = SourceDataset.objects.get(i_id=row_dict['dataset_id'])
        new_args = {
            'source_dataset': source_dataset,
            'i_trait_id': row_dict['source_trait_id'],
            'i_trait_name': row_dict['trait_name'],
            'i_description': row_dict['dcc_description'],
            'i_detected_type': row_dict['detected_type'],
            'i_dbgap_type': row_dict['dbgap_type'],
            'i_visit_number': row_dict['visit_number'],
            'i_dbgap_variable_accession': row_dict['dbgap_variable_accession'],
            'i_dbgap_variable_version': row_dict['dbgap_variable_version'],
            'i_dbgap_comment': row_dict['dbgap_comment'],
            'i_dbgap_unit': row_dict['dbgap_unit'],
            'i_n_records': row_dict['n_records'],
            'i_n_missing': row_dict['n_missing']
        }
        return new_args

    def _make_subcohort_args(self, row_dict):
        """Get args for making a Subcohort object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        Subcohort object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_Subcohort_attribute: attribute_value) pairs
        """
        row_dict = self._fix_row(row_dict)
        study = Study.objects.get(i_accession=row_dict['study_accession'])
        new_args = {
            'study': study,
            'i_id': row_dict['id'],
            'i_name': row_dict['name']
        }
        return new_args
    
    def _make_source_trait_encoded_value_args(self, row_dict):
        """Get args for making a SourceTraitEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        row_dict = self._fix_row(row_dict)
        source_trait = SourceTrait.objects.get(i_trait_id = row_dict['source_trait_id'])
        new_args = {
            'i_id': row_dict['id'],
            'i_category': row_dict['category'],
            'i_value': row_dict['value'],
            'source_trait': source_trait
        }
        return new_args

    # Methods to import new data from the source db into django.
    def _import_new_source_dataset_subcohorts(self, source_db, new_dataset_pks, verbosity):
        """Add subcohort-source_dataset link data to the website db models.
        
        This function pulls information on subcohorts linked with new source_datasets
        from the source db, converts it where necessary, and imports new subcohort links
        in the subcohorts attribute of the SourceDatasets model of the trait_browser
        app.         
        
        Arguments:
            source_db -- an open connection to the source database
            new_dataset_pks -- list of pks for source_datasets for which subcohort
                links should be added
        """
        # Note that subcohort links added to datasets that are already in the db
        # will be handled by the dataset update function, so here we only need to
        # worry about subcohort links for new source_datasets.
        cursor = source_db.cursor(buffered=True, dictionary=True)
        source_dataset_subcohorts_query = 'SELECT * FROM source_dataset_subcohorts'
        if len(new_dataset_pks) > 0:
            source_dataset_subcohorts_query += ' WHERE dataset_id IN ({})'.format(','.join(new_dataset_pks))
        cursor.execute(source_dataset_subcohorts_query)
        for row in cursor:
            type_fixed_row = self._fix_row(row)
            # Get the SourceDataset and Subcohort objects to link.
            source_dataset = SourceDataset.objects.get(i_id=type_fixed_row['dataset_id'])
            subcohort = Subcohort.objects.get(i_id=type_fixed_row['subcohort_id'])
            # Associate the Subcohort object with a SourceDataset object.
            source_dataset.subcohorts.add(subcohort)
            if verbosity == 3: print('Linked {} to {}'.format(subcohort, source_dataset))
        cursor.close()

    # Methods to actually do the management command.
    def add_arguments(self, parser):
        """Add custom command line arguments to this management command."""
        parser.add_argument('--which_db', action='store', type=str,
                            choices=['test', 'production'], default='test',
                            help='Which source database to connect to for retrieving source data.')
        parser.add_argument('--update-only', action='store_true',
                            help='Only update the db records that are already in the db, and do not add new ones.')

    def handle(self, *args, **options):
        """Handle the main functions of this management command.
        
        Get a connection to the source db, import_new Study objects, import_new
        SourceTrait objects, and finally import_new SourceEncodedValue objects.
        Then close the connection to the db.
        
        Arguments:
            **args and **options are handled as per the superclass handling; these
            argument dicts will pass on command line options
        """
        source_db = self._get_source_db(which_db=options['which_db'])
        new_global_study_pks = self._import_new_data(source_db=source_db,
                                                     table_name='global_study',
                                                     pk_name='id',
                                                     model=GlobalStudy,
                                                     make_args=self._make_global_study_args,
                                                     get_current_pks=self._get_current_global_studies,
                                                     verbosity=options['verbosity'])
        print("Added global studies")
        new_study_pks = self._import_new_data(source_db=source_db,
                                              table_name='study',
                                              pk_name='accession',
                                              model=Study,
                                              make_args=self._make_study_args,
                                              get_current_pks=self._get_current_studies,
                                              verbosity=options['verbosity'])
        print("Added studies")
        new_source_study_version_pks = self._import_new_data(source_db=source_db,
                                                             table_name='source_study_version',
                                                             pk_name='id',
                                                             model=SourceStudyVersion,
                                                             make_args=self._make_source_study_version_args,
                                                             get_current_pks=self._get_current_source_study_versions,
                                                             verbosity=options['verbosity'])
        print("Added source study versions")
        new_source_dataset_pks = self._import_new_data(source_db=source_db,
                                                       table_name='source_dataset',
                                                       pk_name='id',
                                                       model=SourceDataset,
                                                       make_args=self._make_source_dataset_args,
                                                       get_current_pks=self._get_current_source_datasets,
                                                       verbosity=options['verbosity'])
        print("Added source datasets")
        new_source_trait_pks = self._import_new_data(source_db=source_db,
                                                     table_name='source_trait',
                                                     pk_name='source_trait_id',
                                                     model=SourceTrait,
                                                     make_args=self._make_source_trait_args,
                                                     get_current_pks=self._get_current_source_traits,
                                                     verbosity=options['verbosity'])
        print("Added source traits")
        new_subcohort_pks = self._import_new_data(source_db=source_db,
                                                  table_name='subcohort',
                                                  pk_name='id',
                                                  model=Subcohort,
                                                  make_args=self._make_subcohort_args,
                                                  get_current_pks=self._get_current_subcohorts,
                                                  verbosity=options['verbosity'])
        print("Added subcohorts")
        new_source_trait_encoded_value_pks = self._import_new_data(source_db=source_db,
                                                             table_name='source_trait_encoded_values',
                                                             pk_name='id',
                                                             model=SourceTraitEncodedValue,
                                                             make_args=self._make_source_trait_encoded_value_args,
                                                             get_current_pks=self._get_current_source_trait_encoded_values,
                                                             verbosity=options['verbosity'])
        print("Added source trait encoded values")

        self._import_new_source_dataset_subcohorts(source_db, new_source_dataset_pks, verbosity=options['verbosity'])
        print("Added source dataset subcohorts")

        source_db.close()