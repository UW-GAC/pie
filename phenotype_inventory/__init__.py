"""
"""

from core.management.commands.increment_version import Command


cmd = Command()
cmd.get_version_from_json()
__version__ = cmd.get_version_string()
