"""Models for the tags app."""

from django.apps import apps
from django.conf import settings
from django.db import models
from django.urls import reverse

from core.exceptions import DeleteNotAllowedError
from core.models import TimeStampedModel

from trait_browser.models import SourceTrait

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

    @property
    def archived_traits(self):
        """Return queryset of archived traits tagged with this tag."""
        archived_tagged_traits = apps.get_model('tags', 'TaggedTrait').objects.archived().filter(tag=self)
        return SourceTrait.objects.filter(pk__in=archived_tagged_traits.values_list('trait__pk', flat=True))

    @property
    def non_archived_traits(self):
        """Return queryset of non-archived traits tagged with this tag."""
        non_archived_tagged_traits = apps.get_model('tags', 'TaggedTrait').objects.non_archived().filter(tag=self)
        return SourceTrait.objects.filter(pk__in=non_archived_tagged_traits.values_list('trait__pk', flat=True))


class TaggedTrait(TimeStampedModel):
    """Intermediate model for connecting Tags and SourceTraits."""

    trait = models.ForeignKey('trait_browser.SourceTrait', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)

    # Managers/custom querysets.
    objects = querysets.TaggedTraitQuerySet.as_manager()

    class Meta:
        verbose_name = 'tagged phenotype'
        unique_together = (('trait', 'tag'), )

    def __str__(self):
        """Pretty printing."""
        return 'variable {} tagged {}'.format(self.trait.i_trait_name, self.tag.lower_title)

    def get_absolute_url(self):
        return reverse('tags:tagged-traits:pk:detail', args=[self.pk])

    def archive(self):
        """Set the TaggedTrait to archived."""
        self.archived = True
        self.save()

    def unarchive(self):
        """Set the TaggedTrait to unarchived."""
        self.archived = False
        self.save()

    def delete(self, *args, **kwargs):
        """Only allow unreviewed TaggedTrait objects to be deleted."""
        if hasattr(self, 'dcc_review'):
            if self.dcc_review.status == self.dcc_review.STATUS_CONFIRMED:
                raise DeleteNotAllowedError("Cannot delete a reviewed TaggedTrait.")
            else:
                self.archive()
        else:
            self.hard_delete()

    def hard_delete(self, *args, **kwargs):
        """Delete objects that cannot be deleted with overriden delete method."""
        super().delete(*args, **kwargs)


class DCCReview(TimeStampedModel):
    """Model to allow DCC staff to review a TaggedTrait."""

    tagged_trait = models.OneToOneField(TaggedTrait, on_delete=models.CASCADE, related_name='dcc_review')
    STATUS_FOLLOWUP = 0
    STATUS_CONFIRMED = 1
    STATUS_CHOICES = (
        (STATUS_FOLLOWUP, 'Needs study followup'),
        (STATUS_CONFIRMED, 'Confirmed'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES)
    comment = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'dcc review'
