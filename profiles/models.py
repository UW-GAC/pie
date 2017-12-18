from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.http import urlencode

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

    def __str__(self):
        """Pretty printing for Profile objects."""
        return 'Profile for user {}'.format(self.user.email)


# Taken from post about how to extend the Django user model.
# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class SavedSearchMeta(TimeStampedModel):
    """M2M through model for saved searches."""

    search = models.ForeignKey(Search)
    profile = models.ForeignKey(Profile)
    active = models.BooleanField(default=True)
