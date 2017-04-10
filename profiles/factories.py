import factory
import factory.fuzzy

from core.factories import UserFactory
from .models import *
from trait_browser.factories import StudyFactory

class SearchFactory(factory.DjangoModelFactory):
    class Meta:
        model = Search
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


class UserDataFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserData

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
        model = SavedSearchMeta

    user_data = factory.SubFactory(UserDataFactory)
    search = factory.SubFactory(SearchFactory)
