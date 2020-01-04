Tests
================================================================================

Organization of tests
--------------------------------------------------------------------------------

For every module in PIE that has testable code, there exists a corresponding test module. For example, within the ``tags`` app, there is a test module ``test_models.py`` corresponding to the module ``models.py``. The partial directory listing below shows the modules with testable code and their corresponding test modules. ::

    tags
    ├── admin.py
    ├── test_admin.py
    ├── factories.py
    ├── test_factories.py
    ├── forms.py
    ├── test_forms.py
    ├── management
    │   └── commands
    │       ├── export_tagging.py
    │       └── test_export_tagging.py
    ├── models.py
    ├── test_models.py
    ├── tables.py
    ├── test_tables.py
    ├── test_views.py
    └── views.py

Tests use the `Django testing framework <https://docs.djangoproject.com/en/1.11/topics/testing/>`_, which is built on Python's `unittest <https://docs.python.org/3.5/library/unittest.html>`_. There is generally one ``TestCase`` class for each PIE function or class to be tested, though tests for more complicated structures may be split into multiple ``TestCase`` classes. While a single ``assert`` statement per test method is desirable, in some cases there are multiple ``assert`` statements per test - usually to prevent too much repetition of code used to make fake data objects for testing.

Inventory of current tests
--------------------------------------------------------------------------------

.. Find all of the test files: tree -P test*.py | grep -v pycache

::

    ├── core
    │   ├── management
    │   │   └── commands
    │   │       └── test_increment_version.py
    │   ├── templatetags
    │   │   └── test_core_tags.py
    │   ├── test_factories.py
    │   └── test_migrations.py
    ├── phenotype_inventory
    │   ├── settings
    │   │   └── test_settings.py
    │   ├── test_admin.py
    │   └── test_email_sending.py
    ├── profiles
    │   ├── test_models.py
    │   └── test_views.py
    ├── recipes
    │   ├── test_factories.py
    │   ├── test_forms.py
    │   ├── test_models.py
    │   └── test_views.py
    ├── selenium_tests
    │   └── test_selenium_development.py
    ├── tags
    │   ├── management
    │   │   └── commands
    │   │       └── test_export_tagging.py
    │   ├── test_admin.py
    │   ├── test_factories.py
    │   ├── test_forms.py
    │   ├── test_models.py
    │   ├── test_tables.py
    │   └── test_views.py
    └── trait_browser
    ├── management
    │   └── commands
    │       ├── test_fill_fields.py
    │       └── test_import_db.py
    ├── test_factories.py
    ├── test_forms.py
    ├── test_models.py
    ├── test_searches.py
    ├── test_tables.py
    └── test_views.py


Running all of the tests
--------------------------------------------------------------------------------

To run all of the tests in the entire project (currently more than 2,000 test methods), you can use Django's builtin test runner. ::

    # Run all the tests. This will take a very long time.
    ./manage.py test

Database for testing purposes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When Django runs tests, it needs to able to access data and manipulate the database without endangering the data in the "real" project database that is currently in use (this could be a local development database, or the production database for the deployed site). In order to run tests without affecting the data in the real project database, Django creates a special "test database" that is used for tests. The first time you run a test in your current working environment, Django will create the test database. Every time a test method is run, the test database schema will be rebuilt. The test database schema will be emptied at the end of each test method.

 The test database has the same settings as the real database, but the database name is prepended with "test_". For example, if you are working in a local production environment and using a database named ``pie``, the test database will be named ``test_pie``. So for testing purposes you will need to set up access to a database named ``DATABASES['default']['NAME']`` (from the settings file) and a testing database named ``'test_' + DATABASES['default']['NAME']``.


Running selected tests
--------------------------------------------------------------------------------

You can select individual test modules, classes, or methods to run by specifying their path in Python module/function format. See the following examples. ::

    # Run all tests from the tags/test_models.py module
    ./manage.py test tags.test_models
    
    # Run all tests from the class TagTest
    ./manage.py test tags.test_models.TagTest
    
    # Run a specific test method
    ./manage.py test tags.test_models.TagTest.test_unique_lower_title


Prioritizing which tests to run
--------------------------------------------------------------------------------

Because running all of the tests can take a very long time, the following commands are often used to selectively run the most relevant tests. The ``--verbosity=2`` option is used to print the name and status of each individual test method as it is run. ::

    # Run tests for all of the custom-written apps, but don't run trait_browser's test_import_db
    # Should take <30 min to run
    ./manage.py test tags --verbosity=2
    ./manage.py test profiles --verbosity=2
    ./manage.py test recipes --verbosity=2
    ./manage.py test core --verbosity=2
    ./manage.py test trait_browser.test_views --verbosity=2
    ./manage.py test trait_browser.test_forms --verbosity=2
    ./manage.py test trait_browser.test_models --verbosity=2
    ./manage.py test trait_browser.test_searches --verbosity=2
    ./manage.py test trait_browser.test_tables --verbosity=2
    ./manage.py test trait_browser.test_factories --verbosity=2

    # Test just the views from every custom app
    ./manage.py test profiles.test_views --verbosity=2
    ./manage.py test recipes.test_views --verbosity=2
    ./manage.py test tags.test_views --verbosity=2
    ./manage.py test trait_browser.test_views --verbosity=2


Assessing test coverage
--------------------------------------------------------------------------------

To see how much of the project code is tested (the "test coverage"), you can use the Python ``coverage`` package when running all of the tests. ::

    # Run test coverage
    coverage run --source='.' manage.py test
    coverage report # text output
    coverage html # html output
    
    # On a mac, open the index.html file in the default browser
    open htmlcov/index.html


Tests of ``import_db``
--------------------------------------------------------------------------------

The management command ``import_db`` tests the ability of the PIE project code to import data from a database mimicking the structure of the TOPMed DCC's phenotype harmonization database. Those outside of the DCC are unlikely to want to use the ``import_db`` command, or to run its tests from ``test_import_db``.

Source DB test data files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DCC team members who need to run ``test_import_db`` will need to obtain test database files. You can either copy existing files from another PIE developer, or create a new version of the files. The script that creates these test database files is located in the ``topmed_pheno_database`` repository at ``R_code/make_phenotype_inventory_test_data.R``. The test database files should be saved to the ``trait_browser/source_db_test_data`` directory. ::

    # Copy files from another location
    cp -R other_copy_of_pie_repo/trait_browser/source_db_test_data my_copy_of_pie_repo
    
    # Make new files
    workon topmed_pheno_database
    source /projects/topmed/working_code/phenotype_harmonization/env/activate_pheno_env
    ./make_phenotype_inventory_test_data.R my_copy_of_topmed_pheno_database_repo my_copy_of_pie_repo/trait_browser/source_db_test_data

Running ``test_import_db``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you have your test source db files set up, you are ready to run the ``import_db`` tests, in part or in full. ::

    # Run a subset of test classes from test_import_db to find failures quickly
    # Should take <30 min to run
    ./manage.py test trait_browser.management.commands.test_import_db.GetSourceDbTest --verbosity=2
    ./manage.py test trait_browser.management.commands.test_import_db.DbFixersTest --verbosity=2
    ./manage.py test trait_browser.management.commands.test_import_db.BackupTest --verbosity=2
    ./manage.py test trait_browser.management.commands.test_import_db.ImportHelperTest --verbosity=2
    ./manage.py test trait_browser.management.commands.test_import_db.UpdateHelperTest --verbosity=2
    ./manage.py test trait_browser.management.commands.test_import_db.IntegrationTest.test_imported_ids_match_source_ids --verbosity=2
    
    # Run all of the test of import_db
    # This may take up to 2 hours to run
    ./manage.py test trait_browser.management.commands.test_import_db --verbosity=2


Tests that are skipped by default
--------------------------------------------------------------------------------

Currently, two test methods from the test module ``trait_browser/management/commands/test_import_db.py`` are skipped by default during test runs. ::

    trait_browser.management.commands.test_import_db.LockSourceDbTest.test_locks_all_tables_production
    trait_browser.management.commands.test_import_db.UnlockSourceDbTest.test_unlocks_all_tables_production

These tests are skipped by default because they test the ability of the ``import_db`` management command to lock and unlock the production deployment of the DCC's phenotype harmonization database. Locking and unlocking this database is disruptive to DCC phenotype harmonization work, so while these test methods can be run by commenting out the ``@skip`` decorator, this should happen very sparingly. A good rule of thumb is to run these test methods only when a finished branch is about to be merged into the ``devel`` or ``master`` branch.


Selenium tests
--------------------------------------------------------------------------------

Tests found at ``selenium_tests/test_selenium_development.py`` use the `Selenium webdriver <https://selenium.dev/projects/>`_ to test the overall PIE site interface by automating control of a web browser. Selenium tests check that expected menu items exist on the pages where they are intended, clicking on menus and links works as expected, and search results are displayed as expected. Very few Selenium tests have been added so far, so many aspects of the site interface remain untested.


Chromedriver setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to run the Selenium tests using Google Chrome, you will need to download the latest version of ``chromedriver`` from `Google's documentation site <https://sites.google.com/a/chromium.org/chromedriver/>`_. Then save the file to the ``selenium_tests`` directory within your PIE project. Now you should be able to run the Selenium tests. ::

    # This is only tested on macOS with Chrome so far
    # Run Selenium tests
    ./manage.py test selenium_tests.test_selenium_development --verbosity=2


Browser and OS compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

So far, Selenium tests for PIE have only been run in macOS using the Google Chrome browser. The original project configuration used Firefox on macOS to run Selenium tests, but Firefox testing failed after some changes in Selenium. At this point, testing was switched to using Google Chrome.


Selenium server ``.jar`` file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The most-recently-tested version of Selenium server used in running the Selenium tests is checked in to this repository and can be found at ``selenium_tests/selenium-server-standalone-2.53.0.jar``. In the future, we may reconsider the decision to keep this file version controlled.
