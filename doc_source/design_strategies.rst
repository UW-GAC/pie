Design strategies
================================================================================

* Class-based views are preferred over function-based views
* Test modules should be located in the same directory as the module they test, and named for the module they test with the "test_" prefix

Project style guidelines
--------------------------------------------------------------------------------

* PIE project code style is to comply with `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_
* Every function and method should have a docstring that complies with `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_
* Project style choices, generally in keeping with the Django style guide, are documented in the ``setup.cfg`` file
* Always include an informative commit message
* You can check for code that breaks the style guidelines by running ``flake8`` from the project's ``virtualenv``