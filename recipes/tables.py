"""Tables for the recipes app."""

import django_tables2 as tables

from .models import *


class UnitRecipeTable(tables.Table):
    """django-tables2 table for displaying a list of UnitRecipes."""
    
    name = tables.LinkColumn()
    version = tables.Column(orderable=False)
    modified = tables.Column(orderable=False)
    created = tables.Column(orderable=False)
    
    class Meta:
        model = UnitRecipe
        fields = ('name', 'version', 'modified', 'created', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'trait_browser/bootstrap_tables2.html'


class HarmonizationRecipeTable(tables.Table):
    """django-tables2 table for displaying a list of HarmonizationRecipes."""
    
    name = tables.LinkColumn(orderable=False)
    target_name = tables.Column(orderable=False)
    version = tables.Column(orderable=False)
    created = tables.Column(orderable=False)
    modified = tables.Column(orderable=False)
    
    class Meta:
        model = HarmonizationRecipe
        fields = ('name', 'target_name', 'version', 'created', 'modified', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'trait_browser/bootstrap_tables2.html'
