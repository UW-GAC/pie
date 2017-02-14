from django.conf import settings
from django.db import models
from django.utils.http import urlencode
from django.core.urlresolvers import reverse

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
    search_type = models.CharField(max_length=25, null=False)

    def build_search_url(search_type, text, study_list):
        """
        This builds the appropriate url with query string.

        Django does not have built-in functionality to build a url with a query string,
        as such we need to build our own urls with query strings here.
        https://code.djangoproject.com/ticket/25582
        """
        search_url = reverse(':'.join(['trait_browser', search_type, 'search']))
        query_string_dict = {
            'text': text,
            'study': study_list
        }
        # doseq seems to allow for handling of lists as values
        # otherwise we would build a list of tuples
        return '?'.join([search_url, urlencode(query_string_dict, doseq=1)])

    def __str__(self):
        """Pretty printing."""
        msg = '\n'.join([
            'Search configuration',
            'param_text: {}'.format(self.param_text),
            'param_studies: {}'.format(self.param_studies.all()),
            'search_count: {}'.format(self.search_count),
            'search_type: {}'.format(self.search_type)
        ])
        return msg

    class Meta:
        verbose_name_plural = 'searches'


class UserData(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    # by default, Django uses the primary key of the foreign key related table
    saved_searches = models.ManyToManyField(Search, through="SavedSearchMeta")


class SavedSearchMeta(TimeStampedModel):
    search = models.ForeignKey(Search)
    user_data = models.ForeignKey(UserData)
    active = models.BooleanField(default=True)
