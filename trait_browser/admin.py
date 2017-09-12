"""Customization of the admin interface for the trait_browser app."""

from django.contrib import admin
from django.contrib.sites.models import Site

from . import models


class GlobalStudyAdmin(admin.ModelAdmin):
    """Admin class for GlobalStudy objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_name', 'get_linked_studies', 'created', 'modified', )
    search_fields = ('i_id', 'i_name', )

    def get_linked_studies(self, global_study):
        """Get the names of the Study objects linked to this GlobalStudy.

        This function is used to properly display the Studies column in the
        admin interface.

        Returns:
            csv list of names of the linked Study objects
        """
        return ','.join([study.i_study_name for study in global_study.study_set.all()])
    get_linked_studies.short_description = 'Linked studies'


class StudyAdmin(admin.ModelAdmin):
    """Admin class for Study objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_accession', 'i_study_name', 'get_global_study', 'created', 'modified', )
    list_filter = ('global_study__i_name', )
    search_fields = ('i_accession', 'i_study_name', )

    def get_global_study(self, study):
        """Get global study name."""
        return study.global_study.i_name
    get_global_study.short_description = 'Global study name'


class SourceStudyVersionAdmin(admin.ModelAdmin):
    """Admin class for SourceStudyVersion objects."""

    # Set fields to display, filter, and search on.
    list_display = (
        'i_id', 'study', 'i_version', 'i_is_prerelease', 'i_is_deprecated', 'phs_version_string', 'created',
        'modified',
    )
    list_filter = ('study__i_accession', 'i_is_prerelease', 'i_is_deprecated', )
    search_fields = ('i_id', 'phs_version_string', )


class SubcohortAdmin(admin.ModelAdmin):
    """Admin class for Subcohort objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_name', 'global_study', 'created', 'modified', )
    list_filter = ('global_study__i_name', 'global_study__i_id', )
    search_fields = ('i_id', 'i_name', )


class SourceDatasetAdmin(admin.ModelAdmin):
    """Admin class for SourceDataset objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_version', 'i_dbgap_description', 'pht_version_string',
                    'i_visit_code', 'i_visit_number', 'i_is_medication_dataset',
                    'i_dcc_description', 'created', 'modified', )
    list_filter = ('source_study_version__study__i_accession',
                   'source_study_version__study__global_study__i_name',
                   'i_is_medication_dataset', 'i_is_subject_file', )
    search_fields = ('i_id', 'i_accession', 'pht_version_string', )


class HarmonizedTraitSetAdmin(admin.ModelAdmin):
    """Admin class for HarmonizedTraitSet objects."""

    # Set fields to display, filter, and search on.
    list_display = (
        'i_id', 'i_trait_set_name', 'i_version', 'i_flavor', 'i_is_longitudinal', 'i_harmonized_by', 'created',
        'modified',
    )
    search_fields = ('i_id', 'i_trait_set_name', )


class HarmonizationUnitAdmin(admin.ModelAdmin):
    """Admin class for HarmonizationUnit objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_tag', 'created', 'modified', )
    list_filter = ('harmonized_trait_set__i_id', )
    search_fields = ('i_id', 'i_tag', )


class SourceTraitAdmin(admin.ModelAdmin):
    """Admin class for SourceTrait objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_trait_id', 'i_trait_name', 'variable_accession', 'i_description',
                    'i_visit_number', 'i_is_unique_key', 'i_is_visit_column', 'created', 'modified')
    list_filter = ('source_dataset__source_study_version__study__i_accession',
                   'source_dataset__source_study_version__study__global_study__i_name',
                   'i_is_unique_key', 'i_is_visit_column', )
    search_fields = ('i_trait_id', 'i_trait_name', 'i_description', 'variable_accession', )


class HarmonizedTraitAdmin(admin.ModelAdmin):
    """Admin class for HarmonizedTrait objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_trait_id', 'i_trait_name', 'i_description', 'created', 'modified', )
    list_filter = ('i_is_unique_key', )
    search_fields = ('i_trait_id', 'i_trait_name', 'i_description',
                     'harmonized_trait_set__i_trait_set_name', )


class SourceTraitEncodedValueAdmin(admin.ModelAdmin):
    """Admin class for SourceTraitEncodedValue objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_category', 'i_value', 'source_trait', 'created', 'modified', )
    # There are too many traits with encoded values to use trait as a filter.
    list_filter = ('source_trait__source_dataset__source_study_version__study__i_accession',
                   'source_trait__source_dataset__source_study_version__study__global_study__i_name', )
    search_fields = ('i_id', 'i_category', 'i_value', 'source_trait__i_trait_name')


class HarmonizedTraitEncodedValueAdmin(admin.ModelAdmin):
    """Admin class for HarmonizedTraitEncodedValue objects."""

    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_category', 'i_value', 'harmonized_trait', 'created', 'modified', )
    search_fields = ('i_id', 'i_category', 'i_value', 'harmonized_trait__i_trait_name', )


# Register models for showing them in the admin interface.
admin.site.register(models.GlobalStudy, GlobalStudyAdmin)
admin.site.register(models.Study, StudyAdmin)
admin.site.register(models.SourceStudyVersion, SourceStudyVersionAdmin)
admin.site.register(models.Subcohort, SubcohortAdmin)
admin.site.register(models.SourceDataset, SourceDatasetAdmin)
admin.site.register(models.HarmonizedTraitSet, HarmonizedTraitSetAdmin)
admin.site.register(models.HarmonizationUnit, HarmonizationUnitAdmin)
admin.site.register(models.SourceTrait, SourceTraitAdmin)
admin.site.register(models.HarmonizedTrait, HarmonizedTraitAdmin)
admin.site.register(models.SourceTraitEncodedValue, SourceTraitEncodedValueAdmin)
admin.site.register(models.HarmonizedTraitEncodedValue, HarmonizedTraitEncodedValueAdmin)

admin.site.unregister(Site)
