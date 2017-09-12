"""Fill in specified model fields."""

from django.core.management.base import BaseCommand

from trait_browser import models


class Command(BaseCommand):
    """Management command to pull data from the source phenotype db."""

    help = 'For specified model fields, fill in field data using a standard method.'

    def _fill_harmonized_trait_set__component_html_detail(self):
        for harmonized_trait_set in models.HarmonizedTraitSet.objects.all():
            harmonized_trait_set.component_html_detail = harmonized_trait_set.get_component_html()
            harmonized_trait_set.save()

    # Methods to actually do the management command.
    def add_arguments(self, parser):
        """Add custom command line arguments to this management command."""
        parser.add_argument('--fields', action='store', nargs='+', type=str, required=True,
                            help='Model fields to fill data for, in the form of model_name__field_name.')

    def handle(self, *args, **options):
        """Handle the main functions of this management command.

        Arguments:
            **args and **options are handled as per the superclass handling; these
            argument dicts will pass on command line options
        """
        if 'harmonized_trait_set__component_html_detail' in options.get('fields'):
            print('Updating harmonized_trait_set__component_html_detail ...')
            self._fill_harmonized_trait_set__component_html_detail()
