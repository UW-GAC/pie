"""Test custom functions etc. in the settings files."""

import os

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from .base import get_env_variable


class SettingsTestCase(TestCase):

    def test_get_env_variable_with_good_var(self):
        """Returns correct value when a variable definitely exists."""
        test_string = 'test_string'
        os.environ['TEST'] = test_string
        self.assertEqual(test_string, get_env_variable('TEST'))
        del os.environ['TEST']

    def test_get_env_variable_with_bad_var(self):
        """Raises an error when a variable has not been set."""
        self.assertRaises(ImproperlyConfigured, get_env_variable, 'IMPROBABLE_VARIABLE_NAME')
