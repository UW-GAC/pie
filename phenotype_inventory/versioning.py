#!/usr/bin/env python3.4

"""
Utilities for tracking the major and minor version number of the phenotype_inventory
Django project.
"""

from argparse import ArgumentParser
from django.conf import settings
import json
import os
import sys


# Get major and minor version numbers from .json version file.
with open(os.path.normpath(os.path.join(settings.BASE_DIR, 'version.json'))) as f:
    version_data = json.loads(f.read())
    MAJOR_VERSION = int(version_data['major'])
    MINOR_VERSION = int(version_data['minor'])
    del version_data


def get_version_string():
    """Make a nicely formatted string from the major and minor version numbers."""
    return '{}.{:02d}'.format(MAJOR_VERSION, MINOR_VERSION)

def increment_version(which):
    """Increment major or minor version number.
    
    Args:
        which (str): 'major' or 'minor'; which version number to increment.
        major (int):
        minor (int):
    """
    global MAJOR_VERSION
    global MINOR_VERSION
    if which == 'major':
        MAJOR_VERSION += 1
        MINOR_VERSION = 0
    elif which == 'minor':
        MINOR_VERSION += 1

def save_version_numbers():
    """Save the version numbers to the .json file."""
    version = {'major': MAJOR_VERSION, 'minor': MINOR_VERSION}
    f = open(os.path.normpath(os.path.join(settings.BASE_DIR, 'version.json')), 'w')
    json.dump(version, f, indent=1, sort_keys=True)
    f.close()

def main():
    """Take command line arguments and increment either major or minor version."""
    # Parse command line arguments.
    parser = ArgumentParser()
    incrementer = parser.add_mutually_exclusive_group()
    incrementer.add_argument("--incr_major", action="store_true", default=False,
        help="Increment the major version number. Also sets minor version to 0.")
    incrementer.add_argument("--incr_minor", action="store_true", default=False,
        help="Increment the minor version number.")
    args = parser.parse_args()
    # Increment major version if necessary.
    if args.incr_major:
        version_type = 'major'
    if args.incr_minor:
        version_type = 'minor'
    increment_version(which=version_type)
    # Save the new version numbers.
    save_version_numbers()

if __name__ == '__main__':
    main()