"""Models for trait_browser app."""

from django.db import models

class Study(models.Model):
    """Model for Study table.
    
    Fields: 
        study_id
        dbgap_id
        name
    """
    study_id = models.IntegerField(primary_key=True, db_column='study_id')
    dbgap_id = models.CharField(max_length=10)
    name     = models.CharField(max_length=100)

    class Meta:
        # because grammar. "Studys" bothers me too much.
        verbose_name_plural = "Studies"

    def __str__(self):
        """Pretty printing of Study objects."""
        return self.name

class Trait(models.Model):
    """Abstract superclass model for SourceTrait and HarmonizedTrait.
    
    SourceTrait and HarmonizedTrait Models inherit from this Model, but the Trait
    model itself won't be used to create a db table. 
    
    Fields: 
        dcc_trait_id
        name
        description
        data_type
        unit
        web_date_added
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
    """Model for 'raw' source variable metadata as received from dbGaP. 
    
    Extends the Trait abstract model. 
    
    Fields: 
        study
        phs_string
        phv_string
    """
    
    study     = models.ForeignKey(Study)
    # This adds two fields: study is the actual Study object that this instance is linked to,
    # and study_id is the primary key of the linked Study object

    # dbGaP dataset id in phsNNNNN.vN.pN format
    phs_string             = models.CharField(max_length=20)
    # dbGaP variable id in phvNNNNNNN format
    phv_string             = models.CharField(max_length=15)
    
    def __str__(self):
        """Pretty printing of SourceTrait objects."""
        print_parms = ['dcc_trait_id', 'name', 'data_type', 'unit', 'web_date_added']
        print_list = ['{0} : {1}'.format(k, str(self.__dict__[k])) for k in print_parms]
        return '\n'.join(print_list)
    
    def is_latest_version(self):
        """Test whether this is the latest version of a given trait. 
        
        Returns: 
            boolean True or False
        """
        pass
        
    def field_iter(self):
        """Iterate over field_name, field_value pairs for the SourceTrait."""
        for field_name in [f.name for f in self._meta.get_fields()]:
            value = getattr(self, field_name, None)
            yield (field_name, value)

    def get_phv_number(self):
        """Extract just the numeric part of the phv_string. 
        
        Returns: 
            int value of the numeric part of the phv_string
        """
        number = int(self.phv_string.replace("phv", ""))
        return number

    def get_dbgap_link(self):
        """Build the dbGaP link URL with info for this trait. 
        
        Returns: 
            string URL of the dbGaP web address for the trait informational page
        """
        base_link = "http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id=%s&phv=%d"
        phv_number = self.get_phv_number()
        this_link = base_link % (self.phs_string, phv_number)
        return this_link

    
    def detail_iter(self):
        """Iterate over a specific set of formatted field names and field values. 
        
        This iterator is used by the SourceTrait detail view and template. 
        
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
    """Abstract superclass model for SourceEncodedValue and HarmonizedEncodedValue.
    
    SourceEncodedValue and HarmonizedEncodedValue models inherit from this Model,
    but the EncodedValue model itself won't be used to create a db table. 
    
    Fields: 
        category
        value
        web_date_added
    """
    # Set up model fields
    category         = models.CharField(max_length=45)
    value            = models.CharField(max_length=100)
    web_date_added   = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True

class SourceEncodedValue(EncodedValue):
    """Model for encoded values from 'raw' dbGaP data, as received from dbGaP.
    
    Extends the EncodedValue abstract superclass. 
    
    Fields: 
        source_trait
    """
    # Set Attributes
    source_trait     = models.ForeignKey(SourceTrait)
    # This adds two fields: source_trait is the actual SourceTrait object that this instance is linked to,
    # and source_trait_id is the primary key of the linked SourceTrait object

    # This will have an automatic primary key field, "id", since I didn't set a primary key
    
    def __str__(self):
        """Pretty printing of SourceEncodedValue objects."""
        to_print = (
            ('SourceTrait id', self.source_trait.dcc_trait_id,),
            ('SourceTrait name', self.source_trait.name,),
            ('category', self.category,),
            ('value', self.value,),
        )
        print_list = ['{0} : {1}'.format(el[0], el[1]) for el in to_print]
        return '\n'.join(print_list)
    
    def get_source_trait_name(self):
        """Get the name of the linked SourceTrait object. 
        
        This function is used to properly display the SourceTrait Name column 
        in the admin interface.
        
        Returns:
            name of the linked SourceTrait object
        """
        return self.source_trait.name
    # Set this model attribute to the value of this function, for the admin interface
    get_source_trait_name.short_description = 'SourceTrait Name'
    
    def get_source_trait_study(self):
        """Get the name of the linked Study object. 
        
        This function is used to properly display the Study Name column in the 
        admin interface.  
        
        Returns:
            study_name of the linked SourceTrait object
        """
        return self.source_trait.study_name
    # Set this model attribute to the value of this function, for the admin interface 
    get_source_trait_study.short_description = 'Study Name'
