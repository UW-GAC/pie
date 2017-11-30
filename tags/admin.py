"""Customization of the admin interface for the tags app."""

from django.contrib import admin

from . import models


class TagAdmin(admin.ModelAdmin):
    """Admin class for Tag objects."""

    list_display = ('lower_title', 'creator', 'created', 'modified', )
    list_filter = ('creator', )
    search_fields = ('lower_title', 'description', )

    def save_model(self, request, obj, form, change):
        """Save current user as the Tag creator."""
        if obj.pk is None:
            obj.creator = request.user
        obj.last_modifier = request.user
        obj.save()


class TaggedTraitAdmin(admin.ModelAdmin):
    """Admin class for TaggedTrait objects."""

    list_display = ('tag', 'trait', 'recommended', 'creator', 'created', 'modified', )
    list_filter = ('tag', 'creator', 'recommended', )
    search_fields = ('tag', 'trait', )

    def save_model(self, request, obj, form, change):
        """Save current user as the TaggedTrait creator."""
        if obj.pk is None:
            obj.creator = request.user
        obj.last_modifier = request.user
        obj.save()


# Register models for showing them in the admin interface.
admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.TaggedTrait, TaggedTraitAdmin)
