"""Test custom functions etc. in the settings files."""

import os

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from .base import get_env_variable


class SettingsTestCase(TestCase):
    
    def test_get_env_variable_with_good_var(self):
        """Test that the function for getting environmental variables works when a variable definitely exists."""
        test_string = 'test_string'
        os.environ['TEST'] = test_string
        self.assertEqual(test_string, get_env_variable('TEST'))
    
    def test_get_env_variable_with_bad_var(self):
        """Test that the function for getting environmental variables raises an error when a variable definitely exists."""
        self.assertRaises(ImproperlyConfigured, get_env_variable, 'IMPROBABLE_VARIABLE_NAME')