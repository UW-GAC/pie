from django.apps import AppConfig
from watson import search as watson


class SourceTraitSearchAdapter(watson.SearchAdapter):

    def get_title(self, obj):
        return ''

    def get_description(self, obj):
        return obj.i_description

    def get_content(self, obj):
        return ''


class TraitBrowserConfig(AppConfig):

    name = 'trait_browser'

    def ready(self):
        SourceTrait = self.get_model("SourceTrait")
        watson.register(SourceTrait, SourceTraitSearchAdapter, fields=('i_description',))
