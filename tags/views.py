"""View functions and classes for the tags app."""

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from braces.views import LoginRequiredMixin, UserFormKwargsMixin, FormMessagesMixin

from . import forms
from . import models


TAGGING_ERROR_MESSAGE = 'Oops! Tagging a phenotype was not successful.'
TAGGING_MULTIPLE_ERROR_MESSAGE = 'Oops! Tagging phenotypes was not successful.'


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
    form_invalid_message = TAGGING_ERROR_MESSAGE

    def form_valid(self, form):
        """Custom processing for valid forms.

        Sets current user as the TaggedTrait's creator.
        """
        form.instance.creator = self.request.user
        return super(TaggedTraitCreate, self).form_valid(form)

    def get_success_url(self):
        return self.object.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = 'Phenotype <a href="{}">{}</a> tagged as {}'.format(
            self.object.trait.get_absolute_url(), self.object.trait.i_trait_name, self.object.tag.title)
        return mark_safe(msg)


class TaggedTraitMultipleFormCreate(LoginRequiredMixin, FormMessagesMixin, FormView):
    """Form view class for tagging multiple traits with one tag."""

    form_class = forms.TaggedTraitMultipleForm
    form_invalid_message = TAGGING_MULTIPLE_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'

    def form_valid(self, form):
        """Create a TaggedTrait object for each trait given."""
        for trait in form.cleaned_data['traits']:
            tagged_trait = models.TaggedTrait(
                tag=form.cleaned_data['tag'], trait=trait, creator=self.request.user,
                recommended=form.cleaned_data['recommended'])
            tagged_trait.full_clean()
            tagged_trait.save()
        # Save the tag object so that you can use it in get_success_url.
        self.tag = form.cleaned_data['tag']
        # Save the traits so you can use them in the form valid message.
        self.traits = form.cleaned_data['traits']
        return super(TaggedTraitMultipleFormCreate, self).form_valid(form)

    def get_success_url(self):
        return self.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = ''
        for trait in self.traits:
            msg += '<p>Phenotype <a href="{}">{}</a> tagged as {}<\p>'.format(
                trait.get_absolute_url(), trait.i_trait_name, self.tag.title)
        return mark_safe(msg)


class CreateTaggedTraitFromTagPk(LoginRequiredMixin, FormMessagesMixin, FormView):
    """Form view class for tagging multiple traits with a specific tag."""

    form_class = forms.TaggedTraitMultipleFromTagForm
    form_invalid_message = TAGGING_MULTIPLE_ERROR_MESSAGE
    template_name = 'tags/taggedtrait_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(models.Tag, pk=kwargs.get('pk'))
        return super(CreateTaggedTraitFromTagPk, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateTaggedTraitFromTagPk, self).get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

    def form_valid(self, form):
        """Create a TaggedTrait object for each trait given."""
        for trait in form.cleaned_data['traits']:
            tagged_trait = models.TaggedTrait(
                tag=self.tag, trait=trait, creator=self.request.user,
                recommended=form.cleaned_data['recommended'])
            tagged_trait.full_clean()
            tagged_trait.save()
        # Save the traits so you can use them in the form valid message.
        self.traits = form.cleaned_data['traits']
        return super(CreateTaggedTraitFromTagPk, self).form_valid(form)

    def get_success_url(self):
        return self.tag.get_absolute_url()

    def get_form_valid_message(self):
        msg = ''
        for trait in self.traits:
            msg += '<p>Phenotype <a href="{}">{}</a> tagged as {}<\p>'.format(
                trait.get_absolute_url(), trait.i_trait_name, self.tag.title)
        return mark_safe(msg)
