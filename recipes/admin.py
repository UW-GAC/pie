"""Customization of the admin interface for the trait_browser app."""

from django.contrib import admin

from .models import UnitRecipe, HarmonizationRecipe


class UnitRecipeAdmin(admin.ModelAdmin):
    """Admin class for UnitRecipe objects."""
    list_display = ('name', 'creator', 'version', 'get_age_variables', 'get_batch_variables', 'get_phenotype_variables', )
    list_filter = ('creator', 'last_modifier', )
    search_fields = ('name', )

    def get_age_variables(self, unit):
        """Get the names of the age variables linked to this harmonization unit.
        
        This function is used to properly display the Age Variables column in the
        admin interface.
        
        Returns:
            csv list of names of the linked age variables
        """
        return ', '.join([age_var.i_trait_name for age_var in unit.age_variables.all()])
    get_age_variables.short_description = 'Age variables'

    def get_batch_variables(self, unit):
        """Get the names of the batch variables linked to this harmonization unit.
        
        This function is used to properly display the Age Variables column in the
        admin interface.
        
        Returns:
            csv list of names of the linked batch variables
        """
        return ', '.join([batch_var.i_trait_name for batch_var in unit.batch_variables.all()])
    get_batch_variables.short_description = 'Batch variables'

    def get_phenotype_variables(self, unit):
        """Get the names of the phenotype variables linked to this harmonization unit.
        
        This function is used to properly display the Age Variables column in the
        admin interface.
        
        Returns:
            csv list of names of the linked phenotype variables
        """
        return ', '.join([phenotype_var.i_trait_name for phenotype_var in unit.phenotype_variables.all()])
    get_phenotype_variables.short_description = 'Phenotype variables'


class HarmonizationRecipeAdmin(admin.ModelAdmin):
    """Admin class for HarmonizationRecipe objects."""
    list_display = ('name', 'creator', 'target_name', 'version', 'type', 'get_number_of_units', )
    list_filter = ('creator', 'last_modifier', 'type', )
    search_fields = ('name', 'target_name', )
    
    def get_number_of_units(self, recipe):
        """Get the number of harmonization units in a HarmonizationRecipe.
        
        This function is used to properly display the unit count in the Admin interface.
        
        Returns:
            int count of units linked to a HarmonizationRecipe.
        """
        return recipe.units.count()
    get_number_of_units.short_description = 'Number of units'

    
# Register models for showing them in the admin interface.
admin.site.register(UnitRecipe, UnitRecipeAdmin)
admin.site.register(HarmonizationRecipe, HarmonizationRecipeAdmin)