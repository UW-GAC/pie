# TOPMed DCC Phenotype Inventory Explorer (PIE)

The TOPMed data coordinating center (DCC) uses the web app PIE as a central location for viewing and searching TOPMed phenotype data. It is primarily of use for our work on phenotype harmonization. PIE can be found at [topmedphenotypes.org](https://topmedphenotypes.org/), with most of the app available only behind a login.

## Features
The main features of PIE are described below.

1. Browse

Browse the TOPMed phenotype data that is available so far. Browse study variables from released dbGaP accessions by study, by dataset, or by variable. Browse DCC-harmonized variables and the component variables used in harmonization.

2. Search

Search the dbGaP study phenotypes by dataset or by variable. Various advanced search options and filters are available. Go directly to a variable, dataset, or study using its dbGaP accession number (phv, pht, or phs).

3. Tag

Tag the dbGaP study variables with controlled vocabularly phenotype concept tags. Review the resulting tagged variables for quality and consistency. 

## Technology overview
PIE is built using:
- Python 3
- Django
- Twitter Bootstrap 3.3.6
- MariaDB

### Python version
PIE is built using Python 3.4. It will probably work with later versions of Python 3 as well, but this has not been tested.

### Django version
PIE is currently using Django 1.11. Modifications are required to get it to run with later versions of Django.

## Documenation

Coming soon...

## Resources
- [Main TOPMed website](https://www.nhlbiwgs.org)


## License
This project is licensed under the terms of the MIT license.
