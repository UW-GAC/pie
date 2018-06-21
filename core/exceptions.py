"""Custom exceptions used in the phenotype_inventory project."""


class DeleteNotAllowedError(Exception):
    """Raised when attempting to delete an object that should not be deleted."""

    pass
