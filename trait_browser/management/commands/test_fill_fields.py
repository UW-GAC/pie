"""Test the functions and classes in the fill_fields management command."""


from django.core import management
from django.test import TestCase

from core.build_test_db import build_test_db
from trait_browser.management.commands.fill_fields import Command
from trait_browser import models


class FillFieldsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = Command()
        build_test_db()

    def test_fill_harmonized_trait_set_version__component_html_detail(self):
        """Component html detail is no longer none after running the command."""
        management.call_command('fill_fields', '--fields=harmonized_trait_set_version__component_html_detail')
        for htsv in models.HarmonizedTraitSetVersion.objects.all():
            self.assertTrue(htsv.component_html_detail != '')
            # Contains the name of each harmonization unit.
            for hu in htsv.harmonizationunit_set.all():
                self.assertIn(hu.i_tag, htsv.component_html_detail)
                # Contains the name of each component age trait.
                for at in hu.component_age_traits.all():
                    self.assertIn(at.i_trait_name, htsv.component_html_detail)
            for htrait in htsv.harmonizedtrait_set.all():
                # Contains the name of each component source trait.
                for st in htrait.component_source_traits.all():
                    self.assertIn(st.i_trait_name, htsv.component_html_detail)
                # Contains the name of each component harmonized trait.
                for component_htsv in htrait.component_harmonized_trait_set_versions.all():
                    for ht in component_htsv.harmonizedtrait_set.all():
                        self.assertIn(ht.i_trait_name, htsv.component_html_detail)
                # # Contains the name of each component batch trait.
                # for bt in htrait.component_batch_traits.all():
                #     self.assertIn(bt.i_trait_name, htsv.component_html_detail)
