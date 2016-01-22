from django.core.management.base import BaseCommand, CommandError
from django.utils                import timezone
from datetime                    import datetime

# References:
# [python - Good ways to import data into Django - Stack Overflow](http://stackoverflow.com/questions/14504585/good-ways-to-import-data-into-django)
# [Providing initial data for models | Django documentation | Django](https://docs.djangoproject.com/en/1.8/howto/initial-data/)

import mysql.connector
import socket
from trait_browser.models import SourceTrait, SourceEncodedValue

## database functions ##
def getCnfDict(cnfFile):
    '''
    '''
    with open(cnfFile) as f:
        lines = f.readlines()
    stripped = [x.strip('\n') for x in lines]

    # list comprehension to split each line by '=' and make it a key,value pair for a dictionary.
    cnf = dict([ (a[0].strip(), a[1].strip()) for a in [s.split('=') for s in stripped] if len(a) == 2])
    return(cnf)


def getDb(dbname):
    # Use this function lifted almost directly from OLGApipeline.py, for now
    '''
    '''
    # if a mac, use the workstation cnf file
    workstations = ['gcc-mac-001.in.biostat.washington.edu',
                    'gcc-mac-003.in.gcc.biostat.washington.edu',
                    'gcc-mac-004.in.gcc.biostat.washington.edu']
    host = socket.gethostname()
    
    if host in workstations:
        cnf_file = '/projects/geneva/gcc-fs2/OLGA/pipeline/.pipeline_olga-mysql-workstation-ro.cnf'
    else:
        cnf_file = '/projects/geneva/gcc-fs2/OLGA/pipeline/.pipeline_olga-mysql-server-ro.cnf'

    if (host in workstations) & (dbname not in ('olga_analysis_test', 'test')):
        print('Do not update full database from workstations.')
        cnx = None
    else:
        cnf = getCnfDict(cnf_file)
        cnx = mysql.connector.connect(database=dbname, charset='latin1', use_unicode=False, **cnf)
    
    return cnx

class Command(BaseCommand):
    help ='Populate the SourceTrait and EncodedValue models with a query to snuffles'
    
    # def add_arguments(self, parser):
    #     parser.add_agrument()
    
    def _populate_source_traits(self, source_db):
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_variable_metadata LIMIT 400;'
        cursor.execute(trait_query)
        # Iterate over rows from the source db, adding them to the SourceTrait model
        for row in cursor:
            type_fixed_row = { (k) : (row[k].decode('utf-8') if type(row[k]) is bytearray
                                      else timezone.make_aware(row[k], timezone.get_current_timezone()) if type(row[k]) is datetime
                                      else row[k]) for k in row }
            # Change source_trait_id name to trait_id (to account for abstract Trait SuperClass)
            trait_id = type_fixed_row['source_trait_id']
            del type_fixed_row['source_trait_id']
            type_fixed_row['trait_id'] = trait_id
            # print(type_fixed_row)
            # Add this row to the site's models
            add_var = SourceTrait(**type_fixed_row)
            add_var.save()
            print(" ".join(('Added trait', str(trait_id))))
        cursor.close()
        
    
    def _populate_encoded_values(self, source_db):
        cursor = source_db.cursor(buffered=True, dictionary=True)
        trait_query = 'SELECT * FROM source_encoded_values LIMIT 400;'
        cursor.execute(trait_query)
        # Iterate over rows from the source db, adding them to the EncodedValue model
        for row in cursor:
            type_fixed_row = { (k) : (row[k].decode('utf-8') if type(row[k]) is bytearray
                                      else timezone.make_aware(row[k], timezone.get_current_timezone()) if type(row[k]) is datetime
                                      else row[k]) for k in row }
            # print(type_fixed_row)
            # Fix the foreign key usage
            linked_id = type_fixed_row['source_trait_id']
            type_fixed_row['trait'] = SourceTrait.objects.get(trait_id = linked_id)
            del type_fixed_row['source_trait_id']
            add_var = SourceEncodedValue(**type_fixed_row)
            add_var.save()
            print(" ".join(('Added encoded value for', str(linked_id))))
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