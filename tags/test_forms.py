"""Test forms for the tags app."""

from django.contrib.auth.models import Group
from django.test import TestCase

from core.factories import UserFactory
from profiles.models import UserData
from trait_browser.factories import SourceTraitFactory, StudyFactory
from trait_browser.models import SourceTrait
from . import forms
from . import factories
from . import models


class TaggedTraitFormTest(TestCase):
    form_class = forms.TaggedTraitForm

    def setUp(self):
        super(TaggedTraitFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(self.trait.source_dataset.source_study_version.study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'trait': self.trait.pk, 'tag': '', 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': ''}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))


class ManyTaggedTraitsFormTest(TestCase):
    form_class = forms.ManyTaggedTraitsForm

    def setUp(self):
        super(ManyTaggedTraitsFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=study)
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
                     'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
                     'tag': '', 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if traits is omitted."""
        form_data = {'traits': [],
                     'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
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
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))


class TaggedTraitByTagFormTest(TestCase):
    form_class = forms.TaggedTraitByTagForm

    def setUp(self):
        super(TaggedTraitByTagFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(self.trait.source_dataset.source_study_version.study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'trait': [str(self.trait.pk)], 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'trait': self.trait.pk, 'recommended': ''}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))


# class TaggedTraitMultipleFromTagFormTest(TestCase):
#     form_class = forms.TaggedTraitMultipleFromTagForm
# 
#     def setUp(self):
#         self.tag = factories.TagFactory.create()
#         self.traits = SourceTraitFactory.create_batch(10)
#         self.user = UserFactory.create()
# 
#     def test_valid(self):
#         """Form is valid with all necessary input."""
#         form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
#                      'recommended': False}
#         form = self.form_class(data=form_data)
#         self.assertTrue(form.is_valid())
# 
#     def test_invalid_missing_trait(self):
#         """Form is invalid if traits is omitted."""
#         form_data = {'traits': [], 'recommended': False}
#         form = self.form_class(data=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertTrue(form.has_error('traits'))
# 
#     def test_valid_missing_recommended(self):
#         """Form is valid if recommended is omitted."""
#         # Because it's a boolean field, required=True has a different meaning.
#         # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
#         # checkbox), you must remember to pass in required=False when creating the BooleanField."
#         # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
#         form_data = {'traits': [str(pk) for pk in SourceTrait.objects.all().values_list('pk', flat=True)],
#                      'recommended': ''}
#         form = self.form_class(data=form_data)
#         self.assertTrue(form.is_valid())
#         self.assertFalse(form.has_error('recommended'))
# 

class TagSpecificTraitFormTest(TestCase):
    form_class = forms.TagSpecificTraitForm

    def setUp(self):
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10)
        self.user = UserFactory.create()

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'tag': '', 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'tag': self.tag.pk, 'recommended': ''}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))
