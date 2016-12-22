"""Customization of the admin interface for the trait_browser app."""

from django.contrib import admin

from .models import UnitRecipe, HarmonizationRecipe


class UnitRecipeAdmin(admin.ModelAdmin):
    """Admin class for UnitRecipe objects."""
    list_display = ()
    list_filter = ()
    search_fields = ()


class HarmonizationRecipeAdmin(admin.ModelAdmin):
    """Admin class for HarmonizationRecipe objects."""
    list_display = ()
    list_filter = ()
    search_fields = ()

    
# Register models for showing them in the admin interface.
admin.site.register(UnitRecipe, UnitRecipeAdmin)
admin.site.register(HarmonizationRecipe, HarmonizationRecipeAdmin)