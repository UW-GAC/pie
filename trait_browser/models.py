from django.db import models

class Study(models.Model):
    """
    Class to store study info
    """
    study_id = models.IntegerField(primary_key=True, db_column='study_id')
    dbgap_id = models.CharField(max_length=10)
    name     = models.CharField(max_length=100)

    class Meta:
        # because grammar. "Studys" bothers me too much.
        verbose_name_plural = "Studies"

    def __str__(self):
        """Pretty printing of Study objects"""
        return self.name

class Trait(models.Model):
    """
    Abstract super class for SourceTrait and HarmonizedTrait
    """
    # Set value choices for data_type
    DATA_TYPES = ("string", "integer", "encoded", "decimal") # All of the available data types
    # Make a properly formatted tuple of ("stored_value", "readable_name") pairs
    DATA_TYPE_CHOICES = tuple([(el, el) for el in DATA_TYPES])
    # Set up the model fields
    dcc_trait_id           = models.PositiveIntegerField(primary_key=True, db_column='dcc_trait_id')
    name                   = models.CharField(max_length=100)
    description            = models.CharField(max_length=500)
    data_type              = models.CharField(max_length=max([len(s) for s in DATA_TYPES]),choices=DATA_TYPE_CHOICES)
    unit                   = models.CharField(max_length=45)
    web_date_added         = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True

class SourceTrait(Trait):
    """
    Class to store data on the 'raw' source variable metadata
    """
    
    study     = models.ForeignKey(Study)
    # This adds two fields: study is the actual Study object that this instance is linked to,
    # and study_id is the primary key of the linked Study object

    # dbGaP dataset id in phsNNNNN.vN.pN format
    phs_string             = models.CharField(max_length=20)
    # dbGaP variable id in phvNNNNNNN format
    phv_string             = models.CharField(max_length=15)
    
    def __str__(self):
        """Pretty printing of SourceTrait objects"""
        print_parms = ['dcc_trait_id', 'name', 'data_type', 'unit', 'web_date_added']
        print_list = ['{0} : {1}'.format(k, str(self.__dict__[k])) for k in print_parms]
        return '\n'.join(print_list)
    
    def is_latest_version(self):
        """
        For Later: a function to determine if this instance of a SourceTrait is the latest version
        of a particular trait.
        """
        pass
        
    def field_iter(self):
        for field_name in [f.name for f in self._meta.get_fields()]:
            value = getattr(self, field_name, None)
            yield (field_name, value)

    def get_phv_number(self):
        number = int(self.phv_string.replace("phv", ""))
        return number

    def get_dbgap_link(self):
        base_link = "http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id=%s&phv=%d"
        phv_number = self.get_phv_number()
        this_link = base_link % (self.phs_string, phv_number)
        return this_link

    
    def detail_iter(self):
        """
        Iterator used by the SourceTrait detail view and template
        
        Yields:
            a (formatted_field_name, field_value) tuple
        """
        for fd in ('name', 'description', 'study_name', 'data_type', 'unit', ):
            if fd == 'study_name':
                value = self.study.name
            else:
                value = getattr(self, fd, None)
            yield (fd.replace('_', ' ').title(), value)
        

class EncodedValue(models.Model):
    """
    Abstract SuperClass for SourceEncodedValue and HarmonizedEncodedValue
    """
    # Set up model fields
    category         = models.CharField(max_length=45)
    value            = models.CharField(max_length=100)
    web_date_added   = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True

class SourceEncodedValue(EncodedValue):
    """
    Class to store data on encoded value categories for SourceTraits
    """
    # DESCRIBE source_encoded_values;
    # +-----------------+--------------+------+-----+---------+-------+
    # | Field           | Type         | Null | Key | Default | Extra |
    # +-----------------+--------------+------+-----+---------+-------+
    # | source_trait_id | int(11)      | NO   | PRI | NULL    |       |
    # | category        | varchar(45)  | NO   | PRI | NULL    |       |
    # | value           | varchar(100) | NO   |     | NULL    |       |
    # +-----------------+--------------+------+-----+---------+-------+
    
    # Set Attributes
    source_trait     = models.ForeignKey(SourceTrait)
    # This adds two fields: source_trait is the actual SourceTrait object that this instance is linked to,
    # and source_trait_id is the primary key of the linked SourceTrait object

    # This will have an automatic primary key field, "id", since I didn't set a primary key
    
    def __str__(self):
        """Pretty printing of SourceEncodedValue objects"""
        to_print = (
            ('SourceTrait id', self.source_trait.dcc_trait_id,),
            ('SourceTrait name', self.source_trait.name,),
            ('category', self.category,),
            ('value', self.value,),
        )
        print_list = ['{0} : {1}'.format(el[0], el[1]) for el in to_print]
        return '\n'.join(print_list)
    
    def get_source_trait_name(self):
        """
        Returns:
            name of the linked SourceTrait object
        """
        return self.source_trait.name
    get_source_trait_name.short_description = 'SourceTrait Name'
    
    def get_source_trait_study(self):
        """
        Returns:
            study_name of the linked SourceTrait object
        """
        return self.source_trait.study_name
    get_source_trait_study.short_description = 'Study Name'
