import factory
import factory.fuzzy

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


# Can't have a ProfileFactory because creating the user already creates the profile.
#
# from core.factories import UserFactory
# class ProfileFactory(factory.DjangoModelFactory):
#     class Meta:
#         model = models.Profile
#
#     user = factory.SubFactory(UserFactory)
#
#     @factory.post_generation
#     def saved_searches(self, create, extracted, **kwargs):
#         if not create:
#             return
#         if extracted:
#             for search in extracted:
#                 self.saved_searches.add(search)


# Can't use this factory because creating the profile through a SubFactory doesn't work.
# You'll just need to create a user first.
#
# class SavedSearchMetaFactory(factory.DjangoModelFactory):
#     class Meta:
#         model = models.SavedSearchMeta
#
#     profile = factory.SubFactory(ProfileFactory)
#     search = factory.SubFactory(SearchFactory)
