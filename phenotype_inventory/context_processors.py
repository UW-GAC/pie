"""Context processors used across the phenotype_inventory project."""

from django.contrib.sites.models import Site


def site(request):
    """Adds the site variable to all template contexts.

    Source:
        http://stackoverflow.com/questions/7466684/is-the-current-site-accessible-from-a-template
    """
    return {'site': Site.objects.get_current()}
