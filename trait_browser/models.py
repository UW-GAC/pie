"""Models for trait_browser app."""

# Model fields that are imported directly from Snuffles are preceded with i_
# ForeignKey fields do not have this prefix, since they are links within the
# Django database.
# Custom primary_key fields have db_column set as well, otherwise their column
# names in the backend db would have "_id" appended to them.

from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Study models.
# ------------------------------------------------------------------------------
class GlobalStudy(TimeStampedModel):
    """Model for "global study", which links studies between parent & child accessions.
    
    Global study connects data that are from the same parent study, but may be spread across
    parent and child accessions. Use GlobalStudy for all of the queries you think you might
    want to use Study for.
    
    Fields:
        i_id
        i_name
    """

    i_id = models.PositiveIntegerField('global study id', primary_key=True, db_column='study_id')
    i_name = models.CharField('global study name', max_length=200)

    class Meta:
        verbose_name_plural = 'GlobalStudies'

    def __str__(self):
        """Pretty printing."""
        return '{}, id={}'.format(self.i_name, self.i_id)


class Study(TimeStampedModel):
    """Model for dbGaP study accessions.
    
    Fields:
        i_accession
        i_study_name
        global_study
        phs
        dbgap_latest_version_link
    """
    
    global_study = models.ForeignKey(GlobalStudy)
    # Adds .global_study (object) and .global_study_id (pk).
    i_accession = models.PositiveIntegerField('study accession', primary_key=True, db_column='i_accession')
    i_study_name = models.CharField('study name', max_length=200)
    phs = models.CharField(max_length=9)
    dbgap_latest_version_link = models.CharField(max_length=200)

    class Meta:
        # Fix pluralization of this model, because grammar. 
        verbose_name_plural = 'Studies'

    def __str__(self):
        """Pretty printing."""
        return '{}, {}'.format(self.phs, self.i_study_name)
    
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
        return 'phs{:06}'.format(self.i_accession)

    STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
    def set_dbgap_latest_version_link(self):
        """Automatically set dbgap_latest_version_link from the study's phs.
        
        Construct a URL to the dbGaP study information page using a base URL.
        Without a specified version number, the dbGaP link takes you to the
        latest version.
        """
        return self.STUDY_URL.format(self.phs)


class SourceStudyVersion(TimeStampedModel):
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
    
    study = models.ForeignKey(Study)
    # Adds .study (object) and .study_id (pk).
    i_id = models.PositiveIntegerField('source study version id', primary_key=True, db_column='i_id')
    i_version = models.PositiveIntegerField('version')
    i_participant_set = models.PositiveIntegerField('participant set')
    i_dbgap_date = models.DateTimeField('dbGaP date')
    i_is_prerelease = models.BooleanField('is prerelease?')
    i_is_deprecated = models.BooleanField('is deprecated?')
    phs_version_string = models.CharField(max_length=20)
    
    def __str__(self):
        """Pretty printing."""
        return 'study {} version {}, id='.format(self.study, self.i_version, self.i_id)
        
    def save(self, *args, **kwargs):
        """Custom save method for setting default dbGaP accession strings.
        
        Automatically sets the value for phs_version_string.
        """
        self.phs_version_string = self.set_phs_version_string()
        # Call the "real" save method.
        super(SourceStudyVersion, self).save(*args, **kwargs)
    
    def set_phs_version_string(self):
        """Automatically set phs_version_string from the study's phs value."""
        return '{}.v{}.p{}'.format(self.study.phs, self.i_version, self.i_participant_set)
    

class Subcohort(TimeStampedModel):
    """Model for subcohorts.
    
    Fields:
        study
        i_id
        i_name
    """
    
    study = models.ForeignKey(Study)
    # Adds .study (object) and .study_id (pk).
    i_id = models.PositiveIntegerField('id', primary_key=True, db_column='i_id')
    i_name = models.CharField('name', max_length=45)

    def __str__(self):
        """Pretty printing."""
        return '{} subcohort of study {}, id={}'.format(self.i_name, self.study, self.i_id)


# Dataset related models.
# ------------------------------------------------------------------------------
class SourceDataset(TimeStampedModel):
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
        subcohorts
    """
    
    source_study_version = models.ForeignKey(SourceStudyVersion)
    # Adds .source_study_version (object) and .source_study_version_id (pk).
    i_id = models.PositiveIntegerField('dataset id', primary_key=True, db_column='i_id')
    i_accession = models.PositiveIntegerField('dataset accession')
    i_version = models.PositiveIntegerField('dataset version')
    i_visit_code = models.CharField('visit code', max_length=100, blank=True)
    i_visit_number = models.CharField('visit number', max_length=45, blank=True)
    i_is_subject_file = models.BooleanField('is subject file?')
    i_study_subject_column = models.CharField('study subject column name', max_length=45, blank=True)
    i_is_medication_dataset = models.NullBooleanField('is medication dataset?', blank=True)
    # These TextFields use longtext in MySQL rather than just text, like in snuffles.
    i_dbgap_description = models.TextField('dbGaP description', blank=True) 
    i_dcc_description = models.TextField('DCC description', blank=True)
    pht_version_string = models.CharField(max_length=20)
    subcohorts = models.ManyToManyField(Subcohort)

    def __str__(self):
        """Pretty printing."""
        return 'dataset {} of study {}, id={}'.format(self.pht_version_string, self.source_study_version.study, self.i_id)

    def save(self, *args, **kwargs):
        """Custom save method for setting default dbGaP accession strings.
        
        Automatically sets the value for pht_version_string.
        """
        self.pht_version_string = self.set_pht_version_string()
        # Call the "real" save method.
        super(SourceDataset, self).save(*args, **kwargs)

    def set_pht_version_string(self):
        """Automatically set pht_version_string from the accession, version, and particpant set."""
        return 'pht{:06}.v{}.p{}'.format(self.i_accession, self.i_version, self.source_study_version.i_participant_set)


class HarmonizedTraitSet(TimeStampedModel):
    """Model for harmonized trait set from snuffles. Analagous to the SourceDataset
    for source traits.
    
    Fields:
        i_id
        i_trait_set_name
        i_flavor
        i_version
        i_description
    """

    i_id = models.PositiveIntegerField('harmonized trait set id', primary_key=True, db_column='i_id')
    i_trait_set_name = models.CharField('trait set name', max_length=45)
    i_flavor = models.PositiveIntegerField('flavor')
    i_version = models.PositiveIntegerField('version')
    i_description = models.CharField('description', max_length=1000)
    # This is a quoted string because the referenced model hasn't been defined yet.
    component_source_traits = models.ManyToManyField('SourceTrait')
    component_harmonized_traits = models.ManyToManyField('HarmonizedTrait')

    def __str__(self):
        """Pretty printing."""
        return 'harmonized trait set {}, id={}'.format(self.i_trait_set_name, self.i_id)

# Trait models.
# ------------------------------------------------------------------------------
class Trait(TimeStampedModel):
    """Abstract superclass model for SourceTrait and HarmonizedTrait.
    
    SourceTrait and HarmonizedTrait Models inherit from this Model, but the Trait
    model itself won't be used to create a db table.
    
    Fields:
        i_trait_id
        i_trait_name
        i_description
    """
    
    i_trait_id = models.PositiveIntegerField('phenotype id', primary_key=True, db_column='i_trait_id')
    i_trait_name = models.CharField('phenotype name', max_length=100)
    i_description = models.TextField('description')
    # Had to put i_is_unique_key in Harmonized and Source subclasses separately
    # because one can be NULL and the other can't.

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
    i_detected_type = models.CharField('detected type', max_length=100, blank=True)
    i_dbgap_type = models.CharField('dbGaP type', max_length=100, blank=True)
    i_visit_number = models.CharField('visit number', max_length=45, blank=True)
    i_dbgap_variable_accession = models.PositiveIntegerField('dbGaP variable accession')
    i_dbgap_variable_version = models.PositiveIntegerField('dbGaP variable version')
    i_dbgap_comment = models.TextField('dbGaP comment', blank=True)
    i_dbgap_unit = models.CharField('dbGaP unit', max_length=45, blank=True)
    i_n_records = models.PositiveIntegerField('n records', null=True, blank=True)
    i_n_missing = models.PositiveIntegerField('n missing', null=True, blank=True)
    i_is_visit_column = models.NullBooleanField('is visit column?', blank=True)
    i_is_unique_key = models.NullBooleanField('is unique key?', blank=True)
    # dbGaP accession numbers
    study_accession = models.CharField(max_length=20)
    dataset_accession = models.CharField(max_length=20)
    variable_accession = models.CharField(max_length=23)
    # dbGaP links.
    # Since these are URLFields, they will be validated as well-formed URLs.
    dbgap_study_link = models.URLField(max_length=200)
    dbgap_variable_link = models.URLField(max_length=200)
    dbgap_dataset_link = models.URLField(max_length=200)
    
    # Constants for custom save methods.
    VARIABLE_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id={}&phv={:08}'
    STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
    DATASET_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/dataset.cgi?study_id={}&pht={}'

    def __str__(self):
        """Pretty printing of SourceTrait objects."""
        return 'source trait {}, study {}, id={}'.format(self.i_trait_name, self.source_dataset.source_study_version.study, self.i_trait_id)
    
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
        self.dbgap_dataset_link = self.set_dbgap_dataset_link()
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
        return 'phv{:08}.v{}.p{}'.format(self.i_dbgap_variable_accession,
                                         self.i_dbgap_variable_version,
                                         self.source_dataset.source_study_version.i_participant_set)

    def set_dbgap_variable_link(self):
        """Automatically set dbgap_variable_link from study_accession and dbgap_variable_accession.
        
        Construct a URL to the dbGaP variable information page using a base URL
        and some fields from this SourceTrait.
        """
        return self.VARIABLE_URL.format(self.study_accession, self.i_dbgap_variable_accession)

    def set_dbgap_study_link(self):
        """Automatically set dbgap_study_link from study_accession.
        
        Construct a URL to the dbGaP study information page using a base URL
        and some fields from this SourceTrait.
        """
        return self.STUDY_URL.format(self.study_accession)

    def set_dbgap_dataset_link(self):
        """Automatically set dbgap_dataset_link from accession information.
        
        Construct a URL to the dbGaP dataset information page using a base URL and
        some fields from this SourceTrait.
        """
        return self.DATASET_URL.format(self.study_accession, self.source_dataset.i_accession)


class HarmonizedTrait(Trait):
    """Model for traits harmonized by the DCC.
    
    Extends the Trait abstract superclass. 
    
    Fields:
        harmonized_trait_set
        i_data_type
        i_unit
        i_is_unique_key
        component_source_traits
        component_harmonized_traits
    """
    
    harmonized_trait_set = models.ForeignKey(HarmonizedTraitSet)
    # Adds .harmonized_trait_set (object) and .harmonized_trait_set_id (pk).
    i_data_type = models.CharField('data type', max_length=45)
    i_unit = models.CharField('unit', max_length=100, blank=True)
    i_is_unique_key = models.BooleanField('is unique key?')
    # component_source_traits = models.ManyToManyField(SourceTrait)
    # # This is a quoted string because the referenced model hasn't been defined yet.
    # component_harmonized_traits = models.ManyToManyField('HarmonizedTrait')
    trait_flavor_name = models.CharField(max_length=150)

    def __str__(self):
        """Pretty printing."""
        return 'harmonized trait {}, id={}, from trait set {}'.format(self.i_trait_name, self.i_trait_id, self.harmonized_trait_set)

    def save(self, *args, **kwargs):
        """Custom save method for making the trait flavor name.
        
        Automatically sets the value for the harmonized trait's trait_flavor_name.
        """
        self.trait_flavor_name = self.set_trait_flavor_name()
        # Call the "real" save method.
        super(HarmonizedTrait, self).save(*args, **kwargs)
    
    def set_trait_flavor_name(self):
        """Automatically set trait_flavor_name from the trait's i_trait_name and the trait set's flavor name.
        
        Properly format the trait_flavor_name for this harmonized trait so that it's
        available for easy use later.
        """
        return '{}_{}'.format(self.i_trait_name, self.harmonized_trait_set.i_flavor)


# Encoded Value models.
# ------------------------------------------------------------------------------
class TraitEncodedValue(TimeStampedModel):
    """Abstract superclass model for SourceEncodedValue and HarmonizedEncodedValue.
    
    SourceEncodedValue and HarmonizedEncodedValue models inherit from this Model,
    but the EncodedValue model itself won't be used to create a db table.
    
    Fields:
        i_category
        i_value
    """
    
    i_id = models.PositiveIntegerField('id', primary_key=True, db_column='i_id')
    i_category = models.CharField('category', max_length=45)
    i_value = models.CharField('value', max_length=1000)

    class Meta:
        abstract = True


class SourceTraitEncodedValue(TraitEncodedValue):
    """Model for encoded values from 'raw' dbGaP data, as received from dbGaP.
    
    Extends the TraitEncodedValue abstract superclass.
    
    Fields:
        source_trait
    """
    
    source_trait = models.ForeignKey(SourceTrait)
    # Adds .source_trait (object) and .source_trait_id (pk)
    
    def __str__(self):
        """Pretty printing."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.source_trait, self.i_value)
   

class HarmonizedTraitEncodedValue(TraitEncodedValue):
    """Model for encoded values from DCC harmonized traits.
    
    Extends the TraitEncodedValue superclass.
    
    Fields:
    
    """
    harmonized_trait = models.ForeignKey(HarmonizedTrait)
    # Adds .harmonized_trait (object) and .harmonized_trait_id (pk).
    
    def __str__(self):
        """Pretty printing of HarmonizedTraitEncodedValue objects."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.harmonized_trait, self.i_value)


# Harmonization recipe models.
# ------------------------------------------------------------------------------
class UnitRecipe(TimeStampedModel):
    """Model for harmonization recipe for one harmonization unit.
    """
    
    age_variables = models.ManyToManyField(SourceTrait, related_name='units_as_age_trait')
    batch_variables = models.ManyToManyField(SourceTrait, related_name='units_as_batch_trait')
    phenotype_variables =  models.ManyToManyField(SourceTrait, related_name='units_as_phenotype_trait')
    creator = models.ForeignKey(User, related_name='units_created_by', blank=True, default='')
    last_modifier = models.ForeignKey(User, related_name='units_last_modified_by', blank=True, default='')
    instructions = models.TextField()
    version = models.IntegerField(default=1)
    name = models.CharField(max_length=1000)

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization unit recipe {} by {}, v{}'.format(self.pk, self.creator.username, self.version)


class HarmonizationRecipe(TimeStampedModel):
    """Model for harmonization recipes.
    """
    
    name = models.CharField(max_length=1000)
    units = models.ManyToManyField(UnitRecipe)
    creator = models.ForeignKey(User, related_name='harmonization_recipes_created_by', blank=True, default='')
    last_modifier = models.ForeignKey(User, related_name='harmonization_recipes_last_modified_by', blank=True, default='')
    version = models.IntegerField(default=1)
    target_name = models.CharField(max_length=50)
    target_description = models.CharField(max_length=1000)
    category_description = models.TextField()

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization recipe {} by {}, v{}, with {} units.'.format(self.pk, self.creator.username, self.version, self.units.count())