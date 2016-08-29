"""Models for trait_browser app."""

# Model fields that are imported directly from Snuffles are preceded with i_
# ForeignKey fields do not have this prefix, since they are links within the
# Django database.
# Custom primary_key fields have db_column set as well, otherwise their column
# names in the backend db would have "_id" appended to them.

from django.db import models


# Study models.
# ------------------------------------------------------------------------------
class GlobalStudy(models.Model):
    """Model for "global study", which links studies between parent & child accessions.
    
    Global study connects data that are from the same parent study, but may be spread across
    parent and child accessions. Use GlobalStudy for all of the queries you think you might
    want to use Study for.
    
    Fields:
        i_id
        i_name
    """

    i_id = models.IntegerField(primary_key=True, db_column='study_id')
    i_name = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'GlobalStudies'


class Study(models.Model):
    """Model for dbGaP study accessions.
    
    Fields:
        i_accession
        i_study_name
        global_study
        phs
        dbgap_latest_version_link
    """
    
    i_accession = models.IntegerField(primary_key=True, db_column='i_accession')
    i_study_name = models.CharField(max_length=200)
    global_study = models.ForeignKey(GlobalStudy)
    # Adds .global_study (object) and .global_study_id (pk).
    phs = models.CharField(max_length=9)
    dbgap_latest_version_link = models.CharField(max_length=200)

    class Meta:
        # Fix pluralization of this model, because grammar. 
        verbose_name_plural = 'Studies'

    def __str__(self):
        """Pretty printing of Study objects."""
        return self.i_study_name
    
    def save(self, *args, **kwargs):
        """Custom save method for default dbGaP latest version study link.
        
        Automatically sets the value for the study's latest version dbGaP link.
        """
        self.phs = self.set_phs()
        self.dbgap_latest_version_link = self.set_dbgap_latest_version_link()
        # Call the "real" save method.
        super(Study, self).save(*args, **kwargs)
    
    def set_phs(self):
        """Automatically set phs from the study's accession number.
        
        Properly format the phs number for this study, so it's easier to get to
        in templates.
        """
        return 'phs{:06}'.format(self.phs)

    def set_dbgap_latest_version_link(self):
        """Automatically set dbgap_latest_version_link from the study's phs.
        
        Construct a URL to the dbGaP study information page using a base URL.
        Without a specified version number, the dbGaP link takes you to the
        latest version.
        """
        STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
        return STUDY_URL.format(self.phs)


class SourceStudyVersion(models.Model):
    """Model for versions of each dbGaP study accession.
    
    Fields:
        i_id
        study
        i_version
        i_participant_set
        i_dbgap_date
        i_prerelease
        i_deprecated
        phs_version_string
    """
    
    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    study = models.ForeignKey(Study)
    # Adds .study (object) and .study_id (pk).
    i_version = models.IntegerField()
    i_participant_set = models.IntegerField()
    i_dbagp_date = models.DateTimeField()
    i_prerelease = models.BooleanField()
    i_deprecated = models.BooleanField()
    phs_version_string = models.CharField(max_length=20)
    
    def save(self, *args, **kwargs):
        """Custom save method for setting default dbGaP accession strings.
        
        Automatically sets the value for phs_version_string.
        """
        self.phs_version_string = self.set_phs_version_string()
        # Call the "real" save method.
        super(Study, self).save(*args, **kwargs)
    
    def set_phs_version_string(self):
        """Automatically set phs_version_string from the study's phs value."""
        return '{}.v{}.p{}'.format(self.study.phs, self.i_version, self.i_participant_set)
    

class Subcohort(models.Model):
    """Model for subcohorts.
    
    Fields:
    
    """
    
    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    study = models.ForeignKey(Study)
    # Adds .study (object) and .study_id (pk).
    i_name = models.CharField(45)


# Dataset related models.
# ------------------------------------------------------------------------------
class SourceDataset(models.Model):
    """Model for dbGaP datasets from which SourceTraits are obtained.
    
    Fields:
        i_id
        study_version
        i_accession
        i_version
        i_visit_code
        i_visit_number
        i_is_subject_file
        i_study_subject_column
        i_is_medication_dataset
        i_dbgap_description
        i_dcc_description
    """
    
    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    source_study_version = models.ForeignKey(SourceStudyVersion)
    i_accession = models.IntegerField()
    i_version = models.IntegerField()
    i_visit_code = models.CharField(max_length=100)
    i_visit_number = models.CharField(max_length=45)
    i_is_subject_file = models.BooleanField()
    i_study_subject_column = models.CharField(max_length=45)
    i_is_medication_dataset = models.BooleanField()
    # These TextFields use longtext in MySQL rather than just text, like in snuffles.
    i_dbgap_description = models.TextField() 
    i_dcc_description = models.TextField()
    pht_version_string = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        """Custom save method for setting default dbGaP accession strings.
        
        Automatically sets the value for pht_version_string.
        """
        self.pht_version_string = self.set_pht_version_string()
        # Call the "real" save method.
        super(Study, self).save(*args, **kwargs)

    def set_pht_version_string(self):
        """Automatically set pht_version_string from the accession, version, and particpant set."""
        return 'pht{:06}.v{}.p{}'.format(self.i_accession, self.i_version, self.source_study_version.participant_set)

class SourceDatasetSubcohorts(models.Model):
    """Model for Subcohorts found within each dbGaP source dataset.
    
    Fields:
        i_id 
        source_dataset
        subcohort
    """
    
    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    source_dataset = models.ForeignKey(SourceDataset)
    # Adds .source_dataset (object) and .source_dataset_id (pk).
    subcohort = models.ForeignKey(Subcohort)
    # Adds .subcohort (object) and .subcohort_id (pk).


class SourceDatasetUniqueKeys(models.Model):
    """Model for unique keys within each dbGaP source dataset.
    
    Fields:
        i_id
        source_dataset
        source_trait
        i_is_visit_column
    """
    
    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    source_dataset = models.ForeignKey(SourceDataset)
    # Adds .source_dataset (object) and .source_dataset_id (pk).
    source_trait = models.ForeignKey(SourceTrait)
    # Adds .source_trait (object) and .source_trait_id (pk).
    i_is_visit_column = models.BooleanField()
    

class HarmonizedTraitSet(models.Model):
    """Model for harmonized trait set from snuffles. Analagous to the SourceDataset
    for source traits.
    
    Fields:
        i_id
        i_trait_set_name
        i_version
        i_description
    """

    i_id = models.IntegerField(primary_key=True, db_column='i_id')
    i_trait_set_name = models.CharField(max_length=45)
    i_version = models.IntegerField()
    i_description = models.CharField(max_length=1000)
    

# Trait models.
# ------------------------------------------------------------------------------
class Trait(models.Model):
    """Abstract superclass model for SourceTrait and HarmonizedTrait.
    
    SourceTrait and HarmonizedTrait Models inherit from this Model, but the Trait
    model itself won't be used to create a db table.
    
    Fields:
        i_trait_id
        i_trait_name
        i_description
        web_date_added
    """
    
    i_trait_id = models.PositiveIntegerField(primary_key=True, db_column='i_trait_id')
    i_trait_name = models.CharField(max_length=100, verbose_name='phenotype name')
    i_description = models.TextField(verbose_name='phenotype description')
    web_date_added = models.DateTimeField(auto_now_add=True, auto_now=False)

    class Meta:
        abstract = True


class SourceTrait(Trait):
    """Model for 'raw' source variable metadata as received from dbGaP.
    
    Extends the Trait abstract model.
    
    Fields:
        source_dataset
        i_detected_type
        i_dbgap_type
        i_visit_number
        i_dbgap_variable_accession
        i_dbgap_variable_version
        i_dbgap_comment
        i_dbgap_unit
        i_n_records
        i_n_missing
        study_accession
        dataset_accession
        variable_accession
        dbgap_study_link
        dbgap_variable_link
    """
    
    source_dataset = models.ForeignKey(SourceDataset)
    # Adds .source_dataset (object) and .source_dataset_id (pk).
    i_detected_type = models.CharField(max_length=100)
    i_dbgap_type = models.CharField(max_length=100)
    i_visit_number = models.CharField(max_length=45)
    i_dbgap_variable_accession = models.IntegerField()
    i_dbgap_variable_version = models.IntegerField()
    i_dbgap_comment = models.TextField()
    i_dbgap_unit = models.CharField(max_length=45)
    i_n_records = models.IntegerField()
    i_n_missing = models.IntegerField()
    # dbGaP accession numbers
    study_accession = models.CharField(max_length=20)
    dataset_accession = models.CharField(max_length=20)
    variable_accession = models.CharField(max_length=23)
    # dbGaP links.
    # Since these are URLFields, they will be validated as well-formed URLs.
    dbgap_study_link = models.URLField(max_length=200)
    dbgap_variable_link = models.URLField(max_length=200)
    
    def __str__(self):
        """Pretty printing of SourceTrait objects."""
        print_parms = ['i_trait_id', 'i_trait_name', 'i_detected_type', 'i_dbgap_unit', 'web_date_added']
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
        """Automatically set study_accession field from the linked SourceStudyVersion."""
        return self.source_dataset.source_study_version.phs_version_string

    def set_dataset_accession(self):
        """Automatically set dataset_accession field from the linked SourceDataset."""
        return self.source_dataset.pht_version_string
    
    def set_variable_accession(self):
        """Automatically set variable_accession from the linked SourceStudyVersion and dbGaP accession."""
        return 'phv{:08}.v{}.p{}'.format(self.dbgap_variable_accession,
                                         self.dbgap_variable_version,
                                         self.source_dataset.source_study_version.participant_set)

    def set_dbgap_variable_link(self):
        """Automatically set dbgap_variable_link from study_accession and dbgap_variable_accession.
        
        Construct a URL to the dbGaP variable information page using a base URL
        and some fields from this SourceTrait.
        """
        VARIABLE_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id={}&phv={:08}'
        return VARIABLE_URL.format(self.study_accession, self.dbgap_variable_accession)

    def set_dbgap_study_link(self):
        """Automatically set dbgap_study_link from study_accession.
        
        Construct a URL to the dbGaP study information page using a base URL
        and some fields from this SourceTrait.
        """
        STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
        return STUDY_URL.format(self.study_accession)


class HarmonizedTrait(Trait):
    """Model for traits harmonized by the DCC.
    
    Extends the Trait abstract superclass. 
    
    Fields:
        harmonized_trait_set
        i_data_type
        i_unit
        i_is_unique_key
    """
    
    harmonized_trait_set = models.ForeignKey(HarmonizedTraitSet)
    i_data_type = models.CharField(max_length=45)
    i_unit = models.CharField(max_length=100)
    i_is_unique_key = models.BooleanField()


# Encoded Value models.
# ------------------------------------------------------------------------------
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