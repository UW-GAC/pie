"""View functions and classes for the tags app."""

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, CreateView, UpdateView

from braces.views import LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin

from . import forms
from . import models


class TagDetail(LoginRequiredMixin, DetailView):
    """Detail view class for Tag."""

    model = models.Tag
    context_object_name = 'tag'
    template_name = 'tags/tag_detail.html'

    def get_context_data(self, **kwargs):
        context = super(TagDetail, self).get_context_data(**kwargs)
        # context['trait_counts_by_study'] = self.object.traits.annotate(n=Count('source_dataset__global_study'))
        return context


class TaggedTraitCreate(LoginRequiredMixin, FormMessagesMixin, CreateView):
    """Create view class for TaggedTrait objects."""

    model = models.TaggedTrait
    form_class = forms.TaggedTraitForm
    form_invalid_message = 'Oops! Tagging a phenotype was not successful.'

    def form_valid(self, form):
        """Custom processing for valid forms.

        Sets current user as the TaggedTrait's creator.
        """
        form.instance.creator = self.request.user
        return super(TaggedTraitCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('tags:detail', args=[self.object.tag.pk])

    def get_form_valid_message(self):
        msg = 'Phenotype <a href="{}">{}</a> tagged as {}'.format(
            self.object.trait.get_absolute_url(), self.object.trait.i_trait_name, self.object.tag.title)
        return mark_safe(msg)
