"""View functions and classes for the tags app."""

from django.db.models import Count
from django.views.generic import DetailView, CreateView, UpdateView

from braces.views import LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin, GroupRequiredMixin

# from . import forms
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
