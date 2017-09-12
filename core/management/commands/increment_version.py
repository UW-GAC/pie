"""Utilities for tracking the major and minor version number of phenotype_inventory."""

import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand


VERSION_FILE = os.path.normpath(os.path.join(settings.BASE_DIR, 'version.json'))


class Command(BaseCommand):

    def get_version_from_json(self):
        """Get major and minor version numbers from .json version file."""
        with open(VERSION_FILE) as f:
            version_data = json.loads(f.read())
            self.MAJOR_VERSION = int(version_data['major'])
            self.MINOR_VERSION = int(version_data['minor'])

    def get_version_string(self):
        """Make a nicely formatted string from the major and minor version numbers."""
        return '{}.{:02d}'.format(self.MAJOR_VERSION, self.MINOR_VERSION)

    def increment_version(self, which):
        """Increment major or minor version number.

        Args:
            which (str): 'major' or 'minor'; which version number to increment.
            major (int):
            minor (int):
        """
        if which == 'major':
            self.MAJOR_VERSION += 1
            self.MINOR_VERSION = 0
        elif which == 'minor':
            self.MINOR_VERSION += 1

    def save_version_numbers(self):
        """Save the version numbers to the .json file."""
        version = {'major': self.MAJOR_VERSION, 'minor': self.MINOR_VERSION}
        f = open(VERSION_FILE, 'w')
        json.dump(version, f, indent=1, sort_keys=True)
        f.close()

    def add_arguments(self, parser):
        incrementer = parser.add_mutually_exclusive_group()
        incrementer.add_argument(
            "--major", action="store_true", default=False,
            help="Increment the major version number. Also sets minor version to 0.")
        incrementer.add_argument(
            "--minor", action="store_true", default=False,
            help="Increment the minor version number.")

    def handle(self, *args, **options):
        """Take command line arguments and increment either major or minor version."""
        # Parse command line arguments.
        self.get_version_from_json()
        # Increment major version if necessary.
        if options.get('major'):
            version_type = 'major'
        if options.get('minor'):
            version_type = 'minor'
        self.increment_version(which=version_type)
        # Save the new version numbers.
        self.save_version_numbers()
        print('Version', self.get_version_string())
