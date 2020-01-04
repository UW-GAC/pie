Documentation
================================================================================

Built with Sphinx
--------------------------------------------------------------------------------

The documentation is built with Sphinx. Source files are stored in ``doc_source`` and a GitHub Pages-compatible deployment is stored in ``docs``. The GitHub Pages site is served from the ``master`` branch ``docs`` directory. The ``conf.py`` file store the code information, Sphinx settings including build directory, etc. ``Makefile`` determines the deployed ``docs`` directory.

Resources on Sphinx
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#internal-links
* http://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#ref-role
* https://pythonhosted.org/an_example_pypi_project/sphinx.html


Updating the build
--------------------------------------------------------------------------------

To build a new version of the html pages for local preview::

    make html

To build a new version of the html pages for deploying to GitHub::

    make github


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Deployment on GitHub Pages
--------------------------------------------------------------------------------

The following resources were used for setting up the deployment on GitHub Pages:

* https://www.scivision.dev/sphinx-python-quickstart/
* https://www.docslikecode.com/articles/github-pages-python-sphinx/
    * Followed directions from this link to add ``make github`` option to Makefile
