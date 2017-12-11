import factory
import factory.fuzzy

from core.factories import UserFactory
from . import models


class SearchFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Search
        django_get_or_create = ('param_text', 'search_type')

    # defaults
    param_text = factory.Faker('catch_phrase')
    search_type = 'source'

    @factory.post_generation
    def param_studies(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for study in extracted:
                self.param_studies.add(study)


class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Profile

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def saved_searches(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for search in extracted:
                self.saved_searches.add(search)


class SavedSearchMetaFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SavedSearchMeta

    profile = factory.SubFactory(ProfileFactory)
    search = factory.SubFactory(SearchFactory)
