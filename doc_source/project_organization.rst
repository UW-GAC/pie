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
Sets up the admin interface for use by DCC users

django.contrib.admindocs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Adds documentation of code methods and functions on the admin site

django.contrib.auth
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Adds user accounts

django.contrib.sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sets up user sessions

django.contrib.sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Used to set the site name and domain

django.contrib.flatpages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Allows for adding static ("flat") pages by users from the admin interface



Installed 3rd-party Django apps
--------------------------------------------------------------------------------

django-autocomplete-light
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Allows autocompletion of text in form fields

debug_toolbar
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Displays advanced debugging information on the staging and development versions of the site

django_tables2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Used to make formatted html tables from Django model data

crispy_forms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Allows advanced formatting of forms

django_extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Provides many extra functions for Django

authtools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Extends the user model by using email instead of username and allowing setup of accounts with a random password

dbbackup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Makes and restores from SQL backup files via Django code

maintenance_mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Displays a maintenance page on the site when activated, and prevents login of data entry

watson
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add full text search functionality of specified model fields


Custom Django apps
--------------------------------------------------------------------------------

trait_browser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Models for the phenotype data, both study phenotypes and harmonized phenotypes

core
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Site-wide functionality that doesn't fit a specific app

profiles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A profile model to attach data to specific users

recipes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Not fully implemented; user-created recipes for describing how harmonization should be done

tags
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Allows tagging study phenotype variables with phenotype concept labels
