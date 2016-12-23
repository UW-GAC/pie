"""Models for the recipes app."""

from django.db import models
from django.contrib.auth.models import User

from trait_browser.models import SourceTrait

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
    
    def __str__(self):
        """Pretty printing."""
        return '{:04d}: {} by {}, v{}'.format(self.pk, self.name, self.creator.username, self.version)


class HarmonizationRecipe(TimeStampedModel):
    """Model for harmonization recipes.
    """
    
    name = models.CharField(max_length=1000, verbose_name='harmonization recipe name')
    units = models.ManyToManyField(UnitRecipe, verbose_name='harmonization units')
    creator = models.ForeignKey(User, related_name='harmonization_recipes_created_by')
    last_modifier = models.ForeignKey(User, related_name='harmonization_recipes_last_modified_by')
    version = models.IntegerField(default=1)
    target_name = models.CharField(max_length=50, verbose_name='target phenotype variable name')
    target_description = models.CharField(max_length=1000, verbose_name='target phenotype variable description')
    encoded_values = models.TextField(verbose_name='definition of encoded values for target variable', blank=True)
    

    def __str__(self):
        """Pretty printing."""
        return 'Harmonization recipe {} by {}, v{}, with {} units.'.format(self.pk, self.creator.username, self.version, self.units.count())