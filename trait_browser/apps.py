from django.apps import AppConfig
from watson import search as watson


class SourceDatasetSearchAdapter(watson.SearchAdapter):

    def get_title(self, obj):
        return ''

    def get_description(self, obj):
        return obj.i_dbgap_description

    def get_content(self, obj):
        return ''


class SourceTraitSearchAdapter(watson.SearchAdapter):

    def get_title(self, obj):
        return ''

    def get_description(self, obj):
        return obj.i_description

    def get_content(self, obj):
        return ''


class HarmonizedTraitSearchAdapter(watson.SearchAdapter):

    def get_title(self, obj):
        return ''

    def get_description(self, obj):
        return obj.i_description

    def get_content(self, obj):
        return ''


class TraitBrowserConfig(AppConfig):

    name = 'trait_browser'

    def ready(self):
        # Register source datasets.
        SourceDataset = self.get_model("SourceDataset")
        watson.register(SourceDataset, SourceDatasetSearchAdapter)
        # Register source traits.
        SourceTrait = self.get_model("SourceTrait")
        watson.register(SourceTrait, SourceTraitSearchAdapter, fields=('i_description',))
        # Register harmonized traits.
        HarmonizedTrait = self.get_model("HarmonizedTrait")
        watson.register(HarmonizedTrait, HarmonizedTraitSearchAdapter, fields=('i_description',))
