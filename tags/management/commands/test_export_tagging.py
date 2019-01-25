"""Test the export_tagging management command."""

import datetime
from faker import Faker
import json
import os
import tarfile
from tempfile import TemporaryDirectory, NamedTemporaryFile

from django.core import management
from django.test import TestCase

from tags.management.commands.export_tagging import Command, TAGGED_TRAIT_VALUES_TO_RETRIEVE
from tags import factories
from tags import models
from trait_browser.factories import StudyFactory, SourceStudyVersionFactory

fake = Faker()
cmd = Command()


class GetDateStampTest(TestCase):

    def test_returns_valid_date(self):
        """The datetime stamp can be converted back into a datetime object, and back again."""
        stamp = cmd._get_date_stamp()
        converted = datetime.datetime.strptime(stamp, '%Y-%m-%d_%H%M')
        self.assertEqual(stamp, converted.strftime('%Y-%m-%d_%H%M'))


class GetFormattedPathAndMakeDirectoryTest(TestCase):

    def test_creates_directory(self):
        """The expected directory is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        self.assertTrue(os.path.exists(output_dir))
        self.assertTrue(os.path.isdir(output_dir))

    def test_fails_in_same_minute(self):
        """Minute-precise timestamp in name prevents creating a directory within the same minute."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        with self.assertRaises(OSError):
            output_dir2 = cmd._make_output_directory(tmpdir.name, date)


class DumpTagsJsonTest(TestCase):

    def test_creates_json_file(self):
        """The expected file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        json_file = cmd._dump_tags_json(output_dir, date)
        self.assertTrue(os.path.exists(json_file))

    def test_file_contains_tag(self):
        """The json dump file contains one expected tag."""
        tag = factories.TagFactory.create()
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        json_file = cmd._dump_tags_json(output_dir, date)
        with open(json_file) as f:
            tags = json.loads(f.read())
        self.assertEqual(tags[0]['pk'], tag.pk)
        self.assertEqual(tags[0]['fields']['title'], tag.title)


class MakeTagsDumpDataDictionaryFileTest(TestCase):

    def test_creates_file(self):
        """The expected file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        json_file = os.path.join(output_dir, 'test_tags_dump.json')
        json_dd_file = cmd._make_tags_dump_data_dictionary_file(json_file)
        self.assertTrue(os.path.exists(json_dd_file))

    def test_dump_data_dictionary_contains_all_json_field_names(self):
        """The data dictionary for the json tags dump contains all field names."""
        tag = factories.TagFactory.create()
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        json_file = cmd._dump_tags_json(output_dir, date)
        json_dd_file = cmd._make_tags_dump_data_dictionary_file(json_file)
        # Find all of the keys that should be defined in the data dictionary.
        with open(json_file) as f:
            tags = json.loads(f.read())
        all_keys = []
        for key in tags[0]:
            all_keys.append(key)
            if type(tags[0][key]) is dict:
                for nested_key in tags[0][key]:
                    all_keys.append(nested_key)
        # Pull out the first column of the data dictionary file.
        with open(json_dd_file) as f:
            data_dict = [line.strip().split('\t') for line in f.readlines()]
        data_dict_terms = [row[0] for row in data_dict]
        # Is each expected term present in the data dictionary column 1?
        for expected_key in all_keys:
            self.assertIn(expected_key, data_dict_terms,
                          msg='JSON field {} not found in data dictionary.'.format(expected_key))


class GetTaggedTraitDataTest(TestCase):

    def test_returns_all_tagged_traits_with_no_filters(self):
        """All tagged traits are included without any extra arguments."""
        all_tagged_traits = factories.TaggedTraitFactory.create_batch(5)
        result = cmd._get_tagged_trait_data()
        self.assertEqual(list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
                         list(models.TaggedTrait.objects.all().values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_excludes_other_study_with_study_pk(self):
        """Giving a study pk excludes tagged traits from other studies."""
        study1 = StudyFactory.create()
        study2 = StudyFactory.create()
        study1_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version__study=study1)
        study2_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version__study=study2)
        result = cmd._get_tagged_trait_data(study_pk=study1.pk)
        self.assertEqual(
            list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
            list(models.TaggedTrait.objects.filter(
                pk__in=[tt.pk for tt in study1_tagged_traits]).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_excludes_archived_with_include_archived_false(self):
        """Archived tagged traits are not included by default."""
        archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, archived=True)
        non_archived_tagged_traits = factories.TaggedTraitFactory.create_batch(2)
        result = cmd._get_tagged_trait_data()  # include_archived=False is the default
        self.assertEqual(
            list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
            list(models.TaggedTrait.objects.filter(
                pk__in=[tt.pk for tt in non_archived_tagged_traits]).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_includes_archived_with_include_archived_true(self):
        """Archived tagged traits are included when requested."""
        archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, archived=True)
        non_archived_tagged_traits = factories.TaggedTraitFactory.create_batch(2)
        result = cmd._get_tagged_trait_data(include_archived=True)
        self.assertEqual(
            list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
            list(models.TaggedTrait.objects.filter(
                pk__in=[tt.pk for tt in non_archived_tagged_traits + archived_tagged_traits]
            ).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_excludes_deprecated_with_include_deprecated_false(self):
        """Deprecated tagged traits are not included by default."""
        study = StudyFactory.create()
        current_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_version = SourceStudyVersionFactory.create(
            study=study, i_version=current_version.i_version - 1, i_is_deprecated=True)
        deprecated_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version=old_version)
        non_deprecated_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version=current_version)
        result = cmd._get_tagged_trait_data()  # include_deprecated=False is the default
        self.assertEqual(
            list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
            list(models.TaggedTrait.objects.filter(
                pk__in=[tt.pk for tt in non_deprecated_tagged_traits]).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_includes_deprecated_with_include_deprecated_true(self):
        """Deprecated tagged traits are included when requested."""
        study = StudyFactory.create()
        current_version = SourceStudyVersionFactory.create(study=study, i_version=5)
        old_version = SourceStudyVersionFactory.create(
            study=study, i_version=current_version.i_version - 1, i_is_deprecated=True)
        deprecated_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version=old_version)
        non_deprecated_tagged_traits = factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version=current_version)
        result = cmd._get_tagged_trait_data(include_deprecated=True)
        self.assertEqual(
            list(result.values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)),
            list(models.TaggedTrait.objects.filter(
                pk__in=[tt.pk for tt in non_deprecated_tagged_traits + deprecated_tagged_traits]
            ).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)))

    def test_with_no_tagged_traits(self):
        """Result is empty when there are no tagged traits."""
        result = cmd._get_tagged_trait_data(include_deprecated=True)
        self.assertEqual(len(result), 0)


class MakeTaggedTraitFileTest(TestCase):

    def test_creates_file(self):
        """The expected file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        data = []
        tagged_traits_file = cmd._make_tagged_trait_file(output_dir, date, data)
        self.assertTrue(os.path.exists(tagged_traits_file))

    def test_file_length_with_tagged_traits(self):
        """The output file contains the right number of lines."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        tagged_traits = factories.TaggedTraitFactory.create_batch(20)
        data = cmd._get_tagged_trait_data()
        tagged_traits_file = cmd._make_tagged_trait_file(output_dir, date, data)
        with open(tagged_traits_file, 'r') as f:
            content = f.readlines()
        self.assertEqual(len(content), models.TaggedTrait.objects.count() + 1)

    def test_file_length_with_no_tagged_traits(self):
        """The output file contains no data lines when there are no tagged traits."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        data = cmd._get_tagged_trait_data()
        tagged_traits_file = cmd._make_tagged_trait_file(output_dir, date, data)
        with open(tagged_traits_file, 'r') as f:
            content = f.readlines()
        self.assertEqual(len(content), 1)


class MakeTaggedTraitDataDictionaryFileTest(TestCase):

    def test_creates_file(self):
        """The expected file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        data = cmd._get_tagged_trait_data()
        tagged_traits_file = cmd._make_tagged_trait_file(output_dir, date, data)
        tt_dd_file = cmd._make_tagged_trait_data_dictionary_file(tagged_traits_file)
        self.assertTrue(os.path.exists(tt_dd_file))

    def test_tagged_trait_data_dictionary_fields_match_columns_of_tagged_trait_file(self):
        """The data dictionary for the tagged traits file contains all column names."""
        tagged_traits = factories.TaggedTraitFactory.create_batch(2)
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        data = cmd._get_tagged_trait_data()
        tagged_traits_file = cmd._make_tagged_trait_file(output_dir, date, data)
        tt_dd_file = cmd._make_tagged_trait_data_dictionary_file(tagged_traits_file)
        with open(tt_dd_file, 'r') as f:
            dd_lines = [line.strip().split('\t') for line in f.readlines()]
        dd_fields = [line[0] for line in dd_lines]
        with open(tagged_traits_file, 'r') as f:
            tagged_trait_lines = [line.strip().split('\t') for line in f.readlines()]
        tagged_trait_header = tagged_trait_lines[0]
        # Is each expected term present in the data dictionary column 1?
        for expected_field in tagged_trait_header:
            self.assertIn(expected_field, dd_fields,
                          msg='tagged trait field {} not found in data dictionary.'.format(expected_field))


class MakeReadmeFileTest(TestCase):

    def test_creates_file(self):
        """The expected readme file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        readme_file = cmd._make_readme_file(output_dir=output_dir,
                                            dump_fn='tags_file.json',
                                            dump_dd_fn='tags_file_dd.txt',
                                            tagged_trait_fn='tagged_traits_file.txt',
                                            tagged_trait_dd_fn='tagged_traits_file_dd.txt')
        self.assertTrue(os.path.exists(readme_file))

    def test_readme_contains_release_notes(self):
        """The contents of a release notes file are included in the readme file."""
        # Make a fake release notes file.
        # Need to be able to close this file for reading by _make_readme_file, so will need to manually delete.
        tmpfile = NamedTemporaryFile(delete=False)
        # Have to encode this string because the tempfile is open in 'w+b' mode.
        release_notes_text = '\n'.join([fake.sentence() for el in range(3)]).encode('utf-8')
        tmpfile.write(release_notes_text)
        tmpfile.close()
        # Now make the readme file and read it in.
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        readme_file = cmd._make_readme_file(output_dir=output_dir,
                                            dump_fn='tags_file.json',
                                            dump_dd_fn='tags_file_dd.txt',
                                            tagged_trait_fn='tagged_traits_file.txt',
                                            tagged_trait_dd_fn='tagged_traits_file_dd.txt',
                                            release_notes=tmpfile.name)
        with open(readme_file, 'r') as f:
            readme_contents = f.read()
        self.assertIn(release_notes_text.decode('utf-8'), readme_contents)
        os.remove(tmpfile.name)  # Delete the fake release notes file.

    def test_readme_contains_file_names(self):
        """The names of the expected files are found in the readme file."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        dump_fn = 'tags_file.json'
        dump_dd_fn = 'tags_file_dd.txt'
        tagged_trait_fn = 'tagged_traits_file.txt'
        tagged_trait_dd_fn = 'tagged_traits_file_dd.txt'
        readme_file = cmd._make_readme_file(output_dir=output_dir,
                                            dump_fn=dump_fn,
                                            dump_dd_fn=dump_dd_fn,
                                            tagged_trait_fn=tagged_trait_fn,
                                            tagged_trait_dd_fn=tagged_trait_dd_fn)
        with open(readme_file, 'r') as f:
            readme_contents = f.read()
        self.assertIn(dump_fn, readme_contents)
        self.assertIn(dump_dd_fn, readme_contents)
        self.assertIn(tagged_trait_fn, readme_contents)
        self.assertIn(tagged_trait_dd_fn, readme_contents)


class CompressDirectoryTest(TestCase):

    def test_creates_file(self):
        """The expected .tar.gz file is created."""
        tmpdir = TemporaryDirectory()
        date = cmd._get_date_stamp()
        output_dir = cmd._make_output_directory(tmpdir.name, date)
        expected_tar_gz_file = cmd._compress_directory(tmpdir.name, output_dir)
        self.assertTrue(os.path.exists(expected_tar_gz_file))


class ExportTaggingIntegrationTest(TestCase):

    def test_creates_all_files(self):
        """All of the expected output files are created."""
        tmpdir = TemporaryDirectory()
        management.call_command('export_tagging', tmpdir.name)
        output = os.listdir(tmpdir.name)
        tar_gz_file = [el for el in output if el.endswith('.tar.gz')][0]
        output_dir = [el for el in output if not el.endswith('.tar.gz')][0]
        output_files = os.listdir(os.path.join(tmpdir.name, output_dir))
        self.assertTrue(any([el.endswith('_tagged_variables.txt') for el in output_files]))
        self.assertTrue(any([el.endswith('_tagged_variables_data_dictionary.txt') for el in output_files]))
        self.assertTrue(any([el.endswith('_tags.json') for el in output_files]))
        self.assertTrue(any([el.endswith('_tags_data_dictionary.txt') for el in output_files]))
        self.assertTrue(any([el.endswith('README.md') for el in output_files]))

    def test_package_contains_all_files(self):
        """The compressed data package contains all of the expected files."""
        tmpdir = TemporaryDirectory()
        management.call_command('export_tagging', tmpdir.name)
        output = os.listdir(tmpdir.name)
        tar_gz_file = [el for el in output if el.endswith('.tar.gz')][0]
        tar_gz_file = os.path.join(tmpdir.name, tar_gz_file)
        output_dir = [el for el in output if not el.endswith('.tar.gz')][0]
        output_files = os.listdir(os.path.join(tmpdir.name, output_dir))
        with tarfile.open(tar_gz_file, 'r:gz') as ftgz:
            archive_contents = ftgz.getnames()
        for file in output_files:
            self.assertIn(os.path.join(output_dir, file), archive_contents,
                          msg='Expected file {} missing from .tar.gz archive.'.format(file))
