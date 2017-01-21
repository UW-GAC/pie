from django.conf import settings
from django.db import models

class UserData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    saved_search_ids = models.CommaSeparatedIntegerField(max_length=255)