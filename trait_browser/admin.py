from django.contrib              import admin
from .models                     import SourceEncodedValue, SourceTrait
from django.contrib.sites.models import Site

class ReadOnlyAdmin(admin.ModelAdmin):
    '''
    A SuperClass to set up non-editable (but viewable) models in the admin interface. 
    '''
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class SourceTraitAdmin(ReadOnlyAdmin):
    # Make all fields read-only
    readonly_fields = SourceTrait._meta.get_all_field_names()
    # Which fields to display
    list_display = ('dcc_trait_id', 'name', 'data_type', 'study_name', 'web_date_added', )
    # Allow filtering on these fields
    list_filter = ('web_date_added', 'data_type', 'study_name', )
    # Allow searching based on these fields
    search_fields = ('dcc_trait_id', 'name', )

class SourceEncodedValueAdmin(ReadOnlyAdmin):
    # Make all fields read-only
    readonly_fields = SourceEncodedValue._meta.get_all_field_names()
    # Which fields to display
    list_display = ('id', 'category', 'value', 'get_source_trait_name', 'get_source_trait_study', 'web_date_added', )
    # Allow filtering on these fields
    list_filter = ('web_date_added', )
    # Allow searching in these fields
    search_fields = ('category', 'id', )

# Register your models here.
admin.site.register(SourceTrait, SourceTraitAdmin)
admin.site.register(SourceEncodedValue, SourceEncodedValueAdmin)
admin.site.unregister(Site)
