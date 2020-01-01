Project dependencies
================================================================================


Overview of project dependencies
--------------------------------------------------------------------------------

.. cat env_requirements/requirements.in

* ``Django==1.11.22`` is the currently required Django version for this project.
* ``coverage`` produces testing coverage reports.
* ``django-authtools`` customizes the Django user model. Customization of the user model include using email instead of username, replacing separate first and last name fields with a single name field, and setting default passwords upon account creation. `on GitHub <https://github.com/fusionbox/django-authtools>`_
* ``django-autocomplete-light`` is used for auto-complete functionality within form fields. `on GitHub <https://github.com/yourlabs/django-autocomplete-light`_
* ``django-braces`` provides Mixins for Django's class-based views. `on GitHub <https://github.com/brack3t/django-braces>`_
* ``django-crispy-forms`` provides advanced form customization and templating. `on GitHub <https://github.com/django-crispy-forms/django-crispy-forms>`_
* ``django-dbbackup`` creates database backups (SQL dump files) and restores from backups, all from a Django command. `on GitHub <https://github.com/django-dbbackup/django-dbbackup>`_
* ``django-debug-toolbar==1.9.1`` provides a toolbar for advanced debugging on local development and staging sites. `on GitHub <https://github.com/jazzband/django-debug-toolbar>`_
* ``django-extensions`` provides many useful utility extensions to Django, including making schema diagrams, validating templates, an enhanced shell, and much more. `on GitHub <https://github.com/django-extensions/django-extensions>`_
* ``django-maintenance-mode`` provides a management command to put the site into "maintenance mode" during code updates, when a custom 503 error page will be shown to users who try to access the site `on GitHub <https://github.com/fabiocaccamo/django-maintenance-mode>`_
* ``django-tables2`` provides classes used to make customized html tables from the project's data models. `on GitHub <https://github.com/jieter/django-tables2>`_
* ``django-watson`` is used to build text search of study variables and datasets. `on GitHub <https://github.com/etianen/django-watson>`_
* ``docutils`` is required by the ``admindocs`` app to produce documentation that is available in the site's admin interface. `Django documentation of admindocs <https://docs.djangoproject.com/en/1.11/ref/contrib/admin/admindocs/>`_
* ``factory-boy`` is used extensively in tests to generate fake data for each Django model. `on GitHub <https://github.com/FactoryBoy/factory_boy>`_
* ``flake8`` checks for PEP 8 inconsistencies.
* ``flake8-docstrings`` checks for PEP 257 inconsistencies.
* ``mysql-connector-python-rf`` is an API for connecting to MySQL/MariaDB databases. Used in ``import_db`` for connecting to the DCC's phenotype harmonization database.
* ``mysqlclient==1.3.12`` might be required by ``mysql-connector-rf`` or Django itself. It's unclear.
* ``pygraphviz==1.3.1`` is used by ``django-extensions`` for graphing the database schema. Unless you use that command in ``django-extensions``, this dependency is not required.
* ``pytz`` is used for timezone support.
* ``selenium`` provides automated browser-based interface testing. `Selenium project <https://selenium.dev/>`_
* ``sphinx`` generates Python documentation pages. `Sphinx <http://www.sphinx-doc.org/en/master/>`_
* ``pip-tools`` provides advanced options for managing dependencies in the project ``virtualenv``. `on GitHub <https://github.com/jazzband/pip-tools>`_

Using `pip-tools` to manage dependencies
--------------------------------------------------------------------------------

This project uses ``pip-tools`` to manage dependencies. A common practice is to store a static set of package dependencies in the ``requirements.txt`` file. But this method doesn't allow for very flexible control of versions in the requirements. ``pip-tools`` instead uses a ``requirements.in`` file that is compiled to a ``requirements.txt`` file with pinned version numbers for each package. ``pip-tools`` should be used any time a package in PIE's requirements is updated. ::

    # Compile the project's requirements.in file
    pip-compile env_requirements/requirements.in

Update all packages in the requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pip-compile --upgrade env_requirements/requirements.in

Update a specific package in the requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pip-compile --upgrade-package django==1.11.30 env_requirements/requirements.in

Update the currently active ``virtualenv`` to match the project's requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pip-sync env_requirements/requirements.txt
