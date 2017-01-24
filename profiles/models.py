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


class UserData(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    saved_search_ids = models.CommaSeparatedIntegerField(max_length=255)