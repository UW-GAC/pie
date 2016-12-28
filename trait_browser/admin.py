"""Customization of the admin interface for the trait_browser app."""

from itertools import chain

from django.contrib import admin
from django.contrib.sites.models import Site

from .models import GlobalStudy, HarmonizedTrait, HarmonizedTraitEncodedValue, HarmonizedTraitSet, SourceDataset, SourceStudyVersion, SourceTrait, SourceTraitEncodedValue, Study, Subcohort


class ReadOnlyAdmin(admin.ModelAdmin):
    """SuperClass for non-editable admin models."""
    
    # There's not a good way to include these in unit-testing.
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Make these available to add to each model's admin.
    list_display = ('created', 'modified', )


class GlobalStudyAdmin(ReadOnlyAdmin):
    """Admin class for GlobalStudy objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in GlobalStudy._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_name', 'get_linked_studies', ) + ReadOnlyAdmin.list_display
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


class StudyAdmin(ReadOnlyAdmin):
    """Admin class for Study objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_accession', 'i_study_name', 'get_global_study', ) + ReadOnlyAdmin.list_display
    list_filter = ('global_study__i_name', )
    search_fields = ('i_accession', 'i_study_name', )

    def get_global_study(self, study):
        """Get global study name."""
        return study.global_study.i_name
    get_global_study.short_description = 'Global study name'


class SourceStudyVersionAdmin(ReadOnlyAdmin):
    """Admin class for SourceStudyVersion objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceStudyVersion._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'study', 'i_version', 'i_is_prerelease', 'i_is_deprecated', 'phs_version_string', ) + ReadOnlyAdmin.list_display
    list_filter = ('study__i_accession', 'i_is_prerelease', 'i_is_deprecated', )
    search_fields = ('i_id', 'phs_version_string', )
    

class SubcohortAdmin(ReadOnlyAdmin):
    """Admin class for Subcohort objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Subcohort._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_name', 'study', ) + ReadOnlyAdmin.list_display
    list_filter = ('study__i_study_name', 'study__i_accession', )
    search_fields = ('i_id', 'i_name', )


class SourceDatasetAdmin(ReadOnlyAdmin):
    """Admin class for SourceDataset objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceDataset._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_version', 'i_dbgap_description', 'pht_version_string',
                    'i_visit_code', 'i_visit_number', 'i_is_medication_dataset',
                    'i_dcc_description', )  + ReadOnlyAdmin.list_display
    list_filter = ('source_study_version__study__i_accession',
                   'source_study_version__study__global_study__i_name',
                   'i_is_medication_dataset', 'i_is_subject_file', )
    search_fields = ('i_id', 'i_accession', 'pht_version_string', )


class HarmonizedTraitSetAdmin(ReadOnlyAdmin):
    """Admin class for HarmonizedTraitSet objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in HarmonizedTraitSet._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_trait_set_name', 'i_version', 'i_flavor' ) + ReadOnlyAdmin.list_display
    search_fields = ('i_id', 'i_trait_set_name', )


class SourceTraitAdmin(ReadOnlyAdmin):
    """Admin class for SourceTrait objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceTrait._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_trait_id', 'i_trait_name', 'variable_accession', 'i_description',
                    'i_visit_number', 'i_is_unique_key', 'i_is_visit_column') + ReadOnlyAdmin.list_display
    list_filter = ('source_dataset__source_study_version__study__i_accession',
                   'source_dataset__source_study_version__study__global_study__i_name',
                   'i_is_unique_key', 'i_is_visit_column', )
    search_fields = ('i_trait_id', 'i_trait_name', 'i_description', 'variable_accession', )


class HarmonizedTraitAdmin(ReadOnlyAdmin):
    """Admin class for HarmonizedTrait objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in HarmonizedTrait._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_trait_id', 'i_trait_name', 'i_description', ) + ReadOnlyAdmin.list_display
    list_filter = ('i_is_unique_key', )
    search_fields = ('i_trait_id', 'i_trait_name', 'i_description',
                     'harmonized_trait_set__i_trait_set_name', )


class SourceTraitEncodedValueAdmin(ReadOnlyAdmin):
    """Admin class for SourceTraitEncodedValue objects."""
    
    # Make all fields read-only.
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceTraitEncodedValue._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_category', 'i_value', 'source_trait', ) + ReadOnlyAdmin.list_display
    # There are too many traits with encoded values to use trait as a filter.
    list_filter = ('source_trait__source_dataset__source_study_version__study__i_accession',
                   'source_trait__source_dataset__source_study_version__study__global_study__i_name', )
    search_fields = ('i_id', 'i_category', 'i_value', 'source_trait__i_trait_name')


class HarmonizedTraitEncodedValueAdmin(ReadOnlyAdmin):
    """Admin class for HarmonizedTraitEncodedValue objects."""
    
    # Make all fields read-only.
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in HarmonizedTraitEncodedValue._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_category', 'i_value', 'harmonized_trait', ) + ReadOnlyAdmin.list_display
    search_fields = ('i_id', 'i_category', 'i_value', 'harmonized_trait__i_trait_name', )


# Register models for showing them in the admin interface.
admin.site.register(GlobalStudy, GlobalStudyAdmin)
admin.site.register(Study, StudyAdmin)
admin.site.register(SourceStudyVersion, SourceStudyVersionAdmin)
admin.site.register(Subcohort, SubcohortAdmin)
admin.site.register(SourceDataset, SourceDatasetAdmin)
admin.site.register(HarmonizedTraitSet, HarmonizedTraitSetAdmin)
admin.site.register(SourceTrait, SourceTraitAdmin)
admin.site.register(HarmonizedTrait, HarmonizedTraitAdmin)
admin.site.register(SourceTraitEncodedValue, SourceTraitEncodedValueAdmin)
admin.site.register(HarmonizedTraitEncodedValue, HarmonizedTraitEncodedValueAdmin)

admin.site.unregister(Site)