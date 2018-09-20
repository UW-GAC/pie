"""Customization of the admin interface for the tags app."""

from django.contrib import admin

from . import forms
from . import models


class TagAdmin(admin.ModelAdmin):
    """Admin class for Tag objects."""

    list_display = ('title', 'lower_title', 'description', 'creator', 'created', 'modified', )
    search_fields = ('lower_title', 'description', )
    list_filter = (('creator', admin.RelatedOnlyFieldListFilter), )
    form = forms.TagAdminForm

    def save_model(self, request, obj, form, change):
        """Save current user as the Tag creator."""
        if obj.pk is None:  # Test for whether the tag is being created or edited.
            obj.creator = request.user
        obj.save()


class TaggedTraitAdmin(admin.ModelAdmin):
    """Admin class for TaggedTrait objects."""

    list_display = ('tag', 'trait', 'dcc_review_status', 'creator', 'created', 'modified', )
    list_filter = ('dcc_review__status', ('creator', admin.RelatedOnlyFieldListFilter), 'tag', )
    search_fields = ('tag', 'trait', )
    form = forms.TaggedTraitAdminForm

    def save_model(self, request, obj, form, change):
        """Save current user as the TaggedTrait creator."""
        if obj.pk is None:
            obj.creator = request.user
        obj.save()

    def dcc_review_status(self, obj):
        return obj.dcc_review.get_status_display()

    def has_delete_permission(self, request, obj=None):
        if obj is not None and hasattr(obj, 'dcc_review'):
            return False
        return super().has_delete_permission(request, obj=obj)

    def has_add_permission(self, request, obj=None):
        """No adding TaggedTraits from the admin."""
        return False


class DCCReviewAdmin(admin.ModelAdmin):

    list_display = ('tagged_trait', 'status', 'comment', 'creator', 'created', 'modified', )
    list_filter = ('status', ('creator', admin.RelatedOnlyFieldListFilter), )
    search_fields = ('tagged_trait__tag__title', 'tagged_trait__trait__i_trait_name', )
    readonly_fields = ('tagged_trait', )
    form = forms.DCCReviewAdminForm

    def has_add_permission(self, request, obj=None):
        """No adding DCCReviews from the admin."""
        return False


# Register models for showing them in the admin interface.
admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.TaggedTrait, TaggedTraitAdmin)
admin.site.register(models.DCCReview, DCCReviewAdmin)
