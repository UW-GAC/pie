"""Models for trait_browser app."""

# Model fields that are imported directly from topmed_pheno are preceded with i_
# ForeignKey fields do not have this prefix, since they are links within the
# Django database.
# Custom primary_key fields have db_column set as well, otherwise their column
# names in the backend db would have "_id" appended to them.

# Query to find out which fields to set null=True for:
# SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='topmed_pheno_devel_emeryl' AND IS_NULLABLE='YES' AND DATA_TYPE NOT IN ('varchar', 'text', 'tinyint') AND TABLE_NAME NOT IN ('harmonized_trait_data', 'subject', 'subject_archive');
# Query to find out which fields should be NullBooleanFields:
# SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='topmed_pheno_devel_emeryl' AND IS_NULLABLE='YES' AND DATA_TYPE='tinyint' AND TABLE_NAME NOT IN ('harmonized_trait_data', 'subject', 'subject_archive');

from django.db import models
from django.core.urlresolvers import reverse


from core.models import TimeStampedModel


INLINE_LIST_HTML = '\n'.join(('<p><strong>{list_title}</strong>',
    '<ul class="list-inline">{list_elements}</ul>', '</p>'))
LIST_ELEMENT_HTML = '<li>{element}</li>'
POPOVER_URL_HTML = '<a href="{url}" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{popover}">{name}</a>'
URL_HTML = '<a href="{url}">{name}</a>'
PANEL_HTML = '\n'.join(('<div class="panel panel-default">',
    '<div class="panel-heading">', '<h5 class="panel-title">{panel_title}</h5>', '</div>',
    '<div class="panel-body">{panel_body}', '</div>',
    '</div>'))

class SourceDBTimeStampedModel(TimeStampedModel):
    """Superclass for models pulled from the source db, with i_date_added and i_date_changed fields.
    """
    i_date_added = models.DateTimeField()
    i_date_changed = models.DateTimeField()

    class Meta:
        abstract = True


# Study models.
# ------------------------------------------------------------------------------
class GlobalStudy(SourceDBTimeStampedModel):
    """Model for "global study", which links studies between parent & child accessions.
    
    Global study connects data that are from the same parent study, but may be spread across
    parent and child accessions. Use GlobalStudy for all of the queries you think you might
    want to use Study for.
    """
    i_id = models.PositiveIntegerField('global study id', primary_key=True, db_column='study_id')
    i_name = models.CharField('global study name', max_length=200)

    class Meta:
        verbose_name_plural = 'GlobalStudies'

    def __str__(self):
        """Pretty printing."""
        return '{}, id={}'.format(self.i_name, self.i_id)


class Study(SourceDBTimeStampedModel):
    """Model for dbGaP study accessions.
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

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given Study instance."""
        return reverse('trait_browser:source:study:detail', kwargs={'pk': self.pk})

    def get_search_url(self):
        """Produce a url to initially populate checkboxes in the search page based on the study."""
        return reverse('trait_browser:source:search') + '?study={}'.format(self.i_accession)

    def get_name_link_html(self):
        """Get html for study's name linking to study detail page."""
        url_text = "{{% url 'trait_browser:source:study:detail' pk={} %}} ".format(self.pk)
        return URL_HTML.format(url=url_text, name=self.i_study_name)


class SourceStudyVersion(SourceDBTimeStampedModel):
    """Model for versions of each dbGaP study accession.
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
    

class Subcohort(SourceDBTimeStampedModel):
    """Model for subcohorts.
    """
    global_study = models.ForeignKey(GlobalStudy)
    i_id = models.PositiveIntegerField('id', primary_key=True, db_column='i_id')
    i_name = models.CharField('name', max_length=45)

    def __str__(self):
        """Pretty printing."""
        return '{} subcohort of global study {}, id={}'.format(self.i_name, self.global_study, self.i_id)


# Dataset related models.
# ------------------------------------------------------------------------------
class SourceDataset(SourceDBTimeStampedModel):
    """Model for dbGaP datasets from which SourceTraits are obtained.
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
    i_is_medication_dataset = models.NullBooleanField('is medication dataset?', blank=True, default=None)
    i_dbgap_date_created = models.DateTimeField('dbGaP date created', null=True, blank=True)
    i_date_visit_reviewed = models.DateTimeField('date visit was reviewed', null=True, blank=True)
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

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given SourceDataset instance."""
        return reverse('trait_browser:source:dataset', kwargs={'pk': self.pk})


class HarmonizedTraitSet(SourceDBTimeStampedModel):
    """Model for harmonized trait set from snuffles. Analagous to the SourceDataset
    for source traits.
    """
    i_id = models.PositiveIntegerField('harmonized trait set id', primary_key=True, db_column='i_id')
    i_trait_set_name = models.CharField('trait set name', max_length=45)
    i_flavor = models.PositiveIntegerField('flavor')
    i_version = models.PositiveIntegerField('version')
    i_description = models.CharField('description', max_length=1000)
    i_harmonized_by = models.CharField('harmonized by', max_length=45)
    i_git_commit_hash = models.CharField('git commit hash', max_length=40)
    i_is_demographic = models.BooleanField('is_demographic', default=False)
    i_is_longitudinal = models.BooleanField('is longitudinal?')
    component_html_detail = models.TextField(default='')

    def __str__(self):
        """Pretty printing."""
        return 'harmonized trait set {}, id={}'.format(self.i_trait_set_name, self.i_id)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given HarmonizedTraitSet instance."""
        return reverse('trait_browser:harmonized:detail', kwargs={'pk': self.pk})
    
    def get_trait_names(self):
        """Gets a list of trait_flavor_names for harmonized traits in this trait set."""
        return self.harmonizedtrait_set.values_list('trait_flavor_name', flat=True)
    
    def get_component_html(self):
        """Get html for component traits, in panels by harmonization unit and harmonized trait."""
        return '\n'.join([hunit.get_component_html() for hunit in self.harmonizationunit_set.all()])


class HarmonizationUnit(SourceDBTimeStampedModel):
    """Model for harmonization units from source db."""
    harmonized_trait_set = models.ForeignKey(HarmonizedTraitSet)
    i_id = models.PositiveIntegerField('harmonization unit id', primary_key=True, db_column='i_id')
    i_tag = models.CharField('tag', max_length=100)
    component_source_traits = models.ManyToManyField('SourceTrait', related_name='source_component_of_harmonization_unit')
    component_batch_traits = models.ManyToManyField('SourceTrait', related_name='batch_component_of_harmonization_unit')
    component_age_traits = models.ManyToManyField('SourceTrait', related_name='age_component_of_harmonization_unit')
    component_harmonized_trait_sets = models.ManyToManyField('HarmonizedTraitSet', related_name='harmonized_set_component_of_harmonization_unit')
    
    def __str__(self):
        """Pretty printing."""
        return 'Harmonization unit - id {} tagged {}'.format(self.i_id, self.i_tag)
    
    def get_all_source_traits(self):
        """Get a queryset of all the SourceTraits connected to this harmonization unit (age, batch, or source component)."""
        return self.component_source_traits.all() | self.component_batch_traits.all() | self.component_age_traits.all()
    
    def get_source_studies(self):
        """Get a list containing all of the studies linked to component traits for this unit."""
        return list(set([trait.source_dataset.source_study_version.study for trait in self.get_all_source_traits()]))

    def get_component_html(self):
        """Get html for a panel of component traits for the harmonization unit, with an inline list of included studies if applicable."""
        study_list = '\n'.join([study.get_name_link_html() for study in self.get_source_studies()])
        age_list = '\n'.join([trait.get_name_link_html() for trait in self.component_age_traits.all()])
        component_html = '\n'.join([trait.get_component_html(harmonization_unit=self) for trait in self.harmonizedtrait_set.all()])
        panel_body = []
        if len(study_list) > 0:
            study_html = INLINE_LIST_HTML.format(list_title='Included studies', list_elements=study_list)
            panel_body.append(study_html)
        if len(age_list) > 0:
            age_html = INLINE_LIST_HTML.format(list_title='Component age variables', list_elements=age_list)
            panel_body.append(age_html)
        panel_body.append(component_html)
        panel_body = '\n'.join(panel_body)
        unit_panel = PANEL_HTML.format(panel_title='Harmonization unit: {}'.format(self.i_tag), panel_body=panel_body)
        return unit_panel


# Trait models.
# ------------------------------------------------------------------------------
class Trait(SourceDBTimeStampedModel):
    """Abstract superclass model for SourceTrait and HarmonizedTrait.
    
    SourceTrait and HarmonizedTrait Models inherit from this Model, but the Trait
    model itself won't be used to create a db table.
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
    """
    source_dataset = models.ForeignKey(SourceDataset)
    # Adds .source_dataset (object) and .source_dataset_id (pk).
    i_detected_type = models.CharField('detected type', max_length=100, blank=True)
    i_dbgap_type = models.CharField('dbGaP type', max_length=100, blank=True)
    i_visit_number = models.CharField('visit number', max_length=45, blank=True)
    i_dbgap_variable_accession = models.PositiveIntegerField('dbGaP variable accession')
    i_dbgap_variable_version = models.PositiveIntegerField('dbGaP variable version')
    i_dbgap_description = models.TextField('dbGaP description')
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
        return '{} from dataset {} ({})'.format(self.variable_accession, self.dataset_accession, self.i_trait_name)
    
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

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given SourceTrait instance."""
        return reverse('trait_browser:source:detail', kwargs={'pk': self.pk})

    def get_name_link_html(self):
        """Get html for the trait name linked to the trait's detail page, with description as popover."""
        url_text = "{{% url 'trait_browser:source:detail' pk={} %}} ".format(self.pk)
        return POPOVER_URL_HTML.format(url=url_text, popover=self.i_description, name=self.i_trait_name)


class HarmonizedTrait(Trait):
    """Model for traits harmonized by the DCC.
    
    Extends the Trait abstract superclass. 
    """
    harmonized_trait_set = models.ForeignKey(HarmonizedTraitSet)
    # Adds .harmonized_trait_set (object) and .harmonized_trait_set_id (pk).
    i_data_type = models.CharField('data type', max_length=45)
    i_unit = models.CharField('unit', max_length=100, blank=True)
    i_has_batch = models.BooleanField('has batch?')
    i_is_unique_key = models.BooleanField('is unique key?')
    component_source_traits = models.ManyToManyField('SourceTrait', related_name='source_component_of_harmonized_trait')
    component_batch_traits = models.ManyToManyField('SourceTrait', related_name='batch_component_of_harmonized_trait')
    component_harmonized_trait_sets = models.ManyToManyField('HarmonizedTraitSet', related_name='harmonized_set_component_of_harmonized_trait')
    harmonization_units = models.ManyToManyField(HarmonizationUnit)
    trait_flavor_name = models.CharField(max_length=150)

    def __str__(self):
        """Pretty printing."""
        return self.trait_flavor_name

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

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given HarmonizedTrait instance.
        
        In this special case, goes to the detail page for the related trait set.
        """
        return reverse('trait_browser:harmonized:detail', kwargs={'pk': self.harmonized_trait_set.pk})

    def get_name_link_html(self):
        """Get html for the trait name linked to the harmonized trait's detail page, with description as popover."""
        url_text = "{{% url 'trait_browser:harmonized:detail' pk={} %}} ".format(self.pk)
        return POPOVER_URL_HTML.format(url=url_text, popover=self.i_description, name=self.trait_flavor_name)

    def get_component_html(self, harmonization_unit):
        """Get html for inline lists of source and harmonized component phenotypes for the harmonized trait."""
        source = [tr.get_name_link_html() for tr in (self.component_source_traits.all() & harmonization_unit.component_source_traits.all())]
        harmonized_trait_sets = [trait_set for trait_set in (self.component_harmonized_trait_sets.all() & harmonization_unit.component_harmonized_trait_sets.all())]
        harmonized = [tr.get_name_link_html() for trait_set in harmonized_trait_sets for tr in trait_set.harmonizedtrait_set.all() if not tr.i_is_unique_key]
        component_html = ''
        if len(source) > 0:
            trait_list = '\n'.join([LIST_ELEMENT_HTML.format(element=trait) for trait in source])
            component_html += INLINE_LIST_HTML.format(list_title='Component source phenotypes for {}'.format(self.trait_flavor_name), list_elements=trait_list)
        if len(harmonized) > 0:
            trait_list = '\n'.join([LIST_ELEMENT_HTML.format(element=trait) for trait in harmonized])
            component_html += '\n' + INLINE_LIST_HTML.format(list_title='Component harmonized phenotypes for {}'.format(self.trait_flavor_name), list_elements=trait_list)
        return component_html


# Encoded Value models.
# ------------------------------------------------------------------------------
class TraitEncodedValue(SourceDBTimeStampedModel):
    """Abstract superclass model for SourceEncodedValue and HarmonizedEncodedValue.
    
    SourceEncodedValue and HarmonizedEncodedValue models inherit from this Model,
    but the EncodedValue model itself won't be used to create a db table.
    """
    i_id = models.PositiveIntegerField('id', primary_key=True, db_column='i_id')
    i_category = models.CharField('category', max_length=45)
    i_value = models.CharField('value', max_length=1000)

    class Meta:
        abstract = True


class SourceTraitEncodedValue(TraitEncodedValue):
    """Model for encoded values from 'raw' dbGaP data, as received from dbGaP.
    
    Extends the TraitEncodedValue abstract superclass.
    """
    source_trait = models.ForeignKey(SourceTrait)
    # Adds .source_trait (object) and .source_trait_id (pk)
    
    def __str__(self):
        """Pretty printing."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.source_trait, self.i_value)
   

class HarmonizedTraitEncodedValue(TraitEncodedValue):
    """Model for encoded values from DCC harmonized traits.
    
    Extends the TraitEncodedValue superclass.
    """
    harmonized_trait = models.ForeignKey(HarmonizedTrait)
    # Adds .harmonized_trait (object) and .harmonized_trait_id (pk).
    
    def __str__(self):
        """Pretty printing of HarmonizedTraitEncodedValue objects."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.harmonized_trait, self.i_value)

