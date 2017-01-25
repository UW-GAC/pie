from django.conf import settings
from django.db import models

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserSearches(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    # by default, Django uses the primary key of the foreign key related table
    search = models.ForeignKey('trait_browser.Searches')
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'search')