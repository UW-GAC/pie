"""Create a data package of exported tagging data."""


from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def foo():
        pass

    def add_arguments(self, parser):
        # incrementer = parser.add_mutually_exclusive_group()
        # incrementer.add_argument(
        #     "--major", action="store_true", default=False,
        #     help="Increment the major version number. Also sets minor version to 0.")
        # incrementer.add_argument(
        #     "--minor", action="store_true", default=False,
        #     help="Increment the minor version number.")
        pass

    def handle(self, *args, **options):
        """Take command line arguments and increment either major or minor version."""
        # # Parse command line arguments.
        # self.get_version_from_json()
        # # Increment major version if necessary.
        # if options.get('major'):
        #     version_type = 'major'
        # if options.get('minor'):
        #     version_type = 'minor'
        # self.increment_version(which=version_type)
        # # Save the new version numbers.
        # self.save_version_numbers()
        # print('Version', self.get_version_string())
        pass
