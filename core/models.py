"""Models to reuse across multiple apps."""

from django.db import models

class TimeStampedModel(models.Model):
    """Superclass for models with created and modified timestamps.
    
    An abstract base class model that provides selfupdating ``created`` and
    ``modified`` fields. 
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
