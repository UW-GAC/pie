"""Test forms for the tags app."""

from django.contrib.auth.models import Group
from django.test import TestCase

from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory, StudyFactory
from . import forms
from . import factories


class TagAdminFormTest(TestCase):
    form_class = forms.TagAdminForm

    def setUp(self):
        super(TagAdminFormTest, self).setUp()
        self.unsaved_tag = factories.TagFactory.build()

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'title': self.unsaved_tag.title, 'description': self.unsaved_tag.description,
                     'instructions': self.unsaved_tag.instructions}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_title(self):
        """Form is invalid if title is omitted."""
        form_data = {'title': '', 'description': self.unsaved_tag.description,
                     'instructions': self.unsaved_tag.instructions}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('title'))

    def test_invalid_missing_description(self):
        """Form is invalid if description is omitted."""
        form_data = {'title': self.unsaved_tag.title, 'description': '',
                     'instructions': self.unsaved_tag.instructions}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('description'))

    def test_invalid_missing_instructions(self):
        """Form is invalid if instructions is omitted."""
        form_data = {'title': self.unsaved_tag.title, 'description': self.unsaved_tag.description,
                     'instructions': ''}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('instructions'))


class TaggedTraitFormTest(TestCase):
    form_class = forms.TaggedTraitForm

    def setUp(self):
        super(TaggedTraitFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.trait.source_dataset.source_study_version.study)

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

    def test_invalid_trait_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        form_data = {'trait': trait2.pk, 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertIn(self.trait, form.fields['trait'].queryset)
        self.assertNotIn(trait2, form.fields['trait'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertFalse(form.has_error('tag'))


class TaggedTraitAdminFormTest(TestCase):
    form_class = forms.TaggedTraitAdminForm

    def setUp(self):
        super(TaggedTraitAdminFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()

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

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertFalse(form.has_error('tag'))


class TaggedTraitByTagFormTest(TestCase):
    form_class = forms.TaggedTraitByTagForm

    def setUp(self):
        super(TaggedTraitByTagFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.trait.source_dataset.source_study_version.study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'trait': self.trait.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'recommended': False}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_valid_missing_recommended(self):
        """Form is valid if recommended is omitted."""
        # Because it's a boolean field, required=True has a different meaning.
        # "If you want to include a boolean in your form that can be either True or False (e.g. a checked or unchecked
        # checkbox), you must remember to pass in required=False when creating the BooleanField."
        # See Django docs: https://docs.djangoproject.com/en/1.8/ref/forms/fields/#django.forms.BooleanField
        form_data = {'trait': self.trait.pk, 'recommended': ''}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended'))

    def test_invalid_trait_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        form_data = {'trait': trait2.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertIn(self.trait, form.fields['trait'].queryset)
        self.assertNotIn(trait2, form.fields['trait'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user)
        form_data = {'trait': self.trait.pk, 'recommended': False}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))


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
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [x.pk for x in self.traits[5:]],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [x.pk for x in self.traits[5:]],
                     'tag': ''}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_valid_missing_traits(self):
        """Form is valid if traits is omitted."""
        form_data = {'traits': [], 'recommended_traits': [x.pk for x in self.traits[5:]],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('traits'))

    def test_valid_missing_recommended_traits(self):
        """Form is valid if traits is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended_traits'))

    def test_invalid_missing_recommended_traits_and_traits(self):
        """Form is invalid if trait and recommended_traits are omitted."""
        form_data = {'traits': [], 'recommended_traits': [],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertTrue(form.has_error('recommended_traits'))

    def test_invalid_traits_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        form_data = {'traits': [str(x.pk) for x in traits2], 'recommended_traits': [], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        for trait in self.traits:
            self.assertIn(trait, form.fields['traits'].queryset)
        for trait in traits2:
            self.assertNotIn(trait, form.fields['traits'].queryset)

    def test_invalid_repeated_trait(self):
        """Form is invalid with a trait repeated in the 'traits' and 'recommended_traits' fields."""
        form_data = {'traits': [self.traits[0].pk], 'recommended_traits': [self.traits[0].pk],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertTrue(form.has_error('recommended_traits'))

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when a trait in 'traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'traits': [self.traits[0].pk], 'recommended_traits': [],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertFalse(form.has_error('recommended_traits'))

    def test_invalid_recommended_trait_already_tagged(self):
        """Form is invalid when a trait in 'recommended_traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'recommended_traits': [self.traits[0].pk], 'traits': [],
                     'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('recommended_traits'))
        self.assertFalse(form.has_error('traits'))


class ManyTaggedTraitsByTagFormTest(TestCase):
    form_class = forms.ManyTaggedTraitsByTagForm

    def setUp(self):
        super(ManyTaggedTraitsByTagFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=study)
        self.user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.add(phenotype_taggers)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(study)

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [x.pk for x in self.traits[5:]]}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())

    def test_valid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [x.pk for x in self.traits[5:]],
                     'tag': ''}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('tag'))

    def test_valid_missing_traits(self):
        """Form is valid if traits is omitted."""
        form_data = {'traits': [], 'recommended_traits': [x.pk for x in self.traits[5:]]}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('traits'))

    def test_valid_missing_recommended_traits(self):
        """Form is valid if traits is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': []}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('recommended_traits'))

    def test_invalid_missing_recommended_traits_and_traits(self):
        """Form is invalid if trait and recommended_traits are omitted."""
        form_data = {'traits': [], 'recommended_traits': []}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertTrue(form.has_error('recommended_traits'))

    def test_invalid_traits_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        form_data = {'traits': [str(x.pk) for x in traits2], 'recommended_traits': []}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        for trait in self.traits:
            self.assertIn(trait, form.fields['traits'].queryset)
        for trait in traits2:
            self.assertNotIn(trait, form.fields['traits'].queryset)

    def test_invalid_repeated_trait(self):
        """Form is invalid with a trait repeated in the 'traits' and 'recommended_traits' fields."""
        form_data = {'traits': [self.traits[0].pk], 'recommended_traits': [self.traits[0].pk]}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertTrue(form.has_error('recommended_traits'))

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when a trait in 'traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'traits': [self.traits[0].pk], 'recommended_traits': []}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        self.assertFalse(form.has_error('recommended_traits'))

    def test_invalid_recommended_trait_already_tagged(self):
        """Form is invalid when a trait in 'recommended_traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'recommended_traits': [self.traits[0].pk], 'traits': []}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('recommended_traits'))
        self.assertFalse(form.has_error('traits'))


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
