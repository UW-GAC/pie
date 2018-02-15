from django.db import models


class SourceDatasetQuerySet(models.query.QuerySet):
    def current(self):
        return self.filter(source_study_version__i_is_deprecated=False)


class SourceTraitQuerySet(models.query.QuerySet):
    def current(self):
        return self.filter(source_dataset__source_study_version__i_is_deprecated=False)
