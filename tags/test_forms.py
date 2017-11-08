"""Test forms for the tags app."""

from django.test import TestCase

from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory
from trait_browser.models import SourceTrait
from . import forms
from . import factories
from . import models


class TaggedTraitFormTest(TestCase):
    form_class = forms.TaggedTraitForm

    def setUp(self):
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.user = UserFactory.create()

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'trait': self.trait.pk, 'tag': '', 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': ''}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))


class TaggedTraitMultipleFormTest(TestCase):
    form_class = forms.TaggedTraitMultipleForm

    def setUp(self):
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10)
        self.user = UserFactory.create()

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
                     'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
                     'tag': '', 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if traits is omitted."""
        form_data = {'traits': [],
                     'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
                     'tag': self.tag.pk, 'recommended': ''}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))
