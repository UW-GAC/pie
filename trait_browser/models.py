"""Models for trait_browser app."""

# General guidelines:
#   * For pk fields, call them i_id and set db_column='i_id' so that the column is named appropriately
#       (otherwise they would be 'i_id_id')
#   * For fk fields, just use the Djangonic field name and appropriate field type
#   * All other fields should be named as their topmed_pheno name, but with 'i_' preceding the name
#   * Don't use any model-level defaults here (those are all handled at topmed_pheno)
#   * Include all NULL settings from topmed_pheno (except on string-like fields)
#   * Include all UNIQUE constraint settings from topmed_pheno (just in case)
#   * The model field type should match the topmed_pheno field type as closely as possible
#   * Do not replicate enum field choices from topmed_pheno

# Query to find out which fields to set null=True for:
# SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='topmed_pheno_devel_emeryl' AND IS_NULLABLE='YES' AND DATA_TYPE NOT IN ('varchar', 'text', 'tinyint') AND TABLE_NAME NOT IN ('harmonized_trait_data', 'subject', 'subject_archive');  # noqa
# Query to find out which fields should be NullBooleanFields:
# SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='topmed_pheno_devel_emeryl' AND IS_NULLABLE='YES' AND DATA_TYPE='tinyint' AND TABLE_NAME NOT IN ('harmonized_trait_data', 'subject', 'subject_archive');  # noqa

# Tables currently in topmed_pheno and wehther they are imported or not.
# +--------------------------------------------+
# | Tables_in_topmed_pheno_devel_emeryl        |
# +--------------------------------------------+
# | allowed_update_reason                      | y
# | component_age_trait                        | y
# | component_batch_trait                      | y
# | component_harmonized_trait_set             | y
# | component_source_trait                     | y
# | global_study                               | y
# | harmonization_unit                         | y
# | harmonized_dataset                         | n
# | harmonized_dataset_release                 | n
# | harmonized_dataset_trait_set               | n
# | harmonized_dataset_version                 | n
# | harmonized_function                        | n
# | harmonized_qc_document                     | n
# | harmonized_trait                           | y
# | harmonized_trait_data                      | n
# | harmonized_trait_encoded_values            | y
# | harmonized_trait_set                       | y
# | harmonized_trait_set_version               | y
# | harmonized_trait_set_version_update_reason | y
# | schema_changes                             | n
# | source_dataset                             | y
# | source_dataset_data_files                  | n
# | source_dataset_dictionary_files            | n
# | source_study_version                       | y
# | source_trait                               | y
# | source_trait_data                          | n
# | source_trait_encoded_values                | y
# | source_trait_inconsistent_metadata         | n
# | study                                      | y
# | subcohort                                  | y
# | subject                                    | n
# | subject_archive                            | n
# | view_harmonized_trait                      | n
# | view_harmonized_trait_all                  | n
# | view_source_trait                          | n
# | view_source_trait_all                      | n
# +--------------------------------------------+


from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils.text import Truncator
from core.models import TimeStampedModel

from . import querysets


INLINE_LIST_HTML = '\n'.join(
    ('<p><strong>{list_title}</strong>', '<ul class="list-inline">{list_elements}</ul>', '</p>'))
LIST_ELEMENT_HTML = '<li>{element}</li>'
POPOVER_URL_HTML = """<a href="{url}" data-toggle="popover" data-trigger="hover" data-placement="top"
                      data-content="{popover}">{name}</a>"""
URL_HTML = '<a href="{url}">{name}</a>'
PANEL_HTML = '\n'.join(
    ('<div class="panel panel-default">', '<div class="panel-heading">',
     '<h5 class="panel-title">{panel_title}</h5>', '</div>', '<div class="panel-body">{panel_body}', '</div>',
     '</div>')
)


class SourceDBTimeStampedModel(TimeStampedModel):
    """Superclass for models pulled from the source db, with i_date_added and i_date_changed fields."""

    i_date_added = models.DateTimeField()
    i_date_changed = models.DateTimeField()

    class Meta:
        abstract = True


# Study models.
# ------------------------------------------------------------------------------
class GlobalStudy(SourceDBTimeStampedModel):
    """Model for global_study from topmed_pheno, which links studies between parent & child accessions.

    Global study connects data that are from the same parent study, but may be spread across
    parent and child accessions. Use GlobalStudy for all of the queries you think you might
    want to use Study for.
    """

    i_id = models.PositiveIntegerField('global study id', primary_key=True, db_column='study_id')
    i_name = models.CharField('global study name', max_length=200, unique=True)
    i_topmed_accession = models.PositiveIntegerField('TOPMed accession', null=True, blank=True, unique=True)
    # In topmed_pheno, topmed_abbreviation has a unique constraint, but I can't do that here since Django just turns
    # all NULL string values into empty strings, and two empty strings are not counted as unique.
    i_topmed_abbreviation = models.CharField('TOPMed abbreviation', max_length=45, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Global studies'

    def __str__(self):
        """Pretty printing."""
        return '{}, id={}'.format(self.i_name, self.i_id)


class Study(SourceDBTimeStampedModel):
    """Model for study from topmed_pheno."""

    STUDY_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'

    global_study = models.ForeignKey(GlobalStudy, on_delete=models.CASCADE)
    # Adds .global_study (object) and .global_study_id (pk).
    i_accession = models.PositiveIntegerField('study accession', primary_key=True, db_column='i_accession')
    i_study_name = models.CharField('study name', max_length=200)
    phs = models.CharField(max_length=9)

    class Meta:
        # Fix pluralization of this model, because grammar.
        verbose_name_plural = 'Studies'

    def __str__(self):
        """Pretty printing."""
        return '{}, {}'.format(self.phs, self.i_study_name)

    def save(self, *args, **kwargs):
        """Custom save method to auto-set the phs field."""
        self.phs = self.set_phs()
        super(Study, self).save(*args, **kwargs)

    def set_phs(self):
        """Automatically set phs from the study's accession number.

        Properly format the phs number for this study, so it's easier to get to
        in templates.
        """
        return 'phs{:06}'.format(self.i_accession)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given Study instance."""
        return reverse('trait_browser:source:studies:pk:detail', kwargs={'pk': self.pk})

    def get_search_url(self):
        """Produce a url to initially populate checkboxes in the search page based on the study."""
        return reverse('trait_browser:source:studies:pk:traits:search', kwargs={'pk': self.pk})

    def get_dataset_search_url(self):
        """Produce a url to search datasets wtihin the study."""
        return reverse('trait_browser:source:studies:pk:datasets:search', kwargs={'pk': self.pk})

    def get_name_link_html(self):
        """Get html for study's name linking to study detail page."""
        url_text = "{{% url 'trait_browser:source:studies:pk:detail' pk={} %}} ".format(self.pk)
        return URL_HTML.format(url=url_text, name=self.i_study_name)

    def get_all_tags_count(self):
        """Return a count of the number of tags for which traits are tagged in this study."""
        return apps.get_model('tags', 'Tag').objects.filter(
            all_traits__source_dataset__source_study_version__study=self,
            all_traits__source_dataset__source_study_version__i_is_deprecated=False
        ).distinct().count()

    def get_archived_tags_count(self):
        """Return a count of the number of tags for which traits are tagged, but archived, in this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.archived().filter(
            trait__source_dataset__source_study_version__study=self
        ).current().aggregate(
            models.Count('tag', distinct=True))['tag__count']

    def get_non_archived_tags_count(self):
        """Return a count of the number of tags for which traits are tagged and NOT archived in this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.current().non_archived().filter(
            trait__source_dataset__source_study_version__study=self
        ).aggregate(
            models.Count('tag', distinct=True)
        )['tag__count']

    def get_all_tagged_traits(self):
        """Return a queryset of all of the TaggedTraits from this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.filter(
            trait__source_dataset__source_study_version__study=self,
        ).current()

    def get_archived_tagged_traits(self):
        """Return a queryset of the archived TaggedTraits from this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.archived().filter(
            trait__source_dataset__source_study_version__study=self
        ).current()

    def get_non_archived_tagged_traits(self):
        """Return a queryset of the non-archived TaggedTraits from this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.current().non_archived().filter(
            trait__source_dataset__source_study_version__study=self)

    def get_all_traits_tagged_count(self):
        """Return the count of all traits that have been tagged in this study."""
        return SourceTrait.objects.filter(
            source_dataset__source_study_version__study=self
        ).current().exclude(all_tags=None).count()

    def get_archived_traits_tagged_count(self):
        """Return the count of traits that have been tagged (and the tag archived) in this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.archived().filter(
            trait__source_dataset__source_study_version__study=self
        ).current().aggregate(
            models.Count('trait', distinct=True)
        )['trait__count']

    def get_non_archived_traits_tagged_count(self):
        """Return the count of traits that have been tagged (and the tag not archived) in this study."""
        return apps.get_model('tags', 'TaggedTrait').objects.current().non_archived().filter(
            trait__source_dataset__source_study_version__study=self).aggregate(
            models.Count('trait', distinct=True))['trait__count']

    def get_latest_version(self):
        """Return the most recent SourceStudyVersion linked to this study."""
        try:
            version = self.sourcestudyversion_set.filter(
                i_is_deprecated=False
            ).order_by(  # We can't use "latest" since it only accepts one field in Django 1.11.
                '-i_version',
                '-i_date_added'
            ).first()
        except ObjectDoesNotExist:
            return None
        return version

    def get_latest_version_link(self):
        """Return a dbGaP link to the page for the latest SourceStudyVersion."""
        return self.get_latest_version().dbgap_link


class SourceStudyVersion(SourceDBTimeStampedModel):
    """Model for source_study_version from topmed_pheno."""

    STUDY_VERSION_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={}'
    STUDY_VERSION_ACCESSION = '{}.v{}.p{}'

    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    # Adds .study (object) and .study_id (pk).
    i_id = models.PositiveIntegerField('source study version id', primary_key=True, db_column='i_id')
    i_version = models.PositiveIntegerField('version')
    i_participant_set = models.PositiveIntegerField('participant set')
    i_dbgap_date = models.DateTimeField('dbGaP date')
    i_is_prerelease = models.BooleanField('is prerelease?')
    i_is_deprecated = models.BooleanField('is deprecated?')
    full_accession = models.CharField(max_length=20)
    dbgap_link = models.URLField(max_length=200)

    def __str__(self):
        """Pretty printing."""
        return 'study {} version {}, id='.format(self.study, self.i_version, self.i_id)

    def save(self, *args, **kwargs):
        """Custom save method to auto-set full_accession and dbgap_link."""
        self.full_accession = self.set_full_accession()
        self.dbgap_link = self.set_dbgap_link()
        super(SourceStudyVersion, self).save(*args, **kwargs)

    def set_full_accession(self):
        """Automatically set full_accession from the study's phs value."""
        return self.STUDY_VERSION_ACCESSION.format(self.study.phs, self.i_version, self.i_participant_set)

    def set_dbgap_link(self):
        """Automatically set dbgap_link from dbGaP identifier information."""
        return self.STUDY_VERSION_URL.format(self.full_accession)

    def get_previous_version(self):
        """Return the previous version of this study."""
        # self.study.sourcestudyversion_set.filter(version_lt=self.version).latest('-i_date_added')
        return self.study.sourcestudyversion_set.filter(
            i_version__lte=self.i_version,
            i_date_added__lt=self.i_date_added
        ).order_by(
            '-i_version',
            '-i_date_added'
        ).first()


class Subcohort(SourceDBTimeStampedModel):
    """Model for subcohort from topmed_pheno."""

    global_study = models.ForeignKey(GlobalStudy, on_delete=models.CASCADE)
    i_id = models.PositiveIntegerField('id', primary_key=True, db_column='i_id')
    i_name = models.CharField('name', max_length=45)

    def __str__(self):
        """Pretty printing."""
        return '{} subcohort of global study {}, id={}'.format(self.i_name, self.global_study, self.i_id)


# Dataset related models.
# ------------------------------------------------------------------------------
class SourceDataset(SourceDBTimeStampedModel):
    """Model for source_dataset from topmed_pheno."""

    DATASET_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/dataset.cgi?study_id={}&pht={}'
    DATASET_ACCESSION = 'pht{:06}.v{}.p{}'

    source_study_version = models.ForeignKey(SourceStudyVersion, on_delete=models.CASCADE)
    # Adds .source_study_version (object) and .source_study_version_id (pk).
    i_id = models.PositiveIntegerField('dataset id', primary_key=True, db_column='i_id')
    i_accession = models.PositiveIntegerField('dataset accession')
    i_version = models.PositiveIntegerField('dataset version')
    i_is_subject_file = models.BooleanField('is subject file?')
    i_study_subject_column = models.CharField('study subject column name', max_length=45, blank=True)
    # The TextField uses longtext in MySQL rather than just text, like in topmed_pheno.
    i_dbgap_description = models.TextField('dbGaP description', blank=True)
    i_dbgap_date_created = models.DateTimeField('dbGaP date created', null=True, blank=True)
    full_accession = models.CharField(max_length=20)
    dbgap_filename = models.CharField(max_length=255, default='')
    dataset_name = models.CharField(max_length=255, default='')
    dbgap_link = models.URLField(max_length=200)

    # Managers/custom querysets.
    objects = querysets.SourceDatasetQuerySet.as_manager()

    def __str__(self):
        """Pretty printing."""
        return 'dataset {} of study {}, id={}, pht={}'.format(
            self.dataset_name, self.source_study_version.study, self.i_id, self.full_accession)

    def save(self, *args, **kwargs):
        """Custom save method to auto-set full_accession and dbgap_link."""
        self.full_accession = self.set_full_accession()
        self.dbgap_link = self.set_dbgap_link()
        super(SourceDataset, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given SourceDataset instance."""
        return reverse('trait_browser:source:datasets:detail', kwargs={'pk': self.pk})

    def set_full_accession(self):
        """Automatically set full_accession from the dataset's dbGaP identifiers."""
        return self.DATASET_ACCESSION.format(
            self.i_accession, self.i_version, self.source_study_version.i_participant_set)

    def set_dbgap_link(self):
        """Automatically set dbgap_link from dbGaP identifier information."""
        return self.DATASET_URL.format(self.source_study_version.full_accession, self.full_accession)

    def get_name_link_html(self, max_popover_words=80):
        """Get html for the dataset name linked to the dataset's detail page, with description as popover."""
        if not self.i_dbgap_description:
            description = '&mdash;'
        else:
            description = Truncator(self.i_dbgap_description).words(max_popover_words)
        return POPOVER_URL_HTML.format(url=self.get_absolute_url(), popover=description,
                                       name=self.dataset_name)

    def get_latest_version(self):
        """Find the most recent version of this dataset."""
        study = self.source_study_version.study
        current_study_version = self.source_study_version.study.get_latest_version()
        if current_study_version is None:
            return None
        # Find the same dataset associated with the current study version.
        try:
            current_dataset = SourceDataset.objects.get(
                source_study_version=current_study_version,
                i_accession=self.i_accession
            )
        except ObjectDoesNotExist:
            return None
        return current_dataset


class HarmonizedTraitSet(SourceDBTimeStampedModel):
    """Model for harmonized trait set from topmed_pheno. Analagous to the SourceDataset for source traits."""

    i_id = models.PositiveIntegerField('harmonized trait set id', primary_key=True, db_column='i_id')
    i_trait_set_name = models.CharField('trait set name', max_length=45)
    i_flavor = models.PositiveIntegerField('flavor')
    i_is_longitudinal = models.BooleanField('is longitudinal?', default=False)
    i_is_demographic = models.BooleanField('is_demographic', default=False)
    # TODO: remove the defaults in both of the above boolean fields.

    def __str__(self):
        """Pretty printing."""
        return 'harmonized trait set {}, id={}'.format(self.i_trait_set_name, self.i_id)


class AllowedUpdateReason(models.Model):
    """Model for allowed_update_reason from topmed_pheno."""

    # Note that this must be loaded during import BEFORE harmonized trait set version
    i_id = models.PositiveIntegerField('allowed update reason id', primary_key=True, db_column='i_id')
    i_abbreviation = models.CharField('abbreviation', max_length=45, unique=True)
    i_description = models.CharField('description', max_length=1000)

    def __str__(self):
        """Pretty printing."""
        return self.i_abbreviation


class HarmonizedTraitSetVersion(SourceDBTimeStampedModel):
    """Model for harmonized_trait_set_version from topmed_pheno."""

    harmonized_trait_set = models.ForeignKey(HarmonizedTraitSet, on_delete=models.CASCADE)
    i_id = models.PositiveIntegerField('harmonized trait set version id', primary_key=True, db_column='i_id')
    i_version = models.PositiveIntegerField('version')
    i_git_commit_hash = models.CharField('git commit hash', max_length=40)
    i_harmonized_by = models.CharField('harmonized by', max_length=45)
    i_is_deprecated = models.BooleanField('is deprecated?')
    update_reasons = models.ManyToManyField(AllowedUpdateReason)
    component_html_detail = models.TextField(default='')

    def __str__(self):
        """Pretty printing."""
        return 'Harm. trait set {} version {}, id={}'.format(
            self.harmonized_trait_set.i_trait_set_name, self.i_version, self.i_id)

    def get_trait_names(self):
        """Gets a list of trait_flavor_names for harmonized traits in this trait set version."""
        return self.harmonizedtrait_set.values_list('trait_flavor_name', flat=True)

    def get_component_html(self):
        """Get html for component traits, in panels by harmonization unit and harmonized trait."""
        return '\n'.join([hunit.get_component_html() for hunit in self.harmonizationunit_set.all()])

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given HarmonizedTraitSet instance."""
        return reverse('trait_browser:harmonized:traits:detail', kwargs={'pk': self.pk})


class HarmonizationUnit(SourceDBTimeStampedModel):
    """Model for harmonization_unit from topmed_pheno."""

    harmonized_trait_set_version = models.ForeignKey(
        HarmonizedTraitSetVersion, null=True, default=None, on_delete=models.CASCADE)
    # TODO: make the fk non-nullable and remove the default.
    i_id = models.PositiveIntegerField('harmonization unit id', primary_key=True, db_column='i_id')
    i_tag = models.CharField('tag', max_length=100)
    # From component_source_trait in topmed_pheno.
    component_source_traits = models.ManyToManyField(
        'SourceTrait', related_name='source_component_of_harmonization_unit')
    # From component_batch_trait in topmed_pheno.
    component_batch_traits = models.ManyToManyField(
        'SourceTrait', related_name='batch_component_of_harmonization_unit')
    # From component_age_trait in topmed_pheno.
    component_age_traits = models.ManyToManyField('SourceTrait', related_name='age_component_of_harmonization_unit')
    # From component_harmonized_trait_set in topmed_pheno.
    component_harmonized_trait_set_versions = models.ManyToManyField(
        'HarmonizedTraitSetVersion', related_name='harmonized_component_of_harmonization_unit')

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization unit - id {} tagged {}'.format(self.i_id, self.i_tag)

    def get_all_source_traits(self):
        """Get a queryset of all the SourceTraits components for this harmonization unit (age, batch, or source)."""
        return self.component_source_traits.all() | self.component_batch_traits.all() | self.component_age_traits.all()

    def get_source_studies(self):
        """Get a list containing all of the studies linked to component traits for this unit."""
        return list(set([trait.source_dataset.source_study_version.study for trait in self.get_all_source_traits()]))

    def get_component_html(self):
        """Get html for a panel of component traits for the harmonization unit.

        Includes an inline list of included studies if applicable.
        """
        study_list = '\n'.join([study.get_name_link_html() for study in self.get_source_studies()])
        age_list = '\n'.join([trait.get_name_link_html() for trait in self.component_age_traits.all()])
        component_html = '\n'.join([
            trait.get_component_html(harmonization_unit=self) for trait in self.harmonizedtrait_set.all()])
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
    """Model for source_trait from topmed_pheno.

    Extends the Trait abstract model.
    """

    VARIABLE_URL = 'http://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/variable.cgi?study_id={}&phv={:08}'
    VARIABLE_ACCESSION = 'phv{:08}.v{}.p{}'

    source_dataset = models.ForeignKey(SourceDataset, on_delete=models.CASCADE)
    # Adds .source_dataset (object) and .source_dataset_id (pk).
    i_detected_type = models.CharField('detected type', max_length=100, blank=True)
    i_dbgap_type = models.CharField('dbGaP type', max_length=100, blank=True)
    i_dbgap_variable_accession = models.PositiveIntegerField('dbGaP variable accession')
    i_dbgap_variable_version = models.PositiveIntegerField('dbGaP variable version')
    # i_description contains data from dbgap_description field.
    i_dbgap_comment = models.TextField('dbGaP comment', blank=True)
    i_dbgap_unit = models.CharField('dbGaP unit', max_length=45, blank=True)
    i_n_records = models.PositiveIntegerField('n records', null=True, blank=True)
    i_n_missing = models.PositiveIntegerField('n missing', null=True, blank=True)
    i_is_unique_key = models.NullBooleanField('is unique key?', blank=True)
    i_are_values_truncated = models.NullBooleanField('are values truncated?', default=None)
    # TODO: remove the default.
    full_accession = models.CharField(max_length=23)
    dbgap_link = models.URLField(max_length=200)

    # Managers/custom querysets.
    objects = querysets.SourceTraitQuerySet.as_manager()

    def __str__(self):
        """Pretty printing of SourceTrait objects."""
        return '{trait_name} ({phv}): dataset {pht}'.format(trait_name=self.i_trait_name,
                                                            phv=self.full_accession,
                                                            pht=self.source_dataset.full_accession)

    def save(self, *args, **kwargs):
        """Custom save method to auto-set full_accession and dbgap_link."""
        self.full_accession = self.set_full_accession()
        self.dbgap_link = self.set_dbgap_link()
        super(SourceTrait, self).save(*args, **kwargs)

    def set_full_accession(self):
        """Automatically set full_accession from the variable's dbGaP identifiers."""
        return self.VARIABLE_ACCESSION.format(
            self.i_dbgap_variable_accession, self.i_dbgap_variable_version,
            self.source_dataset.source_study_version.i_participant_set)

    def set_dbgap_link(self):
        """Automatically set dbgap_link from dbGaP identifier information."""
        return self.VARIABLE_URL.format(
            self.source_dataset.source_study_version.full_accession, self.i_dbgap_variable_accession)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given SourceTrait instance."""
        return reverse('trait_browser:source:traits:detail', kwargs={'pk': self.pk})

    @property
    def archived_tags(self):
        """Return queryset of archived tags linked to this trait."""
        archived_tagged_traits = apps.get_model('tags', 'TaggedTrait').objects.archived().filter(trait=self)
        return apps.get_model('tags', 'Tag').objects.filter(
            pk__in=archived_tagged_traits.values_list('tag__pk', flat=True))

    @property
    def non_archived_tags(self):
        """Return queryset of non-archived tags linked to this trait."""
        non_archived_tagged_traits = apps.get_model('tags', 'TaggedTrait').objects.non_archived().filter(trait=self)
        return apps.get_model('tags', 'Tag').objects.filter(
            pk__in=non_archived_tagged_traits.values_list('tag__pk', flat=True))

    def get_name_link_html(self, max_popover_words=80):
        """Get html for the trait name linked to the trait's detail page, with description as popover."""
        if not self.i_description:
            description = '&mdash;'
        else:
            description = Truncator(self.i_description).words(max_popover_words)
        return POPOVER_URL_HTML.format(url=self.get_absolute_url(), popover=description,
                                       name=self.i_trait_name)

    def get_latest_version(self):
        """Return the most recent version of a trait."""
        current_study_version = self.source_dataset.source_study_version.study.get_latest_version()
        if current_study_version is None:
            return None
        # Find the same trait associated with the current study version.
        try:
            current_trait = SourceTrait.objects.get(
                source_dataset__source_study_version=current_study_version,
                i_dbgap_variable_accession=self.i_dbgap_variable_accession
            )
        except ObjectDoesNotExist:
            return None
        return current_trait


class HarmonizedTrait(Trait):
    """Model for traits harmonized by the DCC.

    Extends the Trait abstract superclass.
    """

    harmonized_trait_set_version = models.ForeignKey(
        HarmonizedTraitSetVersion, null=True, default=None, on_delete=models.CASCADE)
    # TODO: make the fk non-nullable and remove the default.
    # Adds .harmonized_trait_set (object) and .harmonized_trait_set_id (pk).
    i_data_type = models.CharField('data type', max_length=45)
    i_unit = models.CharField('unit', max_length=100, blank=True)
    i_has_batch = models.BooleanField('has batch?')
    i_is_unique_key = models.BooleanField('is unique key?')
    # From component_source_trait in topmed_pheno.
    component_source_traits = models.ManyToManyField(
        'SourceTrait', related_name='source_component_of_harmonized_trait')
    # From component_batch_trait in topmed_pheno.
    component_batch_traits = models.ManyToManyField('SourceTrait', related_name='batch_component_of_harmonized_trait')
    # From component_harmonized_trait_set in topmed_pheno.
    component_harmonized_trait_set_versions = models.ManyToManyField(
        'HarmonizedTraitSetVersion', related_name='harmonized_component_of_harmonized_trait')
    # From a special query (HUNIT_QUERY in import_db) of component_batch_trait, component_source_trait, and
    # component_harmonized_trait_set from topmed_pheno.
    harmonization_units = models.ManyToManyField(HarmonizationUnit)
    # Created according to same rules as topmed_pheno.
    trait_flavor_name = models.CharField(max_length=150)

    # Managers/custom querysets.
    objects = querysets.HarmonizedTraitQuerySet.as_manager()

    class Meta:
        unique_together = (('harmonized_trait_set_version', 'i_trait_name'), )

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
        return '{}_{}'.format(self.i_trait_name, self.harmonized_trait_set_version.harmonized_trait_set.i_flavor)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given HarmonizedTrait instance.

        In this special case, goes to the detail page for the related trait set.
        """
        return self.harmonized_trait_set_version.get_absolute_url()

    def get_name_link_html(self, max_popover_words=80):
        """Get html for the trait name linked to the harmonized trait's detail page, with description as popover."""
        url_text = "{{% url 'trait_browser:harmonized:traits:detail' pk={} %}} ".format(
            self.harmonized_trait_set_version.pk)
        if not self.i_description:
            description = '&mdash;'
        else:
            description = Truncator(self.i_description).words(max_popover_words)
        return POPOVER_URL_HTML.format(url=url_text, popover=description, name=self.trait_flavor_name)

    def get_component_html(self, harmonization_unit):
        """Get html for inline lists of source and harmonized component phenotypes for the harmonized trait."""
        source = [tr.get_name_link_html() for tr in (
            self.component_source_traits.all() & harmonization_unit.component_source_traits.all())]
        harmonized_trait_set_versions = [trait_set_version for trait_set_version in (
            self.component_harmonized_trait_set_versions.all() &
            harmonization_unit.component_harmonized_trait_set_versions.all())]
        harmonized = [tr.get_name_link_html() for trait_set in harmonized_trait_set_versions
                      for tr in trait_set.harmonizedtrait_set.all()
                      if not tr.i_is_unique_key]
        component_html = ''
        if len(source) > 0:
            trait_list = '\n'.join([LIST_ELEMENT_HTML.format(element=trait) for trait in source])
            component_html += INLINE_LIST_HTML.format(
                list_title='Component study variables for {}'.format(self.trait_flavor_name),
                list_elements=trait_list)
        if len(harmonized) > 0:
            trait_list = '\n'.join([LIST_ELEMENT_HTML.format(element=trait) for trait in harmonized])
            component_html += '\n' + INLINE_LIST_HTML.format(
                list_title='Component harmonized variables for {}'.format(self.trait_flavor_name),
                list_elements=trait_list)
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
    """Model for source_trait_encoded_values from topmed_pheno.

    Extends the TraitEncodedValue abstract superclass.
    """

    source_trait = models.ForeignKey(SourceTrait, on_delete=models.CASCADE)
    # Adds .source_trait (object) and .source_trait_id (pk)

    def __str__(self):
        """Pretty printing."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.source_trait, self.i_value)


class HarmonizedTraitEncodedValue(TraitEncodedValue):
    """Model for harmonized_trait_encoded_values from topmed_pheno.

    Extends the TraitEncodedValue superclass.
    """

    harmonized_trait = models.ForeignKey(HarmonizedTrait, on_delete=models.CASCADE)
    # Adds .harmonized_trait (object) and .harmonized_trait_id (pk).

    def __str__(self):
        """Pretty printing of HarmonizedTraitEncodedValue objects."""
        return 'encoded value {} for {}\nvalue = {}'.format(self.i_category, self.harmonized_trait, self.i_value)
