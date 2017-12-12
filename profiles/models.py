from django.conf import settings
from django.db import models
from django.utils.http import urlencode
from django.core.urlresolvers import reverse

from core.models import TimeStampedModel


class Search(TimeStampedModel):
    """Model for searches that anyone has ever searched for."""

    param_text = models.CharField(max_length=100, db_index=True, null=False)
    param_studies = models.ManyToManyField('trait_browser.Study')
    search_count = models.IntegerField(default=1)
    search_type = models.CharField(max_length=25, null=False)

    def build_search_url(self):
        """Build the appropriate url with query string.

        Django does not have built-in functionality to build a url with a query string,
        as such we need to build our own urls with query strings here.
        https://code.djangoproject.com/ticket/25582
        """
        search_url = reverse(':'.join(['trait_browser', self.search_type, 'search']))
        query_string_dict = {
            'text': self.param_text,
            'study': [x[0] for x in self.param_studies.values_list('i_accession')]
        }
        # doseq seems to allow for handling of lists as values
        # otherwise we would build a list of tuples
        return '?'.join([search_url, urlencode(query_string_dict, doseq=1)])

    def __str__(self):
        """Pretty printing."""
        msg = 'Search id: {}, search text: {}'.format(
            self.id,
            self.param_text
        )
        return msg

    class Meta:
        verbose_name_plural = 'searches'


class Profile(TimeStampedModel):
    """Model to hold data related to the User model."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    saved_searches = models.ManyToManyField(Search, through="SavedSearchMeta")
    taggable_studies = models.ManyToManyField('trait_browser.Study')


class SavedSearchMeta(TimeStampedModel):
    """M2M through model for saved searches."""

    search = models.ForeignKey(Search)
    profile = models.ForeignKey(Profile)
    active = models.BooleanField(default=True)
