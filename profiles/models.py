from django.conf import settings
from django.db import models

from trait_browser.models import Study

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Search(TimeStampedModel):
    """Model for searches that anyone has ever saved"""

    param_text = models.CharField(max_length=100, db_index=True, null=False)
    param_studies = models.ManyToManyField(Study)
    search_count = models.IntegerField(default=1)


class UserData(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    # by default, Django uses the primary key of the foreign key related table
    saved_searches = models.ManyToManyField(Search)
