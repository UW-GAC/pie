# Export tagging data for Team Oxygen.

# ssh modu
# workon phenotype_inventory

# Start with shell_plus to run interactively
# ./manage.py shell_plus --settings=phenotype_inventory.settings.production

# Or run in the shell with this command:
# ./manage.py shell --settings=phenotype_inventory.settings.production < ~/export_tagging_data_for_collaborators.py

import datetime
import os
from subprocess import check_call

from django.core import management
from tags import models

# Make a time-stamped file prefix for output files
current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
output_dir = '/home/www-staff/emeryl/exported_tagging_data/{}_TOPMed_variable_tagging_data/'.format(current_date)
os.makedirs(os.path.dirname(output_dir), exist_ok=True)
output_prefix = output_dir + current_date

########################################################################################################################
# Make the json data dump of all of the tags.
dump_fn = output_prefix + '_TOPMed_DCC_tags.json'
dump_file = open(dump_fn, 'w')
management.call_command('dumpdata', '--indent=4', 'tags.tag', stdout=dump_file)
dump_file.close()
print('Saved tag dump to', dump_fn)

# Make a data dictionary for the .json file.
json_fields = (
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

# Write out a data dictionary file.
dump_DD_fn = dump_fn.replace('.json', '_data_dictionary.json.txt')
dump_DD_file = open(dump_DD_fn, 'w')
dump_DD_file.write('element_name \telement_description\n')
dump_DD_file.write( ' \n'.join([' \t'.join(el) for el in json_fields]) )
dump_DD_file.close()
print('Saved tag dump data dictionary to', dump_DD_fn)

########################################################################################################################
# Make a data dictionary.
output_columns = (
    ('tag_pk', 'primary key, or unique id for the tag; corresponds to "pk" from the _TOPMed_DCC_tags.json file'),
    ('tag_title', 'formatted title of tag; corresponds to "title" from the _TOPMed_DCC_tags.json file'),
    ('variable_phv', 'dbGaP variable identifier for the variable, called phv'),
    ('variable_full_accession', 'full dbGaP accession for the variable, including phv, variable version number, and participant set number'),
    ('dataset_full_accession', 'full dbGaP accession for the dataset (table) the variable is from, including pht, dataset version number, and participant set number'),
    ('study_full_accession', 'full dbGaP accession for the study, including phs, study version number, and participant set number'),
    ('study_name', 'dbGaP study name'),
    ('study_phs', 'dbGaP identifier for the study, called phs'),
    ('study_version', 'dbGaP study version number'),
    ('created', 'date the tagged variable (link between tag and variable) was created at the DCC'),
    ('modified', 'date the tagged variable (link between tag and variable) was last modified at the DCC'),
)

# Print the tag-variable links to a tab-delimited file.
formatted_taggedtrait_output = []
formatted_taggedtrait_output.append(' \t'.join( [el[0] for el in output_columns] ))

output = models.TaggedTrait.objects.non_archived().exclude(
    trait__source_dataset__source_study_version__i_is_deprecated=True
).select_related(
    'trait',
    'trait__source_dataset',
    'trait__source_dataset__source_study_version',
    'trait__source_dataset__source_study_version__study'
).values_list(
    'tag__pk',
    'tag__title',
    'trait__i_dbgap_variable_accession',
    'trait__full_accession',
    'trait__source_dataset__full_accession',
    'trait__source_dataset__source_study_version__full_accession',
    'trait__source_dataset__source_study_version__study__i_study_name',
    'trait__source_dataset__source_study_version__study__pk',
    'trait__source_dataset__source_study_version__i_version',
    'created',
    'modified',
)
output2 = ['\t'.join([str(el) for el in row]) for row in output]
formatted_taggedtrait_output.extend(output2)

# Write out the tagging data to a file.
mapping_fn = output_prefix + '_tagged_variables.txt'
mapping_file = open(mapping_fn, 'w')
mapping_file.write(' \n'.join(formatted_taggedtrait_output))
mapping_file.close()
print('Saved tag-variable mapping data to', mapping_fn)

# Write out a data dictionary file.
mapping_DD_fn = mapping_fn.replace('.txt', '_data_dictionary.txt')
mapping_DD_file = open(mapping_DD_fn, 'w')
mapping_DD_file.write('column_name \tcolumn_description\n')
mapping_DD_file.write( ' \n'.join([' \t'.join(el) for el in output_columns]) )
mapping_DD_file.close()
print('Saved tag-variable mapping data dictionary to', mapping_DD_fn)

########################################################################################################################
# Make a README file with background information on the project.
readme_sections = (
    ('# TOPMed variable tagging project', ),
    ('## Description', 
        """This data package contains the results of the TOPMed Data Coordinating Center's (DCC's) phenotype tagging \
project. This project aims to increase the value of dbGaP data from the multiple studies that make up TOPMed, \
as a part of the NIH Data Commons Pilot Phase Consortium. To achieve this goal, we tagged dbGaP variables with \
informative labels indicating the phenotype concept represented by each variable. The data package consists of \
full descriptions of each phenotype tag and the mappings between the dbGaP variables and phenotype tags. \
"""
    ),
    ('## Contact', 
        "Please let us know how you're using this data package!",
        "To initiate collaborative work with this data package, or for other questions, contact:\n",
        "Leslie Emery, emeryl@uw.edu\n",
        "Research scientist\n",
        "Genetic Analysis Center & TOPMed Data Coordinating Center\n",
        "Department of Biostatistics, University of Washington\n",
    ),
    ('## File descriptions', 
        "* {} - latest definition of phenotype tags, as exported from our internal webapp database".format(os.path.split(dump_fn)[-1]),
        "* {} - data dictionary providing information on each of the elements in the previous file".format(os.path.split(dump_DD_fn)[-1]),
        "* {} - tab-delimited text file providing mappings between dbGaP variables and tags".format(os.path.split(mapping_fn)[-1]),
        "* {} - data dictionary providing information on each of the data columns in the previous file".format(os.path.split(mapping_DD_fn)[-1]),
    ),
    ('### Background information', 
        """For more information on the dbGaP data and the organizational structure of TOPMed, be sure to read the \
[TOPMed DCPPC white paper](https://docs.google.com/document/d/1e77a7dZ9I1FcXHbK-CXkbXmP5xywsw1dePsoxX_E6OM/edit?usp=sharing). \
In particular, you should read sections VII and VIII for information on dbGaP data and another \
description of the tagging project. \
"""
    ),
    ('### The tagging process', 
        """We defined tags for 65 phenotypes prioritized by the NHLBI, TOPMed phenotype working groups, and other \
stakeholders. Seven large cohort studies (ARIC, CHS, CARDIA, FHS, JHS, MESA, and WHI) received subcontract \
funding for their data experts to perform tagging. Tagging for remaining studies was performed by members of the \
DCC phenotype team. The DCC added tagging functionality to a webapp that was already developed for internal use. \
The webapp allowed easy selection of one or more tags for a dbGaP variable and performed error checking. \
A mapping between a single dbGaP variable and a single tag will be referred to as a 'tagged variable'. \
"""
        "After initial tagging, all tagged variables were checked in a 3-step quality review process:",
        "1. Initial review by the DCC: confirm or flag for removal",
        "2. Response by study experts: agree to removal or provide explanation of why a tagged variable should remain",
        "3. Final decision by the DCC: confirm or remove",
        "The tagged variables in this data package have all passed this 3-step quality review process."
    ),
    ('### Goals', 
        '#### Short-term goals',
        '* Enable creation of cross-study datasets with similar phenotype variables',
        '* Enable indexing & searching phenotype variables',
        '* Assist with identification of phenotype variables for harmonization of data values',
        '#### Long-term goals',
        '* Train and evaluate automated methods for classifying phenotype variables (e.g. machine learning/natural language processing)',
        '* Enable indexing & searching via ontology terms or synonyms'
    ),
    ('## Caveats', 
        """* We have been updating the tag descriptions and instructions as necessary in response to questions that have \
arisen during the tagging process. If you observe later discrepancies in tag titles, descriptions, or \
instructions, this is probably the reason, but the tag_pk won't change.
"""
        """* The 'age at enrollment/collection' tag includes many variables that don't contain actual age information. We \
asked study representatives to tag both age variables and variables that could be used to calculate age, \
for example 'days since exam 1' for a laboratory test. 'Age at enrollment/collection' is intended to be useful \
for actually finding the variables you want to use, but may present some difficulties for developing automated \
approaches.
"""
        """* The 'medication/supplement use' tag has a much broader definition than the other tags, because it would be \
impractical to ask the study data experts to tag variables for dozens of different kinds of medications. \
Also, the ways that medication datasets are often collected from study subjects (e.g. recall questionnaires, \
physical inventories of medication by a study staff member, etc.) make it difficult to distinguish variables for \
different kinds of medication from one another. Finally, we found that it was difficult to provide clear \
guidance on differentiating between medication (over-the-counter and/or prescription) and dietary supplements. \
The two kinds of data are often collected together and the judgement on whether a particular substance is a \
'medication' or a 'supplement' can be subjective. This led to us including both in the tag. This may make the \
'medication/supplement use' tag difficult to use for developing automated approaches.
"""
        """* We concentrated our efforts on tagging the variables for the dbGaP version of each study that was released at \
the time we began the tagging project. During the course of the tagging, at least two studies (ARIC and FHS) \
released updated dbGaP versions. If a given dbGaP variable is still present in the updated study version, its \
variable accession (phv) will be the same. However, some variables may be removed in the updated study version, \
which will result in the new version not containing a variable with the phv in question.
"""
    ),
    ('## Release notes', 
        "### 2018-12-27",
        """First official release since completion of quality review. Added README file, data dictionaries, and more \
columns for study and dataset accessions. \
"""
    ),
    ('## Acknowledgements', 
        '### TOPMed DCC phenotype team',
        '* Cathy Laurie',
        '* Leslie Emery',
        '* Adrienne Stilp',
        '* Alyna Khan',
        '* Fei Fei Wang',
        '* Jai Broome',
        '### Consultation',
        '* Susan Redline',
        '* Susan Heckbert',
        '### Study representatives:',
        '* Cathy D’Augustine (FHS)',
        '* Karen Mutalik (FHS)',
        '* Nancy Heard-Costa (FHS)',
        '* Chance Hohensee (WHI)',
        '* David Vu (MESA)',
        '* Dongquan Chen (CARDIA)',
        '* Lucia Juarez (CARDIA)',
        '* Kim Lawson (ARIC)',
        '* Laura Raffield (JHS)',
        '* Tony Wilsdon (CHS)',
    ),
    ('## Project status', 
        """We are working on updating our tagged variables for updated dbGaP study versions. More tagged variables may \
be added in the future. We have also mapped our tags to UMLS terms and are working on tracking that information \
and providing it in future data packages. In the meantime, you can view our mapping of phenotype tags to UMLS terms \
in [this Google sheet](https://docs.google.com/spreadsheets/d/1zwUp-7dmcotaEAFti7j7d4S-4UoTPEXXGhHxDx3cwmo/edit?usp=sharing).
"""
    ),
)

# Write out the readme file.
readme_fn = output_dir + 'README.md'
readme_file = open(readme_fn, 'w')
readme_file.write(' \n \n'.join( [' \n'.join(el) for el in readme_sections] ))
readme_file.close()
print('Saved README file to', readme_fn)

########################################################################################################################
# tar and gzip the directory
tar_fn_root = os.path.split(output_dir)[0]
split_output_dir = os.path.split(os.path.split(output_dir)[0])

tar_command = ['tar', '-zcvf', '{}.tar.gz'.format(tar_fn_root), '--directory={}'.format(split_output_dir[0]), split_output_dir[1]]
print(' '.join(tar_command))
check_call(tar_command)

########################################################################################################################
# # Print the counts for each tag
# annotated_tags = Tag.objects.annotate(Count('traits'))
# 
# for tag in annotated_tags:
#     print(tag.title, tag.traits__count)
# 
# # Print the tag + study counts to a tab-delimited file.
# study_tag_counts_dict = dict(
#     (study,
#      TaggedTrait.objects.filter(trait__source_dataset__source_study_version__study=study).values(
#         'tag__pk').annotate(
#             count=Count('pk', distinct=True))
#     ) for study in Study.objects.all()
# )
# 
# annotated_studies = [(study, [(Tag.objects.get(pk=tag['tag__pk']), tag['count']) for tag in study_tag_counts_dict[study]]) for study in study_tag_counts_dict]
# 
# header = ['study_phs', 'study_name', 'tag_title', 'tagged_variable_count']
# output = []
# output.append(' \t'.join(header))
# 
# for (study, tag_list) in annotated_studies:
#     for (tag, count) in tag_list:
#         output.append(' \t'.join((str(study.pk), study.i_study_name, tag.title, str(count))))
# 
# # count_fn = output_prefix + '_tagging_counts.txt'
# # count_file = open(count_fn, 'w')
# # count_file.write(' \n'.join(output))
# # count_file.close()
# # print('Saved counts data to', count_fn)
