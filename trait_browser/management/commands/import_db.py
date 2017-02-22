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
import logging
import mysql.connector
import socket
from sys import stdout
import pytz

from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.utils import timezone
from django.conf import settings

from trait_browser.models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


# Set up a logger to handle messages based on verbosity setting.
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(stdout)
detail_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(detail_formatter)
logger.addHandler(console_handler)

class Command(BaseCommand):
    """Management command to pull data from the source phenotype db."""

    help ='Import/update data from the source db (topmed_pheno) into the Django models.'

    def _get_source_db(self, which_db, cnf_path=settings.CNF_PATH, permissions='readonly'):
        """Get a connection to the source phenotype db.
        
        Arguments:
            which_db -- string; name of the type of db to connect to (production,
                devel, or test)
            cnf_path -- string; path to the mySQL config file with db connection
                settings
            permissions -- string; 'readonly' or 'full'
        
        Returns:
            a mysql.connector open db connection
        """
        if which_db is None:
            raise ValueError('which_db as passed to _get_source_db MUST be set to a valid value ({} is not valid)'.format(which_db))
        if (which_db == 'test' or which_db == 'production') and (permissions == 'full'):
            raise ValueError('Requested full permissions for {} source database. Not allowed!!!')
        # Default is to connect as readonly; only test functions connect as full user.
        cnf_group = ['client', 'mysql_topmed_pheno_{}_{}'.format(permissions, which_db)]
        cnx = mysql.connector.connect(option_files=cnf_path, option_groups=cnf_group, charset='latin1', use_unicode=False, time_zone='+00:00')
        logger.debug('Connected to source db {}'.format(cnx))
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
            row_dict (dict): a dictionary for one row of data, obtained from
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
            row_dict (dict): a dictionary for one row of data, obtained from
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
            row_dict (dict): a dictionary for one row of data, obtained from
                cursor.fetchone or iterating over cursor.fetchall (where the
                connection for the cursor has dictionary=True)
        Returns:
            a dictionary with identical values to row_dict, where all datetime
            objects are now timezone aware
        """
        fixed_row = {
            # Datetimes from the db are already set to UTC, due to our db settings.
            (k): (timezone.make_aware(row_dict[k], pytz.utc) if isinstance(row_dict[k], datetime) else row_dict[k]) for k in row_dict
        }
        return fixed_row
    
    def _fix_row(self, row_dict):
        """Helper function to run all of the fixers."""
        return self._fix_timezone(self._fix_bytearray(self._fix_null(row_dict)))


    # Methods to find out which objects are already in the db.
    def _get_current_pks(self, model):
        """Get a list of str pk values for the given model.
        
        Arguments:
            model (class obj): The Django model to get a list of current pks for
        
        Returns:
            list of str: list of string primary key values
        """
        return [str(obj.pk) for obj in model.objects.all()]

    def _get_new_pks(self, model, old_pks):
        """Get the list of primary keys that have been added to the website db.
        
        Arguments:
            old_pks (list of str): list of str primary key values that were already added to the website db
            model (class obj): the model class to get a pk list from
        
        Returns:
            list of str primary key values for new entries added to the website db
        """
        new_pks = list(set(self._get_current_pks(model)) - set(old_pks))
        return new_pks
    

    # Helper methods for importing data from the source db.
    def _make_table_query(self, source_table, filter_field=None, filter_values=None, filter_not=None, **kwargs):
        """Make a query string for data from a source db table, with optional filters.
        
        Using the table name, make a string query for rows from the source db.
        Optionally allow IN and NOT IN filters based on the filter_field. This
        is a generalized query building method that is used by other, more specific
        query building methods.
        
        Arguments:
            source_table (str): name of the source db table to make a query for
            filter_field (str): name of the source db field to filter on
            filter_values (list of str): values to have in the filter clause
            filter_not (bool): should the filter be WHERE NOT IN? (if False, then WHERE IN)
        
        Returns:
            str: query for rows from source_table with appropriate filters
        """
        query = 'SELECT * FROM {}'.format(source_table)
        # Check to make sure that if any filter field is set, all of them are set.
        if (filter_field is not None) or (filter_values is not None) or (filter_not is not None):
            if not ((filter_field is not None) and (filter_values is not None) and (filter_not is not None)):
                raise ValueError('if any filter arguments are set, they must all be set')
            else:
                if filter_not:
                    not_string = 'NOT'
                else:
                    not_string = ''
                if len(filter_values) == 0:
                    value_string = "''"
                else:
                    value_string = ','.join(filter_values)
                filter_query = ' WHERE {} {} IN ({})'.format(filter_field, not_string, value_string)
                query += filter_query
        return query

    def _make_model_object_from_args(self, model_args, model, **kwargs):
        """Make an instance of a model object using arguments.
        
        Arguments:
            model_args (dict): dict of 'field_name': 'field_value' pairs, used to make a model object instance
            model (class obj): the model class to use to make a model object instance
        """
        obj = model(**model_args)
        obj.save()
        logger.debug('Created {}'.format(obj))

    def _make_model_object_per_query_row(self, source_db, query, make_args, **kwargs):
        """Make a model object instance from each row of a query's results.
        
        Arguments:
            source_db (MySQLConnection): a mysql.connector open db connection 
            query (str): a query to send to the open db
            make_args (function): function to convert a db query result row to args for making a model object
        """
        cursor = source_db.cursor(buffered=True, dictionary=True)
        cursor.execute(query)
        for row in cursor:
            model_args = make_args(self._fix_row(row))
            self._make_model_object_from_args(model_args=model_args, **kwargs)
        cursor.close()
    
    def _make_query_for_new_rows(self, source_table, source_pk, old_pks, **kwargs):
        """Make a query for new rows from the given table.
        
        Arguments:
            source_table (str): name of the table in the source db
            source_pk (str): name of the primary key column in the source db
            old_pks (list of str): pk values that are already imported into the website db
        
        Returns:
            str query that will yield new source db rows that haven't been imported
            to the website db yet
        """
        if len(old_pks) > 0:
            # If some rows of this table are already imported, make a query that will only return the new ones.
            return self._make_table_query(source_table=source_table, filter_field=source_pk, filter_values=old_pks, filter_not=True)
        else:
            # If none of the items from this table are already imported, make a query that will return the whole table.
            return self._make_table_query(source_table=source_table)

    def _make_args_mapping(self, row_dict, source_field_names, source_field_names_to_map=None, foreign_key_mapping=None):
        """Make a dict that maps source db data to django model fields.
        
        Arguments:
            row_dict (dict): source_db_field_name: source_db_field_value_in_one_row pairs
            source_field_names (list of str): field names from source db, which will have 'i_'
                prepended to them to make Django model field names for args dict
            source_field_names_to_map (dict): source_db_field_name: django_model_field_name
                pairs for source db fields that require more complicated mapping than adding 'i_'
            foreign_key_mapping (dict): source_db_foreign_key_field_name: django_foreign_key_model
                pairs, used with Model.objects.get() to get the object to link in the args
        
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

    def _import_new_data(self, **kwargs):
        """Import new data into the website db from the source db from a given table, into a given model.
        
        Query for the data that is already in the Django db. Then query the source db
        for data that has not yet been imported. Use helper functions to make Django
        model objects from the data retrieved by the query.
        
        Returns:
            list of str pk values that were imported to the Django db
        """
        model=kwargs['model']
        old_pks = self._get_current_pks(model)
        new_rows_query = self._make_query_for_new_rows(old_pks=old_pks, **kwargs)
        logger.debug(new_rows_query)
        self._make_model_object_per_query_row(query=new_rows_query, **kwargs)
        new_pks = self._get_new_pks(model=model, old_pks=old_pks)
        return new_pks
    

    # Helper methods for updating data that has been modified in the source db.
    def _make_query_for_rows_to_update(self, source_table, model, old_pks, source_pk, changed_greater, **kwargs):
        """Make a query for data that has been changed since the last update.
        
        Used by the _update methods to retrieve source db data that needs to be
        updated in the Django db. Also used by _update_m2m_field to retrieve
        source db data for new m2m links to create.
        
        Arguments:
            source_table (str): name of the table in the source db
            model (): 
            old_pks (list of str): pk values that are already imported into the website db
            source_pk (str): name of the primary key column in the source db
            changed_greater (bool): whether or not to include the (date_changed > date_added)
                condition; allows use of this method for m2m table queries as well
        
        Returns:
            str query that will yield old source db rows that haven't been imported
            to the website db yet
        """
        # print("Model {}, latest date {}".format(model._meta.object_name, latest_date))
        if len(old_pks) > 0:
            # Make a query for the rows that were already imported into Django.
            query = self._make_table_query(source_table=source_table, filter_field=source_pk, filter_values=old_pks, filter_not=False)
            # Add a where clause to find only those rows that have changed since the last import.
            latest_date = model.objects.latest('i_date_changed').i_date_changed
            latest_date = latest_date.strftime('%Y-%m-%d %H:%M:%S')
            if changed_greater:
                query += " AND (date_changed > date_added)"
            query += " AND (date_changed > '{}')".format(latest_date)
        else:
            # If none of the items from this table can be updated, make a query that will return an empty result set.
            query = self._make_table_query(source_table=source_table, filter_field=source_pk, filter_values=["''"], filter_not=False)
        return query

    def _update_model_object_from_args(self, model_args, model, expected, **kwargs):
        """Update an existing model object using arguments.
        
        Given a dict of updated arguments for the model, if an argument does not
        match the value in the Django db, save the new value to the Django db.
        
        Arguments:
            model_args (dict): 'field_name': 'field_value' pairs, used to update the model object instance
            model (class obj): the model class to use to make a model object instance
            expected (bool): whether or not updates are expected to happen in this 
                model; triggers warning printing
        
        Returns:
            bool; True if any fields were updated, False if not
        """
        model_pk_name = model._meta.pk.name
        obj = model.objects.get(pk=model_args[model_pk_name])
        ## Originally intended to have a check here that date_changed (source db) > modified (web db)
        ## but that's probably redundant based on the query in make_query_for_rows_to_update
        # Update any fields that are different
        updates = 0
        for field_name in model_args:
            old_val = getattr(obj, field_name)
            new_val = model_args[field_name]
            if old_val != new_val:
                updates += 0
                setattr(obj, field_name, new_val)
                obj.save()
                update_message = '{} {} field changed from {} to {}'.format(obj, field_name, old_val, new_val)
                if not expected:
                    logger.warning('Unexpected update: ' + update_message)
                else:
                    logger.debug('Update:' + update_message)
        if updates > 0:
            return True
        else:
            return False

    def _update_model_object_per_query_row(self, source_db, query, make_args, **kwargs):
        """Update an existing model object from each row of a query's results.
        
        Run a query on the source db and use its results to update any changed values
        in the Django db models. 
        
        Arguments:
            source_db (MySQLConnection): a mysql.connector open db connection 
            query (str): query to send to the open db
            make_args (function): function to convert a db query result row to args for making a model object
            model (class obj): the model class to use to make a model object instance
        
        Returns:
            int; number of updated rows that were detected in the source db
        """
        # Print the results of the updated rows query (SQL table format).
        # print(query)
        # cursor = source_db.cursor(buffered=True, dictionary=False)
        # cursor.execute(query)
        # results = cursor.fetchall()
        # widths = []
        # columns = []
        # sep_col = '|'
        # sep_row = '+'
        # 
        # for cd in cursor.description:
        #     if cd[2] is not None:
        #         widths.append(max(cd[2], len(cd[0])))
        #     else:
        #         widths.append(len(cd[0]))
        #     columns.append(cd[0])
        # 
        # for w in widths:
        #     sep_col += " %-"+"%ss |" % (w, )
        #     sep_row += '-'*w + '--+'
        # 
        # print(sep_row)
        # print(sep_col % tuple(columns))
        # print(sep_row)
        # for row in results:
        #     print(sep_col % row)
        # print(sep_row)
        # print('\n')
        # 
        cursor = source_db.cursor(buffered=True, dictionary=True)
        cursor.execute(query)
        updated = 0
        for row in cursor:
            args = make_args(self._fix_row(row))
            if self._update_model_object_from_args(model_args=args, **kwargs):
                updated += 1
        cursor.close()

    def _update_existing_data(self, **kwargs):
        """Update field values that have been modified in the source db since the last update.
        
        Find the pks for model that have already been imported into Django. Then
        query the source db for rows that have been modified since their import into
        Django. Use the results of that query to update the data in the Django db.
        
        Returns:
            int; the number of updated rows detected in the source db
        """
        model = kwargs['model']
        old_pks = self._get_current_pks(model)
        if len(old_pks) < 1:
            logger.debug('Model {} has no imported objects to check for updates.'.format(model._meta.object_name))
            n_updated = 0
        else:
            update_rows_query = self._make_query_for_rows_to_update(old_pks=old_pks, changed_greater=True, **kwargs)
            logger.debug(update_rows_query)
            logger.debug('Updating entries for model {} ...'.format(model._meta.object_name))
            n_updated = self._update_model_object_per_query_row(query=update_rows_query, **kwargs)
        return n_updated


    # Methods to make object-instantiating args from a row of the source db data.
    def _make_global_study_args(self, row_dict):
        """Get args for making a GlobalStudy object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a GlobalStudy
        object. If there is a schema change in the source db, this function may
        need to be modified.
        
        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_GlobalStudy_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict, ['id', 'name', 'date_added', 'date_changed'])

    def _make_study_args(self, row_dict):
        """Get args for making a Study object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a Study
        object. If there is a schema change in the source db, this function may
        need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_Study_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['accession', 'study_name', 'date_added', 'date_changed'],
                                       foreign_key_mapping={'global_study_id': GlobalStudy})
    
    def _make_source_study_version_args(self, row_dict):
        """Get args for making a SourceStudyVersion object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceStudyVersion object. If there is a schema change in the source db,
        this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_SourceStudyVersion_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'version', 'participant_set', 'dbgap_date', 'is_deprecated', 'is_prerelease',
                                        'date_added', 'date_changed'],
                                       foreign_key_mapping={'accession':Study})
    
    def _make_source_dataset_args(self, row_dict):
        """Get args for making a SourceDataset object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        SourceDataset object. If there is a schema change in the source db,
        this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_SourceDataset_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'accession', 'dbgap_description', 'dcc_description', 'is_medication_dataset',
                                        'is_subject_file','study_subject_column', 'version', 'visit_code', 'visit_number',
                                        'date_added', 'date_changed'],
                                       foreign_key_mapping={'study_version_id':SourceStudyVersion})

    def _make_harmonized_trait_set_args(self, row_dict):
        """Get args for making a HarmonizedTraitSet object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        HarmonizedTraitSet object. If there is a schema change in the source db,
        this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_HarmonizedTraitSet_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'trait_set_name', 'version', 'flavor', 'description', 'date_added', 'date_changed'])
    
    def _make_source_trait_args(self, row_dict):
        """Get args for making a SourceTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a SourceTrait object. If there's
        a schema change in the source db, this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['trait_name', 'detected_type', 'dbgap_type', 'visit_number', 'dbgap_variable_accession',
                                        'dbgap_variable_version', 'dbgap_comment', 'dbgap_unit', 'n_records', 'n_missing',
                                        'date_added', 'date_changed'],
                                       source_field_names_to_map={'source_trait_id':'i_trait_id', 'dcc_description':'i_description'},
                                       foreign_key_mapping={'dataset_id': SourceDataset})

    def _make_harmonized_trait_args(self, row_dict):
        """Get args for making a HarmonizedTrait object from a source db row.
        
        Converts a dict containing (colname: row value) pairs into a dict with
        the necessary arguments for constructing a HarmonizedTrait object. If there's
        a schema change in the source db, this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db
        
        Returns:
            a dict of (required_HarmonizedTrait_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['description', 'data_type', 'unit', 'is_unique_key', 'trait_name',
                                        'date_added', 'date_changed'],
                                       source_field_names_to_map={'harmonized_trait_id':'i_trait_id'},
                                       foreign_key_mapping={'harmonized_trait_set_id': HarmonizedTraitSet})

    def _make_subcohort_args(self, row_dict):
        """Get args for making a Subcohort object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a database
        query into a dict with the necessary arguments for constructing a
        Subcohort object. If there is a schema change in the source db,
        this function may need to be modified.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db

        Returns:
            a dict of (required_Subcohort_attribute: attribute_value) pairs
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'name', 'date_added', 'date_changed'],
                                       foreign_key_mapping={'study_accession':Study})
    
    def _make_source_trait_encoded_value_args(self, row_dict):
        """Get args for making a SourceTraitEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db
        
        Arguments:
            source_db -- an open connection to the source database
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'category', 'value', 'date_added', 'date_changed'],
                                       foreign_key_mapping={'source_trait_id':SourceTrait})

    def _make_harmonized_trait_encoded_value_args(self, row_dict):
        """Get args for making a HarmonizedTraitEncodedValue object from a source db row.
        
        Converts a dictionary containing {colname: row value} pairs from a
        database query into a dict with the necessary arguments for constructing
        a Study object. If there is a schema change in the source db, this function
        may need to be changed.

        Arguments:
            row_dict (dict): (column_name, row_value) pairs retrieved from the source db
        
        Arguments:
            source_db -- an open connection to the source database
        """
        return self._make_args_mapping(row_dict,
                                       ['id', 'category', 'value', 'date_added', 'date_changed'],
                                       foreign_key_mapping={'harmonized_trait_id':HarmonizedTrait})


    # Methods for importing data for ManyToMany fields.
    def _break_m2m_link(self, parent_model, parent_pk, child_model, child_pk, child_related_name, **kwargs):
        """Remove a child model object instance from the M2M field of a parent model object instance.
        
        Get model object instances for the parent and child models, given the pk values.
        Use getattr to get the M2M related field. Then use the M2M related object
        manager to remove the child model object instance from the parent model
        object instance's M2M field.
        
        Arguments:
            parent_model (class obj): the model class of the parent model for the m2m field
            parent_pk (str): pk value of the parent model instance to link the child model to
            child_model (class obj): the model class of the child model for the m2m field
            child_pk (str): pk value of the child model instance to link to the parent model
            child_related_name (str): name of the parent model's field which is related to child_model
        
        Returns:
            (parent model object instance, child model object instance)
        """
        parent = parent_model.objects.get(pk=parent_pk)
        child = child_model.objects.get(pk=child_pk)
        m2m_manager = getattr(parent, child_related_name)
        m2m_manager.remove(child)
        logger.debug('Unlinked {} from {}'.format(child, parent))
        return (parent, child)

    def _make_m2m_link(self, parent_model, parent_pk, child_model, child_pk, child_related_name, **kwargs):
        """Add a child model object instance to the M2M field of a parent model object instance.
        
        parent_model must have a field that is a ManyToManyField to child_model.
        Get model object instances for the parent and child models, given the pk
        values. Find the parent's M2M field that matches the child model. Then use
        the M2M field manager to add the child model object instance to parent
        model object instance's M2M field. 
        
        Arguments:
            parent_model (class obj): the model class of the parent model for the m2m field
            parent_pk (str): pk value of the parent model instance to link the child model to
            child_model (class obj): the model class of the child model for the m2m field
            child_pk (str): pk value of the child model instance to link to the parent model
            child_related_name (str): name of the parent model's field which is related to child_model
        
        Returns:
            (parent model object instance, child model object instance)
        """
        parent = parent_model.objects.get(pk=parent_pk)
        child = child_model.objects.get(pk=child_pk)
        m2m_manager = getattr(parent, child_related_name)
        m2m_manager.add(child)
        logger.debug('Linked {} to {}'.format(child, parent))
        return (parent, child)
    
    def _import_new_m2m_field(self, source_db, **kwargs):
        """Import ManyToMany field links from an m2m source table for a set of pks for the newly imported parent model.
        
        parent_model must have a field that is a ManyToManyField to child_model.
        Query the source db for entries in the m2m table (source_table) that link
        child_source_pk values to parent_source_pk values, for parent_source_pk values
        that are in the import_parent_pks list. Then use the results of that query
        to link child_model instances to parent_model instances, using
        parent_model_obj.children.add(child_model_obj)
        
        Arguments:
            source_db (MySQLConnection): a mysql.connector open db connection 
        
        Returns:
            list of str pk values for (parent_pk, child_pk) pairs that have now been linked
        """
        new_m2m_query = self._make_table_query(filter_field=kwargs['parent_source_pk'],
                                               filter_values=kwargs['import_parent_pks'], 
                                               filter_not=False, **kwargs)
        cursor = source_db.cursor(buffered=True, dictionary=True)
        cursor.execute(new_m2m_query)
        links = []
        for row in cursor:
            type_fixed_row = self._fix_row(row)
            child, parent = self._make_m2m_link(parent_pk=type_fixed_row[kwargs['parent_source_pk']],
                                                child_pk=type_fixed_row[kwargs['child_source_pk']],
                                                **kwargs)
            links.append((parent.pk, child.pk))
        return links

    def _update_m2m_field(self, source_db, **kwargs):
        """Remove m2m links that have been removed from the source db (for already-imported parent models).
        
        For each parent model that has been imported, get a list of the linked children
        and check the source db to see if the link between parent and child is still
        present there. If it is no longer linked in the source db, remove the child
        from the m2m field. 
        
        Arguments:
            source_db (MySQLConnection): a mysql.connector open db connection 
        
        Returns:
            list of str pk values for (parent_pk, child_pk) pairs that have now been linked
        """
        links = {'added': [], 'removed': []}
        cursor = source_db.cursor(buffered=True, dictionary=True)
        current_parents = kwargs['parent_model'].objects.all()
        for parent in current_parents:
            logger.debug(parent)
            # Which links are currently present in the Django db?
            linked_pks = [str(el.pk) for el in getattr(parent, kwargs['child_related_name']).all()]
            # Which links are currently present in the source db?
            source_links_query = self._make_table_query(filter_field=kwargs['parent_source_pk'], filter_values=[str(parent.pk)], filter_not=False, **kwargs)
            cursor.execute(source_links_query)
            source_linked_pks = [str(self._fix_row(row)[kwargs['child_source_pk']]) for row in cursor.fetchall()]
            # Figure out which child pk's to add or remove links to.
            to_add = set(source_linked_pks) - set(linked_pks)
            to_remove = set(linked_pks) - set(source_linked_pks)
            # Do the adding and removing
            for pk in to_add:
                add_parent, add_child = self._make_m2m_link(parent_pk=parent.pk, child_pk=pk, **kwargs)
                links['added'].append((add_parent, add_child))
            for pk in to_remove:
                remove_parent, remove_child = self._break_m2m_link(parent_pk=parent.pk, child_pk=pk, **kwargs)
                links['removed'].append((remove_parent, remove_child))
        return links


    # Methods to run all of the updating or importing on all of the models.
    def _import_source_tables(self, which_db):
        """Import all source trait-related data from the source db into the Django models.
        
        Connect to the specified source db and run helper methods to import new data
        for SourceTrait and its related models. For regular models, use the
        _import_new_data() function with appropriate arguments. For ManyToMany fields,
        use the _import_new_m2m_field() function with appropriate arguments. Close
        the source db connection when finished.
        
        Arguments:
            which_db (str): the type of source db to connect to (should be one
                of 'devel', 'test', 'production'); passed on from the command
                line argument
        
        Returns:
            None
        """
        logger.info('Importing new source traits...')
        source_db = self._get_source_db(which_db=which_db)

        new_global_study_pks = self._import_new_data(source_db=source_db,
                                                     source_table='global_study',
                                                     source_pk='id',
                                                     model=GlobalStudy,
                                                     make_args=self._make_global_study_args)
        logger.info("Added {} global studies".format(len(new_global_study_pks)))
        new_study_pks = self._import_new_data(source_db=source_db,
                                              source_table='study',
                                              source_pk='accession',
                                              model=Study,
                                              make_args=self._make_study_args)
        logger.info("Added {} studies".format(len(new_study_pks)))
        new_source_study_version_pks = self._import_new_data(source_db=source_db,
                                                             source_table='source_study_version',
                                                             source_pk='id',
                                                             model=SourceStudyVersion,
                                                             make_args=self._make_source_study_version_args)
        logger.info("Added {} source study versions".format(len(new_source_study_version_pks)))
        new_source_dataset_pks = self._import_new_data(source_db=source_db,
                                                       source_table='source_dataset',
                                                       source_pk='id',
                                                       model=SourceDataset,
                                                       make_args=self._make_source_dataset_args)
        logger.info("Added {} source datasets".format(len(new_source_dataset_pks)))
        new_source_trait_pks = self._import_new_data(source_db=source_db,
                                                     source_table='source_trait',
                                                     source_pk='source_trait_id',
                                                     model=SourceTrait,
                                                     make_args=self._make_source_trait_args)
        logger.info("Added {} source traits".format(len(new_source_trait_pks)))
        new_subcohort_pks = self._import_new_data(source_db=source_db,
                                                  source_table='subcohort',
                                                  source_pk='id',
                                                  model=Subcohort,
                                                  make_args=self._make_subcohort_args)
        logger.info("Added {} subcohorts".format(len(new_subcohort_pks)))
        new_source_trait_encoded_value_pks = self._import_new_data(source_db=source_db,
                                                             source_table='source_trait_encoded_values',
                                                             source_pk='id',
                                                             model=SourceTraitEncodedValue,
                                                             make_args=self._make_source_trait_encoded_value_args)
        logger.info("Added {} source trait encoded values".format(len(new_source_trait_encoded_value_pks)))

        new_source_dataset_subcohort_links = self._import_new_m2m_field(source_db=source_db,
                                                                        source_table='source_dataset_subcohorts',
                                                                        parent_model=SourceDataset,
                                                                        parent_source_pk='dataset_id',
                                                                        child_model=Subcohort,
                                                                        child_source_pk='subcohort_id',
                                                                        child_related_name='subcohorts',
                                                                        import_parent_pks=new_source_dataset_pks)
        logger.info("Added {} source dataset subcohorts".format(len(new_source_dataset_subcohort_links)))

        source_db.close()    

    def _import_harmonized_tables(self, which_db):
        """Import all harmonized trait-related data from the source db into the Django models.
        
        Connect to the specified source db and run helper methods to import new data
        for HarmonizedTrait and its related models. For regular models, use the
        _import_new_data() function with appropriate arguments. For ManyToMany fields,
        use the _import_new_m2m_field() function with appropriate arguments. Close
        the source db connection when finished.
        
        Arguments:
            which_db (str): the type of source db to connect to (should be one
                of 'devel', 'test', 'production'); passed on from the command
                line argument
        
        Returns:
            None
        """
        logger.info('Importing new harmonized traits...')
        source_db = self._get_source_db(which_db=which_db)
        
        new_harmonized_trait_set_pks = self._import_new_data(source_db=source_db,
                                                             source_table='harmonized_trait_set',
                                                             source_pk='id',
                                                             model=HarmonizedTraitSet,
                                                             make_args=self._make_harmonized_trait_set_args)
        logger.info("Added {} harmonized trait sets".format(len(new_harmonized_trait_set_pks)))

        new_harmonized_trait_pks = self._import_new_data(source_db=source_db,
                                                             source_table='harmonized_trait',
                                                             source_pk='harmonized_trait_id',
                                                             model=HarmonizedTrait,
                                                             make_args=self._make_harmonized_trait_args)
        logger.info("Added {} harmonized traits".format(len(new_harmonized_trait_pks)))

        new_harmonized_trait_encoded_value_pks = self._import_new_data(source_db=source_db,
                                                             source_table='harmonized_trait_encoded_values',
                                                             source_pk='harmonized_trait_id',
                                                             model=HarmonizedTraitEncodedValue,
                                                             make_args=self._make_harmonized_trait_encoded_value_args)
        logger.info("Added {} harmonized trait encoded values".format(len(new_harmonized_trait_encoded_value_pks)))
        

        new_component_source_trait_links = self._import_new_m2m_field(source_db=source_db,
                                                                        source_table='component_source_trait',
                                                                        parent_model=HarmonizedTraitSet,
                                                                        parent_source_pk='harmonized_trait_set_id',
                                                                        child_model=SourceTrait,
                                                                        child_source_pk='component_trait_id',
                                                                        child_related_name='component_source_traits',
                                                                        import_parent_pks=new_harmonized_trait_set_pks)
        logger.info("Added {} component source traits".format(len(new_component_source_trait_links)))

        source_db.close()

    def _update_source_tables(self, which_db):
        """Update source trait-related Django models from modified data in the source db.
        
        Connect to the specified source db and run helper methods to detect modifications
        for SourceTrait and its related models. Look for data in the source db that
        has been changed since after the latest modified date in the related Django
        model. For regular models, use the _update_existing_data() function with
        appropriate arguments. For ManyToMany fields, use the _update_m2m_field()
        function with appropriate arguments. Close the source db connection when
        finished.
        
        Arguments:
            which_db (str): the type of source db to connect to (should be one
                of 'devel', 'test', 'production'); passed on from the command
                line argument
        
        Returns:
            None
        """
        logger.info('Updating source traits...')
        source_db = self._get_source_db(which_db=which_db)

        updated_source_dataset_subcohort_links = self._update_m2m_field(source_db=source_db,
                                                                    source_table='source_dataset_subcohorts',
                                                                    parent_model=SourceDataset,
                                                                    parent_source_pk='dataset_id',
                                                                    child_model=Subcohort,
                                                                    child_source_pk='subcohort_id',
                                                                    child_related_name='subcohorts')
        logger.info("Update: added {} source dataset subcohorts".format(len(updated_source_dataset_subcohort_links['added'])))
        logger.info("Update: removed {} source dataset subcohorts".format(len(updated_source_dataset_subcohort_links['removed'])))

        global_study_update_count = self._update_existing_data(source_db=source_db,
                                   source_table='global_study',
                                   source_pk='id',
                                   model=GlobalStudy,
                                   make_args=self._make_global_study_args,
                                   expected=False)
        logger.info('{} global studies updated'.format(global_study_update_count))

        study_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='study',
                                    source_pk='accession',
                                    model=Study,
                                    make_args=self._make_study_args,
                                    expected=False)
        logger.info('{} studies updated'.format(study_update_count))

        source_study_version_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='source_study_version',
                                    source_pk='id',
                                    model=SourceStudyVersion,
                                    make_args=self._make_source_study_version_args,
                                    expected=True)
        logger.info('{} source study versions updated'.format(source_study_version_update_count))

        source_dataset_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='source_dataset',
                                    source_pk='id',
                                    model=SourceDataset,
                                    make_args=self._make_source_dataset_args,
                                    expected=True)
        logger.info('{} source datasets updated'.format(source_dataset_update_count))

        source_trait_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='source_trait',
                                    source_pk='source_trait_id',
                                    model=SourceTrait,
                                    make_args=self._make_source_trait_args,
                                    expected=True)
        logger.info('{} source traits updated'.format(source_trait_update_count))

        subcohort_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='subcohort',
                                    source_pk='id',
                                    model=Subcohort,
                                    make_args=self._make_subcohort_args,
                                    expected=True)
        logger.info('{} subcohorts updated'.format(subcohort_update_count))

        source_trait_ev_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='source_trait_encoded_values',
                                    source_pk='id',
                                    model=SourceTraitEncodedValue,
                                    make_args=self._make_source_trait_encoded_value_args,
                                    expected=False)
        logger.info('{} source trait encoded values updated'.format(source_trait_ev_update_count))

        source_db.close()

    def _update_harmonized_tables(self, which_db):
        """Update harmonized trait-related Django models from modified data in the source db.
        
        Connect to the specified source db and run helper methods to detect modifications
        for HarmonizedTrait and its related models. Look for data in the source db that
        has been changed since after the latest modified date in the related Django
        model. For regular models, use the _update_existing_data() function with
        appropriate arguments. For ManyToMany fields, use the _update_m2m_field()
        function with appropriate arguments. Close the source db connection when
        finished.
        
        Arguments:
            which_db (str): the type of source db to connect to (should be one
                of 'devel', 'test', 'production'); passed on from the command
                line argument
        
        Returns:
            None
        """
        logger.info('Updating harmonized traits...')
        source_db = self._get_source_db(which_db=which_db)

        updated_component_source_trait_links = self._update_m2m_field(source_db=source_db,
                                                                  source_table='component_source_trait',
                                                                  parent_model=HarmonizedTraitSet,
                                                                  parent_source_pk='harmonized_trait_set_id',
                                                                  child_model=SourceTrait,
                                                                  child_source_pk='component_trait_id',
                                                                  child_related_name='component_source_traits')
        logger.info("Update: added {} component source traits".format(len(updated_component_source_trait_links['added'])))
        logger.info("Update: removed {} component source traits".format(len(updated_component_source_trait_links['removed'])))

        htrait_set_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='harmonized_trait_set',
                                    source_pk='id',
                                    model=HarmonizedTraitSet,
                                    make_args=self._make_harmonized_trait_set_args,
                                    expected=False)
        logger.info('{} harmonized trait sets updated'.format(htrait_set_update_count))

        harmonized_trait_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='harmonized_trait',
                                    source_pk='harmonized_trait_id',
                                    model=HarmonizedTrait,
                                    make_args=self._make_harmonized_trait_args,
                                    expected=False)
        logger.info('{} harmonized traits updated'.format(harmonized_trait_update_count))

        htrait_ev_update_count = self._update_existing_data(source_db=source_db,
                                    source_table='harmonized_trait_encoded_values',
                                    source_pk='harmonized_trait_id',
                                    model=HarmonizedTraitEncodedValue,
                                    make_args=self._make_harmonized_trait_encoded_value_args,
                                    expected=False)
        logger.info('{} harmonized trait encoded values updated'.format(htrait_ev_update_count))

        source_db.close()    


    # Methods to actually do the management command.
    def add_arguments(self, parser):
        """Add custom command line arguments to this management command."""
        parser.add_argument('--which_db', action='store', type=str,
                            choices=['test', 'devel', 'production'], default=None, required=True,
                            help='Which source database to connect to for retrieving source data.')
        parser.add_argument('--no_backup', action='store_true',
                            help='Do not backup the Django db before running update and import functions. This should only be used for testing purposes.')
        only_group = parser.add_mutually_exclusive_group()
        only_group.add_argument('--update_only', action='store_true',
                                help='Only update the db records that are already in the db, and do not add new ones.')
        only_group.add_argument('--import_only', action='store_true',
                                help='Only import new db records, and do not update records that are already imported.')

    def handle(self, *args, **options):
        """Handle the main functions of this management command.
        
        Get a connection to the source db, update the source trait models, update
        the harmonized trait models, import new data from the source trait models,
        and finally import new data from the harmonized trait models. Then close
        the connection to the db. Import and update functions can be run separately
        using the --update_only and --import_only command line flags.
        
        Arguments:
            **args and **options are handled as per the superclass handling; these
            argument dicts will pass on command line options
        """
        # Set the logger level based on verbosity setting.
        verbosity = options.get('verbosity') 
        if verbosity == 0:
            logger.setLevel(logging.ERROR)
        elif verbosity == 1:
            logger.setLevel(logging.WARNING)
        elif verbosity == 2:
            logger.setLevel(logging.INFO)
        elif verbosity == 3:
            logger.setLevel(logging.DEBUG)
        
        # First, backup the db before anything is changed.
        if not options.get('no_backup'):
            management.call_command('dbbackup', compress=True)
            logger.info('Django db backup completed.')
        else:
            logger.info('No backup of Django db, due to no_backup option.')
        # First update, then import new data.
        if not options['import_only']:
            self._update_source_tables(which_db=options['which_db'])
            self._update_harmonized_tables(which_db=options['which_db'])
        if not options['update_only']:
            self._import_source_tables(which_db=options['which_db'])
            self._import_harmonized_tables(which_db=options['which_db'])
