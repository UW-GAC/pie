"""Table classes for trait_browser app, using django-tables2."""

import django_tables2 as tables

from . import models


class StudyTable(tables.Table):
    """Class for tables2 handling of Study objects for nice table display.

    This class extends the django_tables2.Table class for use with Study
    objects. It is used for the Browse by Study page.
    """

    i_study_name = tables.LinkColumn(
        'trait_browser:source:studies:pk:detail', args=[tables.utils.A('pk')], verbose_name='Study',
        orderable=False)
    trait_count = tables.Column(accessor='study', verbose_name='Number of variables', orderable=False, empty_values=())
    dbGaP_accession = tables.TemplateColumn(
        orderable=False, verbose_name='dbGaP study',
        template_code='<a target="_blank" href={{record.dbgap_latest_version_link}}>{{ record.phs }}</a>')

    class Meta:
        model = models.Study
        fields = ('i_study_name', )
        attrs = {'class': 'table table-striped table-hover table-bordered', 'style': 'width: auto;'}
        template = 'django_tables2/bootstrap-responsive.html'
        order_by = ('i_study_name', )

    def render_trait_count(self, record):
        """Get the count of non-deprecated source traits for this study."""
        return '{:,}'.format(models.SourceTrait.objects.current().filter(
            source_dataset__source_study_version__study=record).count())


class SourceDatasetTable(tables.Table):
    """Class for table of source datasets for inheritance."""

    dataset_name = tables.LinkColumn(
        'trait_browser:source:datasets:detail', args=[tables.utils.A('pk')], verbose_name='Dataset',
        text=lambda record: record.dataset_name)
    i_dbgap_description = tables.Column(verbose_name='Description', orderable=False)
    trait_count = tables.Column(verbose_name='Number of variables', orderable=False, empty_values=())

    class Meta:
        model = models.SourceDataset
        fields = ('dataset_name', 'i_dbgap_description', 'trait_count', )
        attrs = {'class': 'table table-striped table-hover table-bordered', 'style': 'width: auto;'}
        template = 'django_tables2/bootstrap-responsive.html'

    def render_trait_count(self, record):
        return '{:,}'.format(record.sourcetrait_set.count())


class SourceDatasetTableFull(SourceDatasetTable):
    """Class for table of source datasets for listview."""

    study = tables.LinkColumn(
        'trait_browser:source:studies:pk:detail', args=[tables.utils.A('source_study_version.study.pk')],
        text=lambda record: record.source_study_version.study.i_study_name, verbose_name='Study', orderable=False)

    class Meta(SourceDatasetTable.Meta):
        fields = ('study', 'dataset_name', 'i_dbgap_description', 'trait_count', )
        order_by = ('study')


class SourceTraitTable(tables.Table):

    # Set custom column values that need extra settings.
    i_trait_name = tables.LinkColumn(
        'trait_browser:source:traits:detail', args=[tables.utils.A('pk')], verbose_name='Variable')
    i_description = tables.Column('Description', orderable=False)
    dbGaP_variable = tables.TemplateColumn(
        orderable=False, verbose_name='dbGaP variable',
        template_code='<a target="_blank" href={{ record.dbgap_link }}>{{ record.full_accession }}</a>')

    class Meta:
        fields = ('i_trait_name', 'i_description', 'dbGaP_variable', )
        model = models.SourceTrait
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'django_tables2/bootstrap-responsive.html'


class SourceTraitTableFull(SourceTraitTable):
    """Table for source traits with all information."""

    study = tables.LinkColumn(
        'trait_browser:source:studies:pk:detail',
        args=[tables.utils.A('source_dataset.source_study_version.study.pk')],
        text=lambda record: record.source_dataset.source_study_version.study.i_study_name,
        verbose_name='Study', orderable=False)
    dataset = tables.LinkColumn(
        'trait_browser:source:datasets:detail',
        args=[tables.utils.A('source_dataset.pk')],
        text=lambda record: record.source_dataset.dataset_name,
        verbose_name='Dataset', orderable=False)
    dbGaP_study = tables.TemplateColumn(
        orderable=False, verbose_name='dbGaP study',
        template_code='<a target="_blank" href={{ record.source_dataset.source_study_version.dbgap_link }}>{{ record.source_dataset.source_study_version.full_accession }}</a>')  # noqa: E501
    dbGaP_dataset = tables.TemplateColumn(
        orderable=False, verbose_name='dbGaP dataset',
        template_code='<a target="_blank" href={{ record.source_dataset.dbgap_link }}>{{ record.source_dataset.full_accession }}</a>')  # noqa: E501

    class Meta(SourceTraitTable.Meta):
        fields = (
            'i_trait_name', 'i_description', 'dataset', 'study', 'dbGaP_study', 'dbGaP_dataset', 'dbGaP_variable', )
        order_by = ('dbGaP_dataset', 'dbGaP_variable', )


class SourceTraitStudyTable(SourceTraitTable):
    """Table for displaying SourceTraits that are restricted to one study (e.g. in study views)."""

    dataset = tables.LinkColumn(
        'trait_browser:source:datasets:detail',
        args=[tables.utils.A('source_dataset.pk')],
        text=lambda record: record.source_dataset.dataset_name,
        verbose_name='Dataset', orderable=False)
    dbGaP_dataset = tables.TemplateColumn(
        orderable=False, verbose_name='dbGaP dataset',
        template_code='<a target="_blank" href={{ record.source_dataset.dbgap_link }}>{{ record.source_dataset.full_accession }}</a>')  # noqa: E501

    class Meta(SourceTraitTable.Meta):
        fields = ('i_trait_name', 'i_description', 'dataset', 'dbGaP_dataset', 'dbGaP_variable', )
        order_by = ('dbGaP_dataset', 'dbGaP_variable', )


class SourceTraitDatasetTable(SourceTraitTable):
    """Table for displaying SourceTraits that are restricted to one dataset (e.g. in dataset views)."""

    study = tables.LinkColumn(
        'trait_browser:source:studies:pk:detail',
        args=[tables.utils.A('source_dataset.source_study_version.study.pk')],
        text=lambda record: record.source_dataset.source_study_version.study.i_study_name,
        verbose_name='Study', orderable=False)

    class Meta(SourceTraitTable.Meta):
        fields = ('i_trait_name', 'i_description', 'study', 'dbGaP_variable')
        order_by = ('dbGaP_dataset', 'dbGaP_variable', )


class HarmonizedTraitTable(tables.Table):
    """Class for tables2 handling of HarmonizedTrait objects for nice table display.

    Django-tables2 enables pretty display of tables of data on django pages with
    builtin sorting and table layout. This class extends the tables.Table class
    for use with HarmonizedTrait objects.
    """

    # Set custom column values that need extra settings.
    trait_flavor_name = tables.LinkColumn(
        'trait_browser:harmonized:traits:detail', args=[tables.utils.A('harmonized_trait_set_version.pk')],
        verbose_name='Variable')
    i_description = tables.Column('Description', orderable=False)

    class Meta:
        model = models.HarmonizedTrait
        fields = ('trait_flavor_name', 'i_description', )
        attrs = {'class': 'table table-striped table-bordered table-hover table-condensed'}
        template = 'django_tables2/bootstrap-responsive.html'
        order_by = ('trait_flavor_name', )
