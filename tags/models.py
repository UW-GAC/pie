"""Models for the tags app."""

from django.conf import settings
from django.urls import reverse
from django.db import models

from core.models import TimeStampedModel
from . import querysets


class Tag(TimeStampedModel):
    """Model for phenotype tags, to be created by DCC staff."""

    # Will get an auto-created id field.
    title = models.CharField(max_length=255)
    lower_title = models.CharField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    instructions = models.TextField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)
    traits = models.ManyToManyField('trait_browser.SourceTrait', through='TaggedTrait')

    class Meta:
        verbose_name = 'phenotype tag'

    def save(self, *args, **kwargs):
        """Custom save method.

        Strips leading and trailing whitespace from the title.
        Automatically saves the lower_title field based on the title field.
        """
        # Strip all leading and trailing whitespace.
        self.title = self.title.strip()
        self.lower_title = self.title.lower()
        # Call the "real" save method.
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        """Pretty printing."""
        return 'Tag: {}'.format(self.lower_title)

    def get_absolute_url(self):
        return reverse('tags:tag:detail', args=[self.pk])


class TaggedTrait(TimeStampedModel):
    """Intermediate model for connecting Tags and SourceTraits."""

    trait = models.ForeignKey('trait_browser.SourceTrait', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)

    # Managers/custom querysets.
    objects = querysets.TaggedTraitQuerySet.as_manager()

    class Meta:
        verbose_name = 'tagged phenotype'
        unique_together = (('trait', 'tag'), )

    def __str__(self):
        """Pretty printing."""
        return 'Trait {} tagged {}'.format(self.trait.i_trait_name, self.tag.lower_title)
