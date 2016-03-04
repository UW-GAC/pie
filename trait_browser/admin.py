"""Customization of the admin interface for the trait_browser app."""

from django.contrib              import admin
from django.contrib.sites.models import Site

from .models                     import Study, SourceEncodedValue, SourceTrait


class ReadOnlyAdmin(admin.ModelAdmin):
    """SuperClass for non-editable admin models."""
    
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class StudyAdmin(ReadOnlyAdmin):
    """Admin class for Study objects."""
    
    # Make all fields read-only
    readonly_fields = Study._meta.get_all_field_names()
    # Which fields to display
    list_display = ('study_id', 'dbgap_id', 'name', )
    # Allow filtering on these fields
    list_filter = ('dbgap_id', 'name', )
    # Allow searching based on these fields
    search_fields = ('dbgap_id', 'name', )


class SourceTraitAdmin(ReadOnlyAdmin):
    """Admin class for SourceTrait objects."""
    
    # Make all fields read-only
    readonly_fields = SourceTrait._meta.get_all_field_names()
    # Which fields to display
    list_display = ('dcc_trait_id', 'name', 'data_type', 'study', 'web_date_added', )
    # Allow filtering on these fields
    list_filter = ('web_date_added', 'data_type', 'study', )
    # Allow searching based on these fields
    search_fields = ('dcc_trait_id', 'name', )


class SourceEncodedValueAdmin(ReadOnlyAdmin):
    """Admin class for SourceEncodedValue objects."""
    
    # Make all fields read-only
    readonly_fields = SourceEncodedValue._meta.get_all_field_names()
    # Which fields to display
    list_display = (
        'id', 'category', 'value', 'get_source_trait_name', 
        'get_source_trait_study', 'web_date_added', 
    )
    # Allow filtering on these fields
    list_filter = ('web_date_added', )
    # Allow searching in these fields
    search_fields = ('category', 'id', )


# Register your models here.
admin.site.register(Study, StudyAdmin)
admin.site.register(SourceTrait, SourceTraitAdmin)
admin.site.register(SourceEncodedValue, SourceEncodedValueAdmin)
admin.site.unregister(Site)