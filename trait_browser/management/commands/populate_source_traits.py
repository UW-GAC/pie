# References:
# [python - Good ways to import data into Django - Stack Overflow](http://stackoverflow.com/questions/14504585/good-ways-to-import-data-into-django)
# [Providing initial data for models | Django documentation | Django](https://docs.djangoproject.com/en/1.8/howto/initial-data/)

from django.core.management.base import BaseCommand, CommandError
from django.utils                import timezone
from django.conf                 import settings
from datetime                    import datetime

import mysql.connector
import socket
from trait_browser.models import SourceTrait, SourceEncodedValue, Study


    
class Command(BaseCommand):
    help ='Populate the Study, SourceTrait, and EncodedValue models with a query to the source db'

    def _get_snuffles(self, test=True, cnf_path=settings.CNF_PATH):
        # Use this function lifted almost directly from OLGApipeline.py, for now
        '''
        '''
        #cnf_file = os.path.expanduser('~')  + "/.mysql-topmed.cnf"
        
        if test:
            test_string = "_test"
        else:
            test_string = "_production"
        
        cnf_group = ["client", "mysql_topmed_readonly" + test_string]
        
        cnx = mysql.connector.connect(option_files=cnf_path, option_groups=cnf_group, charset='latin1', use_unicode=False)
        
        return cnx

    
    def _fix_bytearray(self, row_dict):
        """Convert byteArrays into decoded strings. 
        Reference: https://dev.mysql.com/doc/relnotes/connector-python/en/news-2-0-0.html
        """
        fixed_row = { (k) : (row_dict[k].decode('utf-8')
                             if isinstance(row_dict[k], bytearray)
                             else row_dict[k]) for k in row_dict }
        return fixed_row
    
    def _fix_null(self, row_dict):
        """Convert None values (NULL in the db) to empty strings."""
        fixed_row = { (k) : ('' if row_dict[k] is None
                             else row_dict[k]) for k in row_dict }
        return fixed_row
        
    
    def _fix_timezone(self, row_dict):
        """Add timezone awareness to datetime objects."""
        fixed_row = { (k) : (timezone.make_aware(row_dict[k], timezone.get_current_timezone())
                             if isinstance(row_dict[k], datetime)
                             else row_dict[k]) for k in row_dict }
        return fixed_row


    def _make_study_args(self, row_dict):
        '''
        Converts a dictionary containing {colname: row value} pairs from a database query into a
        dict with the necessary arguments for constructing a Study object. If there is a schema change
        in the source db, this function may need to be modified.

        Returns:
            a dict of (required_StudyTrait_attribute: attribute_value) pairs
        '''

        new_args = {'study_id': row_dict['study_id'],
                    'dbgap_id': row_dict['dbgap_id'],
                    'name': row_dict['study_name']}
        return new_args
    
    
    def _populate_studies(self, source_db):
        '''
        Pulls study information from the source db, converts it where necessary, and populates entries
        in the Study model of the trait_browser app.
        '''
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_query = 'SELECT * FROM study'
        cursor.execute(study_query)

        # Iterate over rows from the source db and add them to the Study model
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))

            study_args = self._make_study_args(type_fixed_row)
            add_var = Study(**study_args)
            add_var.save()
            print(" ".join(('Added study', str(study_args['study_id']))))

        cursor.close()
    

    def _make_source_trait_args(self, row_dict):
        '''
        Converts a dict containing (colname: row value) pairs into a dict with the necessary arguments
        for constructing a SourceTrait object. If there's a schema change in the source db, this function
        may need to be modified.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        '''
        study = Study.objects.get(study_id=row_dict['study_id'])
        phs_string = "%s.v%d.p%d" % (study.dbgap_id,
                                     row_dict['dbgap_study_version'],
                                     row_dict['dbgap_participant_set'])

        new_args = {'dcc_trait_id': row_dict['source_trait_id'],
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
        '''
        Pulls source trait data from the source db, converts it where necessary, and populates entries
        in the SourceTrait model of the trait_browser app.
        '''
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_variable_metadata LIMIT 400;'
        cursor.execute(trait_query)
        # Iterate over rows from the source db, adding them to the SourceTrait model
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))
            # Properly format the data from the db for the site's model
            model_args = self._make_source_trait_args(type_fixed_row)
    
            # Add this row to the SourceTrait model
            add_var = SourceTrait(**model_args)
            add_var.save()
            print(" ".join(('Added trait', str(model_args['dcc_trait_id']))))
        cursor.close()


    def _make_source_encoded_value_args(self, row_dict):
        '''
        '''
        new_args = {'category': row_dict['category'],
                    'value': row_dict['value'],
                    'source_trait': SourceTrait.objects.get(dcc_trait_id = row_dict['source_trait_id'])
                    }
        return new_args


    def _populate_encoded_values(self, source_db):
        '''
        '''
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_encoded_values LIMIT 400;'
        cursor.execute(trait_query)
        # Iterate over rows from the source db, adding them to the EncodedValue model
        for row in cursor:
            type_fixed_row = self._fix_bytearray(self._fix_null(row))

            # print(type_fixed_row)
 
            # Properly format the data from the db for the site's model 
            model_args = self._make_source_encoded_value_args(type_fixed_row)

            # Add this row to the SourceEncodedValue model
            add_var = SourceEncodedValue(**model_args)
            add_var.save()
            print(" ".join(('Added encoded value for', str(type_fixed_row['source_trait_id']))))
        cursor.close()


    def handle(self, *args, **options):
        snuffles_db = self._get_snuffles(test=True)
        self._populate_studies(snuffles_db)
        self._populate_source_traits(snuffles_db)
        self._populate_encoded_values(snuffles_db)
        snuffles_db.close()

