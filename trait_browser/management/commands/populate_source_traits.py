from django.core.management.base import BaseCommand, CommandError
from django.utils                import timezone
from datetime                    import datetime

# References:
# [python - Good ways to import data into Django - Stack Overflow](http://stackoverflow.com/questions/14504585/good-ways-to-import-data-into-django)
# [Providing initial data for models | Django documentation | Django](https://docs.djangoproject.com/en/1.8/howto/initial-data/)

import mysql.connector
import socket
from trait_browser.models import SourceTrait, SourceEncodedValue

def getDb(dbname):
    # Use this function lifted almost directly from OLGApipeline.py, for now
    '''
    '''
    servers = ('fisher',
               'pearson0',
               'pearson1',
               'neyman')
    
    cnf_map = {'server': '/projects/geneva/gcc-fs2/OLGA/pipeline/.pipeline_olga-mysql-server-ro.cnf',
               'workstation': '/projects/geneva/gcc-fs2/OLGA/pipeline/.pipeline_olga-mysql-workstation-ro.cnf'}
 
    host = socket.gethostname()
    
    if host in servers:
        cnf_file = cnf_map['server']
    else:
        cnf_file = cnf_map['workstation']

    cnx = mysql.connector.connect(option_files=cnf_file, database=dbname, charset='latin1', use_unicode=False)
    
    return cnx

def fixByteArray(row_dict):
    '''
    '''
    fixed_row = { (k) : (row_dict[k].decode('utf-8') if type(row_dict[k]) is bytearray
                                                else timezone.make_aware(row_dict[k], timezone.get_current_timezone()) if type(row_dict[k]) is datetime
                                                else row_dict[k]) for k in row_dict }
    return fixed_row
    
class Command(BaseCommand):
    help ='Populate the SourceTrait and EncodedValue models with a query to snuffles'
    
    # def add_arguments(self, parser):
    #     parser.add_agrument()
    
    def _getStudies(self, source_db):
        '''
        Called by _populate_source_traits function. Gets study table from snuffles and makes a dict
        to map dbgap_study_id to study_name.
        
        Returns:
            a dict of (study_id: study_name) pairs
        '''
        cursor = source_db.cursor(buffered=True, dictionary=True)
        study_query = 'SELECT * FROM study;'
        cursor.execute(study_query)
        study_rows = cursor.fetchall()
        # Fix the bytearray type 
        study_rows = [fixByteArray(row) for row in study_rows]
        # Make a dict from the db table
        study_dict = { row['study_id']: row['study_name'] for row in study_rows}
        cursor.close()
        return study_dict

    def _makeSourceTraitArgs(self, row_dict, study_dict):
        '''
        Converts a dict containing (colname: row value) pairs into a dict with the necessary arguments
        for constructing a SourceTrait object. If there's a schema change in snuffles, this is the
        function to modify.
        
        Returns:
            a dict of (required_SourceTrait_attribute: attribute_value) pairs
        '''
        new_args = {'dcc_trait_id': row_dict['source_trait_id'],
                    'name': row_dict['trait_name'],
                    'description': row_dict['short_description'],
                    'data_type': row_dict['data_type'],
                    'unit': row_dict['dbgap_unit'],
                    'study_name': study_dict[ row_dict['dbgap_study_id'] ],
                    'phs_string': ''.join( (row_dict['dbgap_study_id'],
                                            '.v', str(row_dict['dbgap_study_version']),
                                            '.p', str(row_dict['dbgap_participant_set']), ) ),
                    'phv_string': row_dict['dbgap_variable_id']
                    }
        return new_args

    def _populate_source_traits(self, source_db):
        '''
        Pulls source trait data from snuffles, converts it where necessary, and populates entries
        in the SourceTrait model of the trait_browser app.
        '''
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_variable_metadata LIMIT 400;'
        cursor.execute(trait_query)
        # Iterate over rows from the source db, adding them to the SourceTrait model
        for row in cursor:
            type_fixed_row = { (k) : (row[k].decode('utf-8') if type(row[k]) is bytearray
                                      else timezone.make_aware(row[k], timezone.get_current_timezone()) if type(row[k]) is datetime
                                      else row[k]) for k in row }
            
            # print(type_fixed_row)
            
            # Properly format the data from the db for the site's model
            study_dict = self._getStudies(source_db)
            model_args = self._makeSourceTraitArgs(type_fixed_row, study_dict)
    
            # Add this row to the SourceTrait model
            add_var = SourceTrait(**model_args)
            add_var.save()
            print(" ".join(('Added trait', str(model_args['dcc_trait_id']))))
        cursor.close()
   
    def _makeSourceEncodedValueArgs(self, row_dict):
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
            type_fixed_row = fixByteArray(row)

            # print(type_fixed_row)
 
            # Properly format the data from the db for the site's model 
            model_args = self._makeSourceEncodedValueArgs(type_fixed_row)

            # Add this row to the SourceEncodedValue model
            add_var = SourceEncodedValue(**model_args)
            add_var.save()
            print(" ".join(('Added encoded value for', str(type_fixed_row['source_trait_id']))))
        cursor.close()

    def handle(self, *args, **options):
        db = getDb("test")
        self._populate_source_traits(db)
        self._populate_encoded_values(db)
        db.close()

# if __name__ == '__main__':
#     db = getDb('test')
#     cursor = db.cursor(buffered=True, dictionary=True)
# 
#     trait_query = 'SELECT * FROM source_variable_metadata LIMIT 100;'
#     print(trait_query)
#     cursor.execute(trait_query)
#     
#     # TRAIT_ID_COL = 'source_trait_id'
#     # trait_columns = cursor.column_names
#     # non_id_columns = set(trait_columns) - set((TRAIT_ID_COL,))
# 
#     # Iterate over rows from the source db, adding them to the SourceTrait model
#     for row in cursor:
#         add_var = SourceTrait(**row)
#         add_var.save()
# 
#     # code_value_query = ('SELECT * FROM source_encoded_values LIMIT 100;')
#     # print(code_value_query)
#     # cursor.execute(code_value_query)
#     # 
#     # # Add each encoded value row to the EncodedValue model
#     # for row in cursor:
#     #     add_var = EncodedValue(**row)
#     #     add_var.save()
#     
#     cursor.close()
#     db.close()