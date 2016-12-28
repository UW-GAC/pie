"""Models for the recipes app."""

from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User

from trait_browser.models import SourceTrait


validate_alphanumeric_underscore = RegexValidator(regex=r'^[0-9a-zA-Z_]*$',
                                                  message='Only letters, numbers, and underscores (_) are allowed.')

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UnitRecipe(TimeStampedModel):
    """Model for harmonization recipe for one harmonization unit.
    """
    
    age_variables = models.ManyToManyField(SourceTrait, related_name='units_as_age_trait')
    batch_variables = models.ManyToManyField(SourceTrait, related_name='units_as_batch_trait')
    phenotype_variables =  models.ManyToManyField(SourceTrait, related_name='units_as_phenotype_trait')
    creator = models.ForeignKey(User, related_name='units_created_by')
    last_modifier = models.ForeignKey(User, related_name='units_last_modified_by')
    instructions = models.TextField(verbose_name='harmonization instructions')
    version = models.IntegerField(default=1)
    name = models.CharField(max_length=1000, verbose_name='harmonization unit name')

    class Meta:
        verbose_name = 'harmonization unit recipe'
        unique_together = (('creator', 'name'), )
    
    def __str__(self):
        """Pretty printing."""
        return '{} by {}, v{} (modified {})'.format(self.name, self.creator.username, self.version, self.modified.date())
    
    def get_absolute_url(self):
        """ """
        return reverse('recipes:unit:detail', kwargs={'pk': self.pk})


class HarmonizationRecipe(TimeStampedModel):
    """Model for harmonization recipes.
    """
    
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

    name = models.CharField(max_length=1000, verbose_name='harmonization recipe name')
    units = models.ManyToManyField(UnitRecipe, verbose_name='harmonization units')
    creator = models.ForeignKey(User, related_name='harmonization_recipes_created_by')
    last_modifier = models.ForeignKey(User, related_name='harmonization_recipes_last_modified_by')
    version = models.IntegerField(default=1)
    target_name = models.CharField(max_length=50, verbose_name='target phenotype variable name', validators=[validate_alphanumeric_underscore])
    target_description = models.CharField(max_length=1000, verbose_name='target phenotype variable description')
    encoded_values = models.TextField(verbose_name='definition of encoded values for target variable', blank=True)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, verbose_name='harmonization type')
    measurement_unit = models.CharField(max_length=100, verbose_name='unit of measurement')
    
    class Meta:
        unique_together = (('creator', 'name'), )

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization recipe {} by {}, v{}, with {} harmonization units (modified {})'.format(self.name, self.creator.username, self.version, self.units.count(), self.modified.date())
    
    def get_absolute_url(self):
        """ """
        return reverse('recipes:harmonization:detail', kwargs={'pk': self.pk})    