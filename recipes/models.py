"""Models for the recipes app."""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models

from core.models import TimeStampedModel


validate_alphanumeric_underscore = RegexValidator(regex=r'^[0-9a-zA-Z_]*$',
                                                  message='Only letters, numbers, and underscores (_) are allowed.')

validate_encoded_values = RegexValidator(regex=r'^(.*: .*\n)*(.*: .*)$',
                                         message='Invalid format for encoded values definitions.')


class UnitRecipe(TimeStampedModel):
    """Model for harmonization recipe for one harmonization unit."""

    UNIT_RECODE = 'unit_recode'
    CATEGORY_RECODE = 'category_recode'
    FORMULA = 'formula'
    OTHER = 'other'
    TYPE_CHOICES = (
        (UNIT_RECODE, 'recode variable for different units of measurement'),
        (CATEGORY_RECODE, 'recode variable for new encoded value category definitions'),
        (FORMULA, 'calculate variable from a formula'),
        (OTHER, 'other'),
    )

    age_variables = models.ManyToManyField('trait_browser.SourceTrait', related_name='units_as_age_trait', blank=True)
    batch_variables = models.ManyToManyField('trait_browser.SourceTrait', related_name='units_as_batch_trait', blank=True)
    phenotype_variables = models.ManyToManyField('trait_browser.SourceTrait', related_name='units_as_phenotype_trait', blank=True)
    harmonized_phenotype_variables = models.ManyToManyField('trait_browser.HarmonizedTrait', related_name='units_as_phenotype_trait',
                                                            blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='units_created_by')
    last_modifier = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='units_last_modified_by')
    instructions = models.TextField(verbose_name='harmonization instructions')
    version = models.IntegerField(default=1)
    name = models.CharField(max_length=255, verbose_name='harmonization unit name')
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, verbose_name='harmonization type')

    class Meta:
        verbose_name = 'harmonization unit recipe'
        unique_together = (('creator', 'name'), )

    def __str__(self):
        """Pretty printing."""
        return '{} by {}, v{}'.format(self.name, self.creator.email, self.version)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given UnitRecipe instance."""
        return reverse('recipes:unit:detail', kwargs={'pk': self.pk})


class HarmonizationRecipe(TimeStampedModel):
    """Model for harmonization recipes.

    Harmonization recipes provide instructions for combining harmonization units
    to create the target harmonized variable.
    """

    name = models.CharField(max_length=255, verbose_name='harmonization recipe name')
    units = models.ManyToManyField(UnitRecipe, verbose_name='harmonization units')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='harmonization_recipes_created_by')
    last_modifier = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='harmonization_recipes_last_modified_by')
    version = models.IntegerField(default=1)
    target_name = models.CharField(
        max_length=50, verbose_name='target phenotype variable name', validators=[validate_alphanumeric_underscore])
    target_description = models.TextField(verbose_name='target phenotype variable description')
    encoded_values = models.TextField(
        verbose_name='definition of encoded values for target variable', blank=True,
        validators=[validate_encoded_values])
    measurement_unit = models.CharField(max_length=100, verbose_name='unit of measurement')

    class Meta:
        unique_together = (('creator', 'name'), )

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization recipe {} by {}, v{}'.format(self.name, self.creator.email, self.version)

    def get_absolute_url(self):
        """Gets the absolute URL of the detail page for a given HarmonizationRecipe instance."""
        return reverse('recipes:harmonization:detail', kwargs={'pk': self.pk})

    def get_encoded_values_dict(self):
        """Get a dict of category, value pairs by parsing the encoded_values field.

        Process the encoded_values field, which was input by a user in a specific format,
        into a more usable Python dictionary with category as the keys and value as the values.

        Returns:
            dict of (category, value) pairs, both as strings
        """
        return dict([line.split(': ') for line in self.encoded_values.split('\r\n')])

    def get_config(self):
        """Get a phenotype harmonization workflow config file from this HarmonizationRecipe.

        Produce a formatted xml config file for the DCC phenotype harmonization
        workflow based on the information in the harmonization unit recipes for
        this HarmonizationRecipe.
        """
        pass
