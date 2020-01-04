Custom management commands
================================================================================

.. Find all management commands: ls -1 */management/commands/*.py


increment_version
--------------------------------------------------------------------------------

Sets the version numbers (major and minor) in the ``version.json`` file. Used when finalizing a release branch.

export_tagging
--------------------------------------------------------------------------------

Exports tagging data in the format that has been distributed to collaborators.


fill_fields
--------------------------------------------------------------------------------

Saves a field to the ``HarmonizedTrait`` model that includes the component trait information in formatted html for display on the ``HarmonizedTraitDetail`` page.


import_db
--------------------------------------------------------------------------------

Copies phenotype metadata (both study phenotypes and harmonized phenotypes) from the DCC's phenotype harmonization database to the PIE backend database.

