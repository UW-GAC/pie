"""Tables for the recipes app."""

import django_tables2 as tables

from . import models


class UnitRecipeTable(tables.Table):
    """django-tables2 table for displaying a list of UnitRecipes."""

    name = tables.LinkColumn(orderable=False)
    version = tables.Column(orderable=False)
    modified = tables.Column(orderable=False)
    created = tables.Column(orderable=False)

    class Meta:
        model = models.UnitRecipe
        fields = ('name', 'version', 'modified', 'created', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'bootstrap_tables2.html'


class HarmonizationRecipeTable(tables.Table):
    """django-tables2 table for displaying a list of HarmonizationRecipes."""

    name = tables.LinkColumn(orderable=False)
    target_name = tables.Column(orderable=False)
    version = tables.Column(orderable=False)
    created = tables.Column(orderable=False)
    modified = tables.Column(orderable=False)

    class Meta:
        model = models.HarmonizationRecipe
        fields = ('name', 'target_name', 'version', 'created', 'modified', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'bootstrap_tables2.html'
