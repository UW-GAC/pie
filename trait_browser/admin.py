"""Customization of the admin interface for the trait_browser app."""

from itertools import chain

from django.contrib import admin
from django.contrib.sites.models import Site

from .models import Study, SourceEncodedValue, SourceTrait


class ReadOnlyAdmin(admin.ModelAdmin):
    """SuperClass for non-editable admin models."""
    
    # There's not a good way to include these in unit-testing.
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class GlobalStudyAdmin(ReadOnlyAdmin):
    """Admin class for GlobalStudy objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_name', )
    list_filter = ('i_id', 'i_name', )
    search_fields = ('i_id', 'i_name', )


class StudyAdmin(ReadOnlyAdmin):
    """Admin class for Study objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_accession', 'i_study_name', )
    list_filter = ('i_accession', 'i_study_name', )
    search_fields = ('i_accession', 'i_study_name', )


class SourceStudyVersionAdmin(ReadOnlyAdmin):
    """Admin class for SourceStudyVersion objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('study_id', 'i_id', 'i_is_prerelease', 'i_is_deprecated', 'phs_version_string', )
    list_filter = ('study_id', )
    search_fields = ('study_id', 'phs_version_string', )
    

class SubcohortAdmin(ReadOnlyAdmin):
    """Admin class for Subcohort objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'study_id', 'i_name', )
    list_filter = ('i_id', 'i_study_id', )
    search_fields = ('i_id', 'study_id', 'i_name', )


class SourceDatasetAdmin(ReadOnlyAdmin):
    """Admin class for SourceDataset objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'i_accession', 'i_version', 'i_visit_code',
                    'i_visit_number', 'i_is_medication_dataset', 'i_dcc_description',
                    'i_dbgap_description', 'pht_version_string', )
    list_filter = ('i_id', 'i_accession', 'i_version', )
    search_fields = ('i_id', 'i_accession', 'pht_version_string', )


class SourceDatasetSubcohortsAdmin(ReadOnlyAdmin):
    """Admin class for SourceDatasetSubcohorts objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in Study._meta.get_fields()
        if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('i_id', 'subcohort_id', 'source_dataset_id', )
    list_filter = ('i_id', )
    search_fields = ('i_id', )





class SourceTraitAdmin(ReadOnlyAdmin):
    """Admin class for SourceTrait objects."""
    
    # Make all fields read-only
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceTrait._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = ('dcc_trait_id', 'name', 'data_type', 'study', 'web_date_added', )
    list_filter = ('web_date_added', 'data_type', 'study', )
    search_fields = ('dcc_trait_id', 'name', )


class SourceEncodedValueAdmin(ReadOnlyAdmin):
    """Admin class for SourceEncodedValue objects."""
    
    # Make all fields read-only.
    readonly_fields = list(set(chain.from_iterable(
        (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
        for field in SourceEncodedValue._meta.get_fields()
        # if not field.is_relation    # Exclude foreign keys from the results.
    )))
    # Set fields to display, filter, and search on.
    list_display = (
        'id', 'category', 'value', 'get_source_trait_name',
        'get_source_trait_study', 'web_date_added',
    )
    list_filter = ('web_date_added', )
    search_fields = ('category', 'id', )


# Register models for showing them in the admin interface.
admin.site.register(Study, StudyAdmin)
admin.site.register(SourceTrait, SourceTraitAdmin)
admin.site.register(SourceEncodedValue, SourceEncodedValueAdmin)
admin.site.unregister(Site)