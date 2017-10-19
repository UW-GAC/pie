"""Models for the tags app."""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from trait_browser.models import SourceTrait


class Tag(TimeStampedModel):
    """Model for phenotype tags, to be created by DCC staff."""

    # Will get an auto-created id field.
    title = models.CharField(max_length=500)
    lower_title = models.CharField(max_length=500, unique=True)
    description = models.TextField()
    instructions = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    traits = models.ManyToManyField(SourceTrait, through='TaggedTrait')

    class Meta:
        verbose_name = 'phenotype tag'

    def save(self, *args, **kwargs):
        """Custom save method.

        Automatically saves the lower_title field based on the title field.
        """
        self.lower_title = self.title.lower()
        # Call the "real" save method.
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        """Pretty printing."""
        return 'Tag: {}'.format(self.lower_title)


class TaggedTrait(TimeStampedModel):
    """Intermediate model for connecting Tags and SourceTraits."""

    trait = models.ForeignKey(SourceTrait)
    tag = models.ForeignKey(Tag)
    recommended = models.BooleanField(default=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        """Pretty printing."""
        return 'Trait {} tagged {}'.format(self.trait.i_trait_name, self.tag.lower_title)
