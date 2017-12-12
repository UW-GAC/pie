"""Customization of the admin interface for the profiles app."""

from django.contrib import admin

from . import models


class ProfileAdmin(admin.ModelAdmin):
    """Admin class for Profile objects."""

    list_display = ('user', )
    list_filter = ('user', )
    readonly_fields = ('user', )


# Register models for showing them in the admin interface.
admin.site.register(models.Profile, ProfileAdmin)
