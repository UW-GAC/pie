Getting study phenotype metadata
================================================================================

The models in the ``trait_browser`` app are designed to store metadata parsed from two main sources:

* Study phenotypes: dbGaP phenotype data dictionaries
* Harmonized phenotypes: DCC-harmonized phenotype datasets

At the TOPMed DCC, we use the ``import_db`` management command to pull all of this data out of our phenotype harmonization database. However, this database is not available outside of the DCC. If someone wanted to run another instance of the PIE web application, they would need to obtain this data from other sources. Below are some suggestions for how one might do this.

Study phenotypes
--------------------------------------------------------------------------------

Parse the ``.xml`` data dictionary files for phenotype datasets. The ``.xml`` data dictionaries can be obtained from the `dbGaP ftp site <ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/>`_ or by downloading phenotype data from an approved dbGaP controlled access data request. The study phenotype metadata from these ``.xml`` data dictionaries could be used to fill in data from the following ``trait_browser`` models::

    Study
    SourceStudyVersion
    Subcohort
    SourceDataset
    SourceTrait
    SourceTraitEncodedValue


Harmonized phenotypes
--------------------------------------------------------------------------------

Documentation for reproducing the DCC's harmonized phenotype data will soon be `available on GitHub <https://github.com/UW-GAC/topmed-dcc-harmonized-phenotypes>`_. The harmonized phenotype metadata from the ``.json`` documentation files could be used to fill in data from the following ``trait_browser`` models::

    HarmonizedTraitSet
    HarmonizedTraitSetVersion
    HarmonizationUnit
    HarmonizedTrait
    HarmonizedTraitEncodedValue

More complicated cases
--------------------------------------------------------------------------------

For some of the models, it will not be as straightforward to fill the data from dbGaP data dictionaries or DCC-harmonized phenotype documentation.

* The ``GlobalStudy`` model connects dbGaP studies (of the ``Study`` model) that comprise a single TOPMed study. Two dbGaP studies may be connected to the same ``globalstudy`` object. The data for making this connection is currently available only in the DCC's phenotype harmonization database. However, ``GlobalStudy`` data is not currently used in the main functions of PIE. ``GlobalStudy`` could be safely left without any data. 
* The ``AllowedUpdateReason`` contains the set of allowed reasons for updating a DCC-harmonized phenotype variable. ``AllowedUpdateReason`` data is not currently used in the main functions of PIE and could be safely left without any data.
