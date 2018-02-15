from django.apps import AppConfig
from watson import search as watson


class TraitBrowserConfig(AppConfig):

    name = 'trait_browser'

    def ready(self):
        SourceTrait = self.get_model("SourceTrait")
        watson.register(SourceTrait, fields=('i_description',))
