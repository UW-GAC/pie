Project organization
================================================================================

Project directory structure
--------------------------------------------------------------------------------

.. Get a basic dir structure for later editing: tree -d | grep -v pycache | grep -v migration | grep -v management | grep -v commands

See the annotated directory structure below. ::

    ├── core = A custom Django app; contains core functionality that doesn't fit in any other apps
    ├── doc_source = Source files for building the documentation
    ├── docs = The deployed version of the built documentation
    ├── env_requirements = Python virtualenv requirements files for specifying versioned dependencies
    ├── phenotype_inventory = Central Django files for project and server configuration
    │   └── settings
    ├── profiles = A custom Django app; adds a "profile" object for each user
    ├── recipes = A custom Django app; currently not fully implemented; features for building recipes for phenotype harmonization
    ├── selenium_tests = Automated interactive tests using Selenium webdriver
    ├── static = static resources, e.g., CSS, fonts, JavaScript, images, etc.
    │   ├── bootstrap
    │   │   ├── css
    │   │   ├── fonts
    │   │   └── js
    │   ├── css
    │   ├── icons
    │   ├── js
    │   └── topmed_logo
    ├── tags = A custom Django app; features for tagging study phenotype variables and performing quality review of tagged variables
    ├── templates = Django html template files for every view in the project, organized into subdirectories corresponding to each app
    │   ├── crispy_forms
    │   ├── flatpages
    │   ├── profiles
    │   ├── recipes
    │   ├── registration
    │   ├── tags
    │   └── trait_browser
    └── trait_browser = A custom Django app; features for parsing, browsing, and searching metadata for dbGaP phenotype files


Builtin Django apps in use
--------------------------------------------------------------------------------

Some builtin Django apps are optional, but are in use by PIE. Descriptions of each follow below.

django.contrib.admin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django.contrib.admindocs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django.contrib.auth
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django.contrib.sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django.contrib.sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django.contrib.flatpages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^




Installed 3rd-party Django apps
--------------------------------------------------------------------------------

django-autocomplete-light
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


debug_toolbar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django_tables2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


crispy_forms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


django_extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


authtools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


dbbackup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


maintenance_mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


watson
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Custom Django apps
--------------------------------------------------------------------------------

trait_browser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


core
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


profiles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


recipes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


tags
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
