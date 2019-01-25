"""Create a data package of exported tagging data."""


import datetime
import os
from subprocess import check_call

from django.core.management.base import BaseCommand
from django.core import management

from tags.models import TaggedTrait
from trait_browser.models import Study


TAGS_JSON_FIELDS = (
    ('model', 'indicates this is part of the "tags.tag" model, an artifact of the data export process'),
    ('pk', 'the primary key, or unique id number of the tag'),
    ('fields', 'the field properties for each tag object'),
    ('created', 'timestamp for creation time of the tag'),
    ('modified', 'timestamp for last modified time of the tag'),
    ('title', 'formatted title of the tag; the general phenotype concept'),
    ('lower_title', 'a conversion of the "title" field to all lowercase, in order to enforce a unique constraint on case-insensitive tag title'),
    ('description', 'a brief description of the phenotype concept represented by the tag'),
    ('instructions', 'detailed instructions describing which kinds of variables should have the tag applied or not'),
    ('creator', 'id number for the user who created the tag'),
)

# Tuple format: ('output_column_name', 'field_name__in__values_list', 'column description for DD')
TAGGED_TRAIT_COLUMNS = (
    ('tag_pk', 'tag__pk',
     'primary key, or unique id for the tag; corresponds to "pk" from the _TOPMed_DCC_tags.json file'),
    ('tag_title', 'tag__title',
     'formatted title of tag; corresponds to "title" from the _TOPMed_DCC_tags.json file'),
    ('variable_phv', 'trait__i_dbgap_variable_accession',
     'dbGaP variable identifier for the variable, called phv'),
    ('variable_full_accession', 'trait__full_accession',
     'full dbGaP accession for the variable, including phv, variable version number, and participant set number'),
    ('dataset_full_accession', 'trait__source_dataset__full_accession',
     'full dbGaP accession for the dataset (table) the variable is from, including pht, dataset version number, and participant set number'),
    ('study_full_accession', 'trait__source_dataset__source_study_version__full_accession',
     'full dbGaP accession for the study, including phs, study version number, and participant set number'),
    ('study_name', 'trait__source_dataset__source_study_version__study__i_study_name',
     'dbGaP study name'),
    ('study_phs', 'trait__source_dataset__source_study_version__study__pk',
     'dbGaP identifier for the study, called phs'),
    ('study_version', 'trait__source_dataset__source_study_version__i_version',
     'dbGaP study version number'),
    ('created', 'created',
     'date the tagged variable (link between tag and variable) was created at the DCC'),
    ('modified', 'modified',
     'date the tagged variable (link between tag and variable) was last modified at the DCC'),
)
TAGGED_TRAIT_VALUES_TO_RETRIEVE = tuple([el[1] for el in TAGGED_TRAIT_COLUMNS])
TAGGED_TRAIT_COLUMN_NAMES = tuple([el[0] for el in TAGGED_TRAIT_COLUMNS])

README_TEMPLATE = 'tags/management/commands/README.md'


class Command(BaseCommand):

    def _get_formatted_path_and_make_directory(self, input_path):
        """Creates an output directory and returns formatted paths and filenames."""
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
        output_dir = input_path + '/{}_TOPMed_variable_tagging_data/'.format(current_date)
        os.makedirs(os.path.dirname(output_dir))
        output_prefix = output_dir + current_date
        prefix = 'TOPMed_DCC'
        files = {
            'output_directory': output_dir,
            'tagged_traits_file': '_'.join([current_date, prefix, 'tagged_variables.txt']),
            'tagged_traits_data_dictionary_file': '_'.join([current_date, prefix,
                                                            'tagged_variables_data_dictionary.txt']),
            'tags_dump_file': '_'.join([current_date, prefix, 'tags.json']),
            'tags_dump_data_dictionary_file': '_'.join([current_date, prefix, 'tags_data_dictionary.txt']),
            'readme_file': 'README.md'
        }
        return files

    def _dump_tags_json(self, files):
        dump_fn = files['output_directory'] + files['tags_dump_file']
        dump_file = open(dump_fn, 'w')
        management.call_command('dumpdata', '--indent=4', 'tags.tag', stdout=dump_file)
        dump_file.close()
        return dump_fn

    def _make_tags_dump_data_dictionary_file(self, files):
        dump_DD_fn = files['output_directory'] + files['tags_dump_data_dictionary_file']
        dump_DD_file = open(dump_DD_fn, 'w')
        dump_DD_file.write('element_name\telement_description\n')
        dump_DD_file.write('\n'.join(['\t'.join(el) for el in TAGS_JSON_FIELDS]))
        dump_DD_file.close()
        return dump_DD_fn

    def _get_tagged_trait_data(self, study_pk=None, include_archived=False, include_deprecated=False):
        if include_archived:
            q = TaggedTrait.objects.all()
        else:
            q = TaggedTrait.objects.non_archived()
        if not include_deprecated:
            q = q.exclude(trait__source_dataset__source_study_version__i_is_deprecated=True)
        if study_pk is not None:
                filter_study = Study.objects.get(pk=study_pk)
                q = q.filter(trait__source_dataset__source_study_version__study=filter_study)
        return q.select_related(
            'trait',
            'trait__source_dataset',
            'trait__source_dataset__source_study_version',
            'trait__source_dataset__source_study_version__study'
        ).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)

    def _make_tagged_trait_file(self, files, tagged_traits):
        formatted_taggedtrait_output = []
        formatted_taggedtrait_output.append('\t'.join(TAGGED_TRAIT_COLUMN_NAMES))
        tagged_traits = ['\t'.join([str(el) for el in row]) for row in tagged_traits]
        formatted_taggedtrait_output.extend(tagged_traits)
        mapping_fn = files['output_directory'] + files['tagged_traits_file']
        mapping_file = open(mapping_fn, 'w')
        mapping_file.write('\n'.join(formatted_taggedtrait_output))
        mapping_file.close()
        return mapping_fn

    def _make_tagged_trait_data_dictionary_file(self, files):
        mapping_DD_fn = files['output_directory'] + files['tagged_traits_data_dictionary_file']
        mapping_DD_file = open(mapping_DD_fn, 'w')
        mapping_DD_file.write('column_name\tcolumn_description\n')
        mapping_DD_file.write('\n'.join(['\t'.join(el[:2]) for el in TAGGED_TRAIT_COLUMNS]))
        mapping_DD_file.close()
        return mapping_DD_fn

    def _make_readme_file(self, files, release_notes=None):
        if release_notes is not None:
            with open(release_notes, 'r') as rnf:
                release_notes_text = rnf.read()
        else:
            release_notes_text = ''
        with open(README_TEMPLATE, 'r') as template_file:
            template = template_file.read()
        readme_fn = files['output_directory'] + files['readme_file']
        readme_file = open(readme_fn, 'w')
        readme_file.write(
            template.format(
                tags_dump_file=files['tags_dump_file'],
                tags_dump_dd_file=files['tags_dump_data_dictionary_file'],
                tagged_variable_file=files['tagged_traits_file'],
                tagged_variable_dd_file=files['tagged_traits_data_dictionary_file'],
                release_notes=release_notes_text
            )
        )
        readme_file.close()
        return readme_fn

    def _compress_directory(self, files):
        """Create a .tar.gz compressed version of the output directory."""
        tar_fn_root = os.path.split(files['output_directory'])[0]
        tar_gz_fn = tar_fn_root + '.tar.gz'
        split_output_dir = os.path.split(tar_fn_root)
        input_path = split_output_dir[0]
        output_package_dir = split_output_dir[1]
        tar_command = ['tar', '-zcvf', tar_gz_fn, '--directory={}'.format(input_path), output_package_dir]
        print(' '.join(tar_command))
        check_call(tar_command)
        return tar_gz_fn

    def add_arguments(self, parser):
        parser.add_argument('output_path', action='store', type=str, default=None,
                            help="""
                                The path at which to save a .tag.gz file containing exported tagging data.
                                The file will have a default file name and include the date and time of export.
                                This argument only lets you specify the path at which to create a .tar.gz.
                            """
                            )
        parser.add_argument('--study_pk', action='store', type=int, default=None, required=False,
                            help='Study primary key (phs). Exports only tagged variables from this study.'
                            )
        parser.add_argument('--release_notes', action='store', type=str, default=None, required=False,
                            help='Path to a file containing release notes to include in the README.'
                            )

    def handle(self, *args, **options):
        """Take command line arguments and increment either major or minor version."""
        # Make output directory
        dir_option = options.get('output_path')
        files = self._get_formatted_path_and_make_directory(dir_option)
        # Make json data dump of tags
        self._dump_tags_json(files)
        # Make a data dictionary for json data dump
        self._make_tags_dump_data_dictionary_file(files)
        # Make exported tagged variables file
        study_pk = options.get('study_pk')
        tagging_data = self._get_tagged_trait_data(study_pk=study_pk)
        self._make_tagged_trait_file(files, tagging_data)
        # Make a data dictionary for tagged variables file
        self._make_tagged_trait_data_dictionary_file(files)
        # Make a current version of the readme file
        notes_file = options.get('release_notes')
        self._make_readme_file(files, release_notes=notes_file)
        # tar and gzip the output directory
        self._compress_directory(files)
