"""Models for trait_browser app."""

from django.db import models


class Study(models.Model):
    """Model for Study table.
    
    Fields:
        study_id
        phs
        name
    """
    
    study_id = models.IntegerField(primary_key=True, db_column='study_id')
    phs = models.IntegerField()
    name = models.CharField(max_length=100)

    class Meta:
        # Fix pluralization of this model, because grammar. 
        verbose_name_plural = 'Studies'

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

    # Set value choices for data_type.
    DATA_TYPES = ('string', 'integer', 'encoded', 'decimal') # All of the available data types
    DATA_TYPE_CHOICES = tuple([(el, el) for el in DATA_TYPES])
    
    dcc_trait_id = models.PositiveIntegerField(primary_key=True, db_column='dcc_trait_id')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    data_type = models.CharField(max_length=max([len(s) for s in DATA_TYPES]),choices=DATA_TYPE_CHOICES)
    unit = models.CharField(max_length=45)
    web_date_added = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True


class SourceTrait(Trait):
    """Model for 'raw' source variable metadata as received from dbGaP.
    
    Extends the Trait abstract model.
    
    Fields:
        study
        phv
        pht
        study_version
        dataset_version
        variable_version
        participant_set
        study_accession
        dataset_accession
        variable_accession
        dbgap_study_link
        dbgap_variable_link
    """
    
    study = models.ForeignKey(Study)
    # This adds two fields: study is the actual Study object that this instance 
    # is linked to, and study_id is the primary key of the linked Study object.
    # dbGaP variable and dataset ids.
    phv = models.IntegerField()
    pht = models.IntegerField()
    # dbGaP version numbers.
    study_version = models.IntegerField()
    dataset_version = models.IntegerField()
    variable_version = models.IntegerField()
    participant_set = models.IntegerField()
    # dbGaP accession numbers
    study_accession = models.CharField(max_length=15)
    dataset_accession = models.CharField(max_length=15)
    variable_accession = models.CharField(max_length=17)
    # dbGaP links.
    # Since these are URLFields, they will be validated as well-formed URLs.
    dbgap_study_link = models.URLField(max_length=200)
    dbgap_variable_link = models.URLField(max_length=200)
    
    def __str__(self):
        """Pretty printing of SourceTrait objects."""
        print_parms = ['dcc_trait_id', 'name', 'data_type', 'unit', 'web_date_added']
        print_list = ['{0} : {1}'.format(k, str(self.__dict__[k])) for k in print_parms]
        return '\n'.join(print_list)
    
    def save(self, *args, **kwargs):
        """Custom save method for default dbGaP accessions and links.
        
        Automatically sets values for various dbGaP accession numbers and dbGaP
        link URLs. 
        """
        # Set values for dbGaP accession numbers.
        self.study_accession = self.set_study_accession()
        self.dataset_accession = self.set_dataset_accession()
        self.variable_accession = self.set_variable_accession()
        # Set values for dbGaP links.
        self.dbgap_study_link = self.set_dbgap_study_link()
        self.dbgap_variable_link = self.set_dbgap_variable_link()
        # Call the "real" save method.
        super(SourceTrait, self).save(*args, **kwargs)
    
    def is_latest_version(self):
        """Test whether this is the latest version of a given trait.
        
        Returns:
            boolean True or False
        """
        pass
        
    def set_study_accession(self):
        """Automatically set study_accession field from study.phs, study_version, and participant_set."""
        return 'phs{:06}.v{}.p{}'.format(self.study.phs, self.study_version, self.participant_set)

    def set_dataset_accession(self):
        """Automatically set dataset_accession field from pht, dataset_version, and participant_set."""
        return 'pht{:06}.v{}.p{}'.format(self.pht, self.dataset_version, self.participant_set)
    
    def set_variable_accession(self):
        """Automatically set variable_accession from phv, variable_version, and participant_set."""
        return 'phv{:08}.v{}.p{}'.format(self.phv, self.variable_version, self.participant_set)

    def set_dbgap_variable_link(self):
        """Automatically set dbgap_variable_link from study_accession and phv.
        
        Construct a URL to the dbGaP variable information page using a base URL
        and some fields from this SourceTrait.
        """
        VARIABLE_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id={}&phv={:08}'
        return VARIABLE_URL.format(self.study_accession, self.phv)

    def set_dbgap_study_link(self):
        """Automatically set dbgap_study_link from study_accession.
        
        Construct a URL to the dbGaP study information page using a base URL
        and some fields from this SourceTrait.
        """
        STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
        return STUDY_URL.format(self.study_accession)


class EncodedValue(models.Model):
    """Abstract superclass model for SourceEncodedValue and HarmonizedEncodedValue.
    
    SourceEncodedValue and HarmonizedEncodedValue models inherit from this Model,
    but the EncodedValue model itself won't be used to create a db table.
    
    Fields:
        category
        value
        web_date_added
    """
    
    category = models.CharField(max_length=45)
    value = models.CharField(max_length=100)
    web_date_added = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True


class SourceEncodedValue(EncodedValue):
    """Model for encoded values from 'raw' dbGaP data, as received from dbGaP.
    
    Extends the EncodedValue abstract superclass.
    
    Fields:
        source_trait
    """
    
    # This adds two fields: source_trait is the actual SourceTrait object that
    # this instance is linked to, and source_trait_id is the primary key of the
    # linked SourceTrait object.
    source_trait = models.ForeignKey(SourceTrait)
    # This will have an automatic primary key field, "id", since pk isn't set.
    
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
    # Set this model attribute to the value of this function, for the admin interface.
    get_source_trait_name.short_description = 'SourceTrait Name'
    
    def get_source_trait_study(self):
        """Get the name of the linked Study object.
        
        This function is used to properly display the Study Name column in the
        admin interface.
        
        Returns:
            study_name of the linked SourceTrait object
        """
        return self.source_trait.study.name
    # Set this model attribute to the value of this function, for the admin interface.
    get_source_trait_study.short_description = 'Study Name'