Django project configuration
================================================================================

Django settings files
--------------------------------------------------------------------------------

PIE uses a group of settings modules rather than a single Django settings file. Settings modules are located at ``phenotype_inventory/settings``. An explanation for each settings module is below:

* ``base.py``: Common settings shared across all configurations. Includes directory, site name, language, time zone, static file, template, message, middleware, installed apps, sitewide URL, and app-specific settings. Inherited by each of the more specific settings files.
* ``local.py``: Settings specific to local development environments. Uses environment variables (stored in the ``virtualenv`` `activate` script) to set Django secrets.
* ``local_sqlite.py``: Setting for a local development environment using SQLite as the backend. Creates a SQLite database file named ``phenotype_inventory.sqlite3``. Uses environment variables (stored in the ``virtualenv`` ``activate`` script) to set Django secrets.
* ``production.py``: Settings specific the DCC's production environment for PIE. These settings are responsible for deployment of the site at topmephenotypes.org. Django secrets are manually set on the production server. Designed to work with a WSGI Apache deployment.
* ``staging.py``: Settings specific the DCC's staging environment for PIE. These settings are responsible for deployment of the site on an internal-use staging server. Django secrets are manually set on the staging server. Designed to work with a WSGI Apache deployment.


Django secrets
--------------------------------------------------------------------------------

Many of the Django configuration settings should be kept "secret". For the local development environments, these secrets are stored as shell environmental variables. In Apache deployment environments they are manually set on the server. Secrets include the following:

* Database login settings
* Secret key for hashing
* Email login settings


Database backend
--------------------------------------------------------------------------------

The DCC uses a MariaDB database server as the backend for PIE. PIE should be largely compatible with any of the Django-allowed database backend options, but this has not been tested. For local development purposes, you may use a SQLite database - a file-based database format which doesn't require setting up a database server. SQLite should not be used in production environments.

