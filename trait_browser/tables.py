"""Table classes for trait_browser app, using django-tables2."""

import django_tables2 as tables

from . import models


class SourceTraitTable(tables.Table):
    """Class for tables2 handling of SourceTrait objects for nice table display.

    Django-tables2 enables pretty display of tables of data on django pages with
    builtin sorting and table layout. This class extends the tables.Table class
    for use with SourceTrait objects.
    """

    # Set custom column values that need extra settings.
    i_trait_name = tables.LinkColumn(
        'trait_browser:source:detail', args=[tables.utils.A('pk')], verbose_name='Phenotype name')
    i_description = tables.Column('Phenotype description', orderable=False)
    # Get the name from the Study linked to this trait.
    study_name = tables.Column('Study name', accessor='source_dataset.source_study_version.study.i_study_name')
    dbGaP_study = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.dbgap_study_link }}>{{ record.study_accession }}</a>')
    dbGaP_dataset = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.dbgap_dataset_link }}>{{ record.dataset_accession }}</a>')
    dbGaP_variable = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{ record.dbgap_variable_link }}>{{ record.variable_accession }}</a>')

    class Meta:
        model = models.SourceTrait
        fields = ('i_trait_name', 'i_description', 'study_name', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('dbGaP_dataset', 'dbGaP_variable', )


class HarmonizedTraitTable(tables.Table):
    """Class for tables2 handling of HarmonizedTrait objects for nice table display.

    Django-tables2 enables pretty display of tables of data on django pages with
    builtin sorting and table layout. This class extends the tables.Table class
    for use with HarmonizedTrait objects.
    """

    # Set custom column values that need extra settings.
    trait_flavor_name = tables.LinkColumn(
        'trait_browser:harmonized:detail', args=[tables.utils.A('harmonized_trait_set.pk')],
        verbose_name='Phenotype name')
    i_description = tables.Column('Phenotype description', orderable=False)

    class Meta:
        model = models.HarmonizedTrait
        fields = ('trait_flavor_name', 'i_description', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('trait_flavor_name', )


class StudyTable(tables.Table):
    """Class for tables2 handling of Study objects for nice table display.

    This class extends the django_tables2.Table class for use with Study
    objects. It is used for the Browse by Study page.
    """

    i_study_name = tables.LinkColumn(
        'trait_browser:source:study:detail', args=[tables.utils.A('pk')], verbose_name='Study name', orderable=False)
    dbGaP_accession = tables.TemplateColumn(
        orderable=False,
        template_code='<a target="_blank" href={{record.dbgap_latest_version_link}}>{{ record.phs }}</a>')

    class Meta:
        model = models.Study
        fields = ('i_study_name', )
        attrs = {'class': 'table table-striped table-hover table-bordered', 'style': 'width: auto;'}
        template = 'trait_browser/bootstrap_tables2.html'
        order_by = ('i_study_name', )
