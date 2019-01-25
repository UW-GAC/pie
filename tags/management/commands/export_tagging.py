"""Create a data package of exported tagging data."""


import datetime
import logging
import os
from sys import stdout
from subprocess import check_output, STDOUT

from django.core.management.base import BaseCommand
from django.core import management

from tags.models import TaggedTrait
from trait_browser.models import Study


# Set up a logger to handle messages based on verbosity setting.
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(stdout)
detail_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(detail_formatter)
logger.addHandler(console_handler)

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
PREFIX = 'TOPMed_DCC'


class Command(BaseCommand):

    def _get_date_stamp(self):
        """Return a formatted datetime stamp for use in file names."""
        return datetime.datetime.now().strftime('%Y-%m-%d_%H%M')

    def _make_output_directory(self, input_path, date):
        """Create the directory that will contain output files.

        Arguments:
            input_path: str; input value of the path where an output results directory should be created
            date: str; the formatted datetime stamp from _get_date_stamp
        """
        output_dir = os.path.join(os.path.abspath(input_path), '{}_TOPMed_variable_tagging_data'.format(date))
        os.makedirs(output_dir)
        logger.debug('Created output directory {}'.format(output_dir))
        return output_dir

    def _dump_tags_json(self, output_dir, date):
        """Create a data dump file of the tags in json format.

        Arguments:
            output_dir: str; path of the directory where output files should be saved
            date: str; the formatted datetime stamp from _get_date_stamp
        """
        dump_fn = os.path.join(output_dir, '_'.join([date, PREFIX, 'tags.json']))
        dump_file = open(dump_fn, 'w')
        management.call_command('dumpdata', '--indent=4', 'tags.tag', stdout=dump_file)
        dump_file.close()
        logger.debug('Created json-formatted tags dump file {}'.format(dump_fn))
        return dump_fn

    def _make_tags_dump_data_dictionary_file(self, dump_fn):
        """Create a data dictionary file defining the fields in the tags dump json file.

        Arguments:
            dump_fn: str; the full path of the json formatted tags dump file the DD corresponds to
        """
        dump_dd_fn = dump_fn.replace('.json', '_data_dictionary.txt')
        dump_dd_file = open(dump_dd_fn, 'w')
        dump_dd_file.write('element_name\telement_description\n')
        dump_dd_file.write('\n'.join(['\t'.join(el) for el in TAGS_JSON_FIELDS]))
        dump_dd_file.close()
        logger.debug('Created data dictionary for tags dump file {}'.format(dump_dd_fn))
        return dump_dd_fn

    def _get_tagged_trait_data(self, study_pk=None, include_archived=False, include_deprecated=False):
        """Return a nested list of tagged traits according to the given filtersself.

        Arguments:
            study_pk: int; primary key of a study to filter the tagged traits to
            include_archived: bool; whether or not to include archived tagged traits
            include_deprecated: bool; whether or not to include tagged traits from deprecated study versions
        """
        if include_archived:
            q = TaggedTrait.objects.all()
            logger.debug('Including archived tagged traits...')
        else:
            q = TaggedTrait.objects.non_archived()
        if not include_deprecated:
            q = q.exclude(trait__source_dataset__source_study_version__i_is_deprecated=True)
        else:
            logger.debug('Including tagged traits from deprecated study versions...')
        if study_pk is not None:
                filter_study = Study.objects.get(pk=study_pk)
                q = q.filter(trait__source_dataset__source_study_version__study=filter_study)
                logger.debug('Filtering to a single study: {}...'.format(filter_study))
        return q.select_related(
            'trait',
            'trait__source_dataset',
            'trait__source_dataset__source_study_version',
            'trait__source_dataset__source_study_version__study'
        ).values_list(*TAGGED_TRAIT_VALUES_TO_RETRIEVE)

    def _make_tagged_trait_file(self, output_dir, date, tagged_traits):
        """Create a tab-delimited output file containing tagged trait data.

        Arguments:
            output_dir: str; path of the directory where output files should be saved
            date: str; the formatted datetime stamp from _get_date_stamp
        """
        formatted_taggedtrait_output = []
        formatted_taggedtrait_output.append('\t'.join(TAGGED_TRAIT_COLUMN_NAMES))
        tagged_traits = ['\t'.join([str(el) for el in row]) for row in tagged_traits]
        formatted_taggedtrait_output.extend(tagged_traits)
        tagged_trait_fn = os.path.join(output_dir, '_'.join([date, PREFIX, 'tagged_variables.txt']))
        tagged_trait_file = open(tagged_trait_fn, 'w')
        tagged_trait_file.write('\n'.join(formatted_taggedtrait_output))
        tagged_trait_file.close()
        logger.debug('Created tab-delimited tagged traits data file {}'.format(tagged_trait_fn))
        return tagged_trait_fn

    def _make_tagged_trait_data_dictionary_file(self, tagged_trait_fn):
        """Create a data dictionary file defining the fields in the tagged traits file.

        Arguments:
            tagged_trait_fn: str; the full path of the tab-delimited tagged traits file the DD corresponds to
        """
        mapping_dd_fn = tagged_trait_fn.replace('.txt', '_data_dictionary.txt')
        mapping_dd_file = open(mapping_dd_fn, 'w')
        mapping_dd_file.write('column_name\tcolumn_description\n')
        mapping_dd_file.write('\n'.join(['\t'.join(el[:2]) for el in TAGGED_TRAIT_COLUMNS]))
        mapping_dd_file.close()
        logger.debug('Created data dictionary for tagged traits data file {}'.format(mapping_dd_fn))
        return mapping_dd_fn

    def _make_readme_file(self, output_dir, dump_fn, dump_dd_fn, tagged_trait_fn, tagged_trait_dd_fn,
                          release_notes=None):
        """Create a README file based on the template found in README_TEMPLATE.

        Arguments:
            output_dir: str; path of the directory where output files should be saved
            dump_fn: str; full path of the tags dump json format file
            dump_dd_fn: str; full path of the DD for the tags dump json file
            tagged_trait_fn: str; full path of the tab-delimited tagged traits file
            tagged_trait_dd_fn: str; full path of the DD for the tagged traits file
            release_notes: str; full path of a file containing notes to include in the release notes section
        """
        if release_notes is not None:
            with open(release_notes, 'r') as rnf:
                release_notes_text = rnf.read()
        else:
            release_notes_text = ''
        with open(README_TEMPLATE, 'r') as template_file:
            template = template_file.read()
        readme_fn = os.path.join(output_dir, 'README.md')
        readme_file = open(readme_fn, 'w')
        readme_file.write(
            template.format(
                tags_dump_file=dump_fn.replace(output_dir, ''),
                tags_dump_dd_file=dump_dd_fn.replace(output_dir, ''),
                tagged_variable_file=tagged_trait_fn.replace(output_dir, ''),
                tagged_variable_dd_file=tagged_trait_dd_fn.replace(output_dir, ''),
                release_notes=release_notes_text
            )
        )
        readme_file.close()
        logger.debug('Created README file')
        return readme_fn

    def _compress_directory(self, input_path, output_dir):
        """Create a .tar.gz compressed version of the output directory.

        Arguments:
            input_path: str; input value of the path where an output results directory should be created
            output_dir: str; path of the directory where output files should be saved
        """
        tar_gz_fn = output_dir + '.tar.gz'
        output_package_dir = os.path.basename(output_dir)
        tar_command = ['tar', '-zcvf', tar_gz_fn, '--directory={}'.format(input_path), output_package_dir]
        logger.debug('Running tar command:\n' + ' '.join(tar_command))
        tar_output = check_output(tar_command, stderr=STDOUT)
        logger.debug(tar_output.decode('utf-8'))
        logger.debug('Created compressed data package {}'.format(tar_gz_fn))
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
        """Create a package (compressed and uncompressed) of the tagging data."""
        # Set the logger level based on verbosity setting.
        verbosity = options.get('verbosity')
        if verbosity == 0:
            logger.setLevel(logging.ERROR)
        elif verbosity == 1:
            logger.setLevel(logging.WARNING)
        elif verbosity == 2:
            logger.setLevel(logging.INFO)
        elif verbosity == 3:
            logger.setLevel(logging.DEBUG)
        # Make output directory
        dir_option = options.get('output_path')
        date = self._get_date_stamp()
        output_dir = self._make_output_directory(dir_option, date)
        # Make json data dump of tags
        dump_fn = self._dump_tags_json(output_dir, date)
        # Make a data dictionary for json data dump
        dump_dd_fn = self._make_tags_dump_data_dictionary_file(dump_fn)
        # Make exported tagged variables file
        study_pk = options.get('study_pk')
        tagging_data = self._get_tagged_trait_data(study_pk=study_pk)
        tagged_trait_fn = self._make_tagged_trait_file(output_dir, date, tagging_data)
        # Make a data dictionary for tagged variables file
        tagged_trait_dd_fn = self._make_tagged_trait_data_dictionary_file(tagged_trait_fn)
        # Make a current version of the readme file
        notes_file = options.get('release_notes')
        readme_fn = self._make_readme_file(output_dir=output_dir, dump_fn=dump_fn, dump_dd_fn=dump_dd_fn,
                                           tagged_trait_fn=tagged_trait_fn, tagged_trait_dd_fn=tagged_trait_dd_fn,
                                           release_notes=notes_file)
        # tar and gzip the output directory
        self._compress_directory(dir_option, output_dir)
