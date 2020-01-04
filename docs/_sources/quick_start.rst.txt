PIE quick start guide
================================================================================

Follow these steps to set up a local development version of PIE:

1. Clone the git repository
--------------------------------------------------------------------------------

::

    git clone https://github.com/UW-GAC/pie.git

2. Set up a Python virtual environment using ``virtualenv``
--------------------------------------------------------------------------------

Before running the following commands, make sure you have ``pip`` and ``virtualenv`` installed for the version of Python 3 you plan to use. ::

    virtualenv ~/virtualenv/pie

In this example the virtual environment is set up at ``~/virtualenv`` but you can install it in any location you'd like.


3. Activate the virtual environment and install required packages
--------------------------------------------------------------------------------
::

    # Change directory into the PIE git repository.
    cd pie
    source ~/virtualenv/pie/bin/activate
    pip install -r env_requirements/requirements.txt

One of PIE's requirements has a feature that plots the structure of the backend database. This feature requires that you have the package ``graphviz`` installed. If you don't need this schema plotting feature, you can ignore the error message about not being able to install ``pygraphviz`` due to missing ``graphviz``.


4. Choose settings and database
--------------------------------------------------------------------------------

You will need to set up a database for PIE to use to store the app's data. You may choose to use SQLite (the quickest and easiest way, but less similar to production settings). Or you may choose to use a SQL database server, e.g., MySQL, MariaDB, or PostgreSQL. The DCC uses MariaDB. Either way you will need to modify the virtual environment's activate file with the local settings you are going to use.

Open up the file for editing in a simple command line editor. ::

    nano ~/virtualenv/pie/bin/activate


Use local SQLite settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You will need to make sure you have SQLite installed on your system first. Add the following lines to the end of the ``activate`` file, with values in angle brackets (<>) filled in with the appropriate values. ::

    export PYTHONPATH='<path_to_pie_repo>/pie/phenotype_inventory'
    export DJANGO_SETTINGS_MODULE='phenotype_inventory.settings.local_sqlite'
    export DJANGO_SECRET_KEY="<add a secret key here>"


Or use a SQL database server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You will need to make sure that the database server is set up and you can log in to the SQL shell with the database settings you are going to save in your activate file. Add the following lines to the end of the ``activate`` file, with values in angle brackets (<>) filled in with the appropriate values. ::

    export PYTHONPATH='<path_to_pie_repo>/pie/phenotype_inventory'
    export DJANGO_SETTINGS_MODULE='phenotype_inventory.settings.local'
    export DJANGO_SECRET_KEY="<add a secret key here>"
    export DB_NAME='<name_of_development_DB>'
    export DB_HOST='<hostname_of_development_DB'
    export DB_PORT='<port_of_development_DB>'
    export DB_USER='<username_for_development_DB>'
    export DB_PASS='<password_for_development_DB>'


Getting a secret key value
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Django secret key is used for hashing secure data (e.g., passwords, sessions). It should always be kept **secret** and should never be committed to a code repository. You will need to create a secret key to insert into the settings in your ``virtualenv`` activate file. To create a secret key value, you can use `this free web tool <https://miniwebtool.com/django-secret-key-generator/>`_. Or if you have access to an installed Django application using the ``django-extensions`` app, you can use the ``generate_secret_key`` management command like so::

    ./manage.py generate_secret_key


5. Reactivate ``virtualenv`` with new settings
--------------------------------------------------------------------------------

Now that you've added your Django settings to the ``virtualenv`` ``activate`` script, you'll need to deactivate and reactivate the environment. ::

    deactivate
    source ~/virtualenv/bin/activate


6. Set up the database tables
--------------------------------------------------------------------------------

In order to create the database tables used to store data for the Django site, you will need to run Django migrations, which are a set of Django scripts used to set up the database schema. ::

    # Look at the available migrations and which have been run or not so far.
    ./manage.py showmigrations
    # Run all of the migrations needed.
    ./manage.py migrate


7. Make sure your database connection works
--------------------------------------------------------------------------------

Log into the database shell to make sure that Django is able to communicate with the database you have specified. ::

    ./manage.py dbshell


8. Running tests
--------------------------------------------------------------------------------

To test that the PIE code works as expected, you can run tests on your development setup. ::

    # Run all the tests. This will take a very long time to run hundreds of tests.
    ./manage.py test

``test_import_db`` will fail without test data obtained from the DCC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can obtain test data for use by the test_import_db test module by contacting the DCC. The test source data is a set of MariaDB database dump files mimicking the structure of the TOPMed DCC's phenotype harmonization database. Because the harmonization database is not available outside of the DCC, it is unlikely that this test data will be useful to those outside of the DCC. ::

    # test_import_db tests will fail
    Creating test database for alias 'default'...
    <Many test errors will show up here>
    Ran 53 tests in 0.283s

    FAILED (errors=37, skipped=2)
    Destroying test database for alias 'default'...

Running a minimal set of tests to see that the code works as expected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instead of running all of the tests as shown above, you can run a select set of tests that demonstrate that most of the functionality of PIE works as expected. ::

    ./manage.py test tags
    ./manage.py test profiles
    ./manage.py test recipes
    ./manage.py test core
    ./manage.py test trait_browser.test_views
    ./manage.py test trait_browser.test_forms
    ./manage.py test trait_browser.test_models
    ./manage.py test trait_browser.test_searches
    ./manage.py test trait_browser.test_tables
    ./manage.py test trait_browser.test_factories


9. Create a superuser account for login
--------------------------------------------------------------------------------

You will need a superuser account to administer your development Django site. ::

    ./manage.py createsuperuser

You will be prompted to enter an email address and password for this Django administrator account.


10. Make some fake data to fill your development site with
--------------------------------------------------------------------------------

PIE has a function that will create fake data to fill your development site with. Run that function now from within the Django shell so that your development site isn't empty. ::

    ./manage.py shell
    >>> from core.build_test_db import build_test_db
    >>> build_test_db()


11. Run a development server
--------------------------------------------------------------------------------

Run the Django builtin web server (which is intended only for development purposes). This will serve a copy of the PIE app that is only available to you locally. ::

    ./manage.py runserver

Now you should be able to view your development version of PIE by navigating to http://127.0.0.1:8000 in your favorite browser.


12. Deactivate the virtual environment when you're done working on PIE
--------------------------------------------------------------------------------

In order to return your shell environment to normal function, make sure to deactivate the PIE ``virtualenv`` when you're done. ::

    deactivate
