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

    help ='Import the db models with a query to the source db (snuffles).'

    def _get_source_db(self, which_db, cnf_path=settings.CNF_PATH):
        """Get a connection to the source phenotype db.
        
        Arguments:
            which_db -- string; name of the type of db to connect to (production,
                devel, or test)
            cnf_path -- string; path to the mySQL config file with db connection
                settings
        
        Returns:
            a mysql.connector open db connection
        """
        if which_db is None:
            raise ValueError('which_db as passed to _get_source_db MUST be set to a valid value ({} is not valid)'.format(which_db))
        # ALWAYS connect to the db as the read-only user
        cnf_group = ['client', 'mysql_topmed_pheno_readonly' + '_{}'.format(which_db)]
        cnx = mysql.connector.connect(option_files=cnf_path, option_groups=cnf_group, charset='latin1', use_unicode=False)
        # TODO add a try/except block here in case the db connection fails.
        return cnx
    
    # Helper methods for importing data from the source db.
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
            args = make_args(self._fix_row(row))
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
    
    def _get_new_pks(self, model, old_pks):
        """Get the list of primary keys that have been added to the website db.
        
        Arguments:
            old_pks: list of str primary key values that were already added to the website db
            get_current_pks: function that will return a str list of pks for this model/table
        
        Returns:
            list of str primary key values for new entries added to the website db
        """
        new_pks = list(set(self._get_current_pks(model)) - set(old_pks))
        return new_pks
    
    def _import_new_data(self, source_db, table_name, pk_name, model, make_args, verbosity):
        """Import new data into the website db from the source db from a given table, into a given model.
        
        Arguments:
            source_db: a mysql.connector open db connection 
            table_name: str name of the table in the source db
            pk_name: str name of the primary key column in the source db
            model: the model class to use to make a model object instance
            make_args: function to convert a db query result row to args for making a model object
            get_current_pks: function that will return a str list of pks for this model/table
        """
        old_pks = self._get_current_pks(model)
        new_rows_query = self._make_query_for_new_rows(table_name, pk_name, old_pks, verbosity)
        self._make_model_object_per_query_row(source_db, new_rows_query, make_args, model, verbosity)
        new_pks = self._get_new_pks(model, old_pks)
        return new_pks
    
    def _make_args_mapping(self, row_dict, source_field_names, source_field_names_to_map=None, foreign_key_mapping=None):
        """Make a dict that maps source db data to django model fields.
        
        Arguments:
            row_dict: dict of source_db_field_name: source_db_field_value_in_one_row pairs
            source_field_names: list of str field names from source db, which will have 'i_'
                prepended to them to make Django model field names for args dict
            source_field_names_to_map: dict of source_db_field_name: django_model_field_name
                pairs for source db fields that require more complicated mapping than adding 'i_'
            foreign_key_mapping: dict of source_db_foreign_key_field_name: django_foreign_key_model
                pairs, used to Model.objects.get() the object to link in the args
        
        Returns:
            dict of django_model_field_name: field_value pairs to be used in constructing
            a model object instance; use in model(**kwargs) statement
        """
        args_mapping = {}
        for source_name in source_field_names:
            args_mapping['i_' + source_name] = row_dict[source_name]
        if source_field_names_to_map is not None:
            for name_to_map in source_field_names_to_map:
                args_mapping[source_field_names_to_map[name_to_map]] = row_dict[name_to_map]
        if foreign_key_mapping is not None:
            for source_pk_name in foreign_key_mapping:
                mod = foreign_key_mapping[source_pk_name]
                args_mapping[mod._meta.verbose_name.replace(' ', '_')] = mod.objects.get(pk=row_dict[source_pk_name])
        return args_mapping
        
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
    def _get_current_pks(self, model):
        """Get a list of str pk values for the given model."""
        return [str(obj.pk) for obj in model.objects.all()]
    
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
        return self._make_args_mapping(row_dict, ['id', 'name'])

    def _make_study_args(self, row_dict):
        """Get args for making a Study object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a Study
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Returns:
            a dict of (required_Study_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict, ['accession', 'study_name'], foreign_key_mapping={'global_study_id': GlobalStudy})
    
    def _make_source_study_version_args(self, row_dict):
        """Get args for making a SourceStudyVersion object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceStudyVersion object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceStudyVersion_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'version', 'participant_set', 'dbgap_date', 'is_deprecated', 'is_prerelease'],
                                       foreign_key_mapping={'accession':Study})
    
    def _make_source_dataset_args(self, row_dict):
        """Get args for making a SourceDataset object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDataset object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_SourceDataset_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'accession', 'dbgap_description', 'dcc_description', 'is_medication_dataset',
                                        'is_subject_file','study_subject_column', 'version', 'visit_code', 'visit_number'],
                                       foreign_key_mapping={'study_version_id':SourceStudyVersion})

    def _make_harmonized_trait_set_args(self, row_dict):
        """Get args for making a HarmonizedTraitSet object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        HarmonizedTraitSet object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_HarmonizedTraitSet_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'trait_set_name', 'version', 'flavor', 'description'])
    
    def _make_source_trait_args(self, row_dict):
        """Get args for making a SourceTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a SourceTrait object. If there's
        a schema change in the source db, this function may need to be modified.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['trait_name', 'detected_type', 'dbgap_type', 'visit_number', 'dbgap_variable_accession',
                                        'dbgap_variable_version', 'dbgap_comment', 'dbgap_unit', 'n_records', 'n_missing'],
                                       source_field_names_to_map={'source_trait_id':'i_trait_id', 'dcc_description':'i_description'},
                                       foreign_key_mapping={'dataset_id': SourceDataset})

    def _make_subcohort_args(self, row_dict):
        """Get args for making a Subcohort object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        Subcohort object. If there is a schema change in the source db,
        this function may need to be modified.

        Returns:
            a dict of (required_Subcohort_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict, ['id', 'name'], foreign_key_mapping={'study_accession':Study})
    
    def _make_source_trait_encoded_value_args(self, row_dict):
        """Get args for making a SourceTraitEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.
        
        Arguments:
            source_db -- an open connection to the source database
        """
        return self._make_args_mapping(row_dict, ['id', 'category', 'value'],
                                       foreign_key_mapping={'source_trait_id':SourceTrait})

    def _make_harmonized_trait_args(self, row_dict):
        """Get args for making a HarmonizedTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a HarmonizedTrait object. If there's
        a schema change in the source db, this function may need to be modified.
        
        Returns:
            a dict of (required_HarmonizedTrait_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['description', 'data_type', 'unit', 'is_unique_key'],
                                       source_field_names_to_map={'harmonized_trait_id':'i_trait_id'},
                                       foreign_key_mapping={'harmonized_trait_set_id': HarmonizedTraitSet})




    # Methods for importing data for models that require special processing.
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
                            choices=['test', 'devel', 'production'], default=None, required=True,
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
                                                     verbosity=options['verbosity'])
        print("Added global studies")
        new_study_pks = self._import_new_data(source_db=source_db,
                                              table_name='study',
                                              pk_name='accession',
                                              model=Study,
                                              make_args=self._make_study_args,
                                              verbosity=options['verbosity'])
        print("Added studies")
        new_source_study_version_pks = self._import_new_data(source_db=source_db,
                                                             table_name='source_study_version',
                                                             pk_name='id',
                                                             model=SourceStudyVersion,
                                                             make_args=self._make_source_study_version_args,
                                                             verbosity=options['verbosity'])
        print("Added source study versions")
        new_source_dataset_pks = self._import_new_data(source_db=source_db,
                                                       table_name='source_dataset',
                                                       pk_name='id',
                                                       model=SourceDataset,
                                                       make_args=self._make_source_dataset_args,
                                                       verbosity=options['verbosity'])
        print("Added source datasets")
        new_source_trait_pks = self._import_new_data(source_db=source_db,
                                                     table_name='source_trait',
                                                     pk_name='source_trait_id',
                                                     model=SourceTrait,
                                                     make_args=self._make_source_trait_args,
                                                     verbosity=options['verbosity'])
        print("Added source traits")
        new_subcohort_pks = self._import_new_data(source_db=source_db,
                                                  table_name='subcohort',
                                                  pk_name='id',
                                                  model=Subcohort,
                                                  make_args=self._make_subcohort_args,
                                                  verbosity=options['verbosity'])
        print("Added subcohorts")
        new_source_trait_encoded_value_pks = self._import_new_data(source_db=source_db,
                                                             table_name='source_trait_encoded_values',
                                                             pk_name='id',
                                                             model=SourceTraitEncodedValue,
                                                             make_args=self._make_source_trait_encoded_value_args,
                                                             verbosity=options['verbosity'])
        print("Added source trait encoded values")

        self._import_new_source_dataset_subcohorts(source_db, new_source_dataset_pks, verbosity=options['verbosity'])
        print("Added source dataset subcohorts")

        source_db.close()