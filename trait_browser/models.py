from django.db import models

class Trait(models.Model):
    '''
    Abstract super class for SourceTrait and HarmonizedTrait
    '''
    # Set value choices for data_type
    DATA_TYPES = ("string", "integer", "encoded", "decimal") # All of the available data types
    # Make a properly formatted tuple of ("stored_value", "readable_name") pairs
    DATA_TYPE_CHOICES = tuple([(el, el) for el in DATA_TYPES])
    # Set up the model fields
    trait_id               = models.IntegerField(primary_key=True, db_column="trait_id")
    trait_name             = models.CharField(max_length=100)
    short_description      = models.CharField(max_length=500)
    data_type              = models.CharField(max_length=max([len(s) for s in DATA_TYPES]),choices=DATA_TYPE_CHOICES)
    web_date_added         = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True

class SourceTrait(Trait):
    '''
    Class to store data on the 'raw' source variable metadata
    '''
    # DESCRIBE source_variable_metadata;
    # +------------------------+----------------------------------------------+------+-----+---------+----------------+
    # | Field                  | Type                                         | Null | Key | Default | Extra          |
    # +------------------------+----------------------------------------------+------+-----+---------+----------------+
    # | source_trait_id        | int(11)                                      | NO   | PRI | NULL    | auto_increment |
    # | trait_name             | varchar(100)                                 | NO   |     | NULL    |                |
    # | short_description      | varchar(500)                                 | NO   |     | NULL    |                |
    # | data_type              | enum('string','integer','encoded','decimal') | NO   |     | NULL    |                |
    # | dbgap_study_id         | varchar(45)                                  | NO   | MUL | NULL    |                |
    # | dbgap_study_version    | int(11)                                      | NO   |     | NULL    |                |
    # | dbgap_dataset_id       | varchar(45)                                  | NO   |     | NULL    |                |
    # | dbgap_dataset_version  | int(11)                                      | NO   |     | NULL    |                |
    # | dbgap_variable_id      | varchar(45)                                  | NO   |     | NULL    |                |
    # | dbgap_variable_version | int(11)                                      | NO   |     | NULL    |                |
    # | dbgap_comment          | varchar(1000)                                | YES  |     | NULL    |                |
    # | dbgap_unit             | varchar(45)                                  | YES  |     | NULL    |                |
    # | dbgap_participant_set  | int(11)                                      | NO   |     | NULL    |                |
    # | dbgap_date_created     | datetime                                     | YES  |     | NULL    |                |
    # | dataset_description    | varchar(1000)                                | YES  |     | NULL    |                |
    # +------------------------+----------------------------------------------+------+-----+---------+----------------+
    
    # Set Attributes
    dbgap_study_id         = models.CharField(max_length=45)
    dbgap_study_version    = models.IntegerField()
    dbgap_dataset_id       = models.CharField(max_length=45)
    dbgap_dataset_version  = models.IntegerField()
    dbgap_variable_id      = models.CharField(max_length=45)
    dbgap_variable_version = models.IntegerField()
    dbgap_comment          = models.CharField(max_length=1000, null=True)
    dbgap_unit             = models.CharField(max_length=45, null=True)
    dbgap_participant_set  = models.IntegerField()
    dbgap_date_created     = models.DateTimeField(null=True)
    dataset_description    = models.CharField(max_length=1000, null=True)
    
    def __str__(self):
        '''Pretty printing of SourceTrait objects'''
        print_parms = ['trait_id', 'trait_name', 'data_type', 'dbgap_study_id', 'web_date_added']
        print_list = ['{0} : {1}'.format(k, str(self.__dict__[k])) for k in print_parms]
        return '\n'.join(print_list)
    
    def is_latest_version(self):
        '''
        For Later: a function to determine if this instance of a SourceTrait is the latest version
        of a particular trait.
        '''
        pass
        
    def field_iter(self):
        for field_name in self._meta.get_all_field_names():
            value = getattr(self, field_name, None)
            yield (field_name, value)
    
class EncodedValue(models.Model):
    '''
    Abstract SuperClass for SourceEncodedValue and HarmonizedEncodedValue
    '''
    # Set up model fields
    category         = models.CharField(max_length=45)
    value            = models.CharField(max_length=100)
    web_date_added   = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True

class SourceEncodedValue(EncodedValue):
    '''
    Class to store data on encoded value categories for SourceTraits
    '''
    # DESCRIBE source_encoded_values;
    # +-----------------+--------------+------+-----+---------+-------+
    # | Field           | Type         | Null | Key | Default | Extra |
    # +-----------------+--------------+------+-----+---------+-------+
    # | source_trait_id | int(11)      | NO   | PRI | NULL    |       |
    # | category        | varchar(45)  | NO   | PRI | NULL    |       |
    # | value           | varchar(100) | NO   |     | NULL    |       |
    # +-----------------+--------------+------+-----+---------+-------+
    
    # Set Attributes
    trait     = models.ForeignKey(SourceTrait)
    # This adds two fields: source_trait is the actual SourceTrait object that this instance is linked to,
    # and source_trait_id is the primary key of the linked SourceTrait object

    # This will have an automatic primary key field, "id", since I didn't set a primary key
    
    def __str__(self):
        '''Pretty printing of SourceEncodedValue objects'''
        to_print = (('SourceTrait id', self.trait.trait_id,),
            ('SourceTrait trait_name', self.trait.trait_name,),
            ('category', self.category,),
            ('value', self.value,),)
        print_list = ['{0} : {1}'.format(el[0], el[1]) for el in to_print]
        return '\n'.join(print_list)