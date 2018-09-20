"""Test forms for the tags app."""

from django.contrib.auth.models import Group
from django.test import TestCase

from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory, StudyFactory

from . import forms
from . import factories
from . import models


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

    def test_invalid_nonunique_lower_title(self):
        """Form is invalid if the title results in a non-unique lower_title."""
        tag = factories.TagFactory.create()
        form_data = {'title': tag.title.upper(), 'description': tag.description,
                     'instructions': tag.instructions}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('title'))


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
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'trait': self.trait.pk, 'tag': ''}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_invalid_trait_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        form_data = {'trait': trait2.pk, 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertIn(self.trait, form.fields['trait'].queryset)
        self.assertNotIn(trait2, form.fields['trait'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertFalse(form.has_error('tag'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user, archived=True)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
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
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
        form = self.form_class(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'trait': self.trait.pk, 'tag': ''}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': '', 'tag': self.tag.pk}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
        form = self.form_class(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertFalse(form.has_error('tag'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, archived=True)
        form_data = {'trait': self.trait.pk, 'tag': self.tag.pk}
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
        form_data = {'trait': self.trait.pk}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_trait(self):
        """Form is invalid if trait is omitted."""
        form_data = {'trait': ''}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_invalid_trait_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        form_data = {'trait': trait2.pk}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertIn(self.trait, form.fields['trait'].queryset)
        self.assertNotIn(trait2, form.fields['trait'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the selected trait is already linked to the selected tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user)
        form_data = {'trait': self.trait.pk}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait, creator=self.user, archived=True)
        form_data = {'trait': self.trait.pk}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('trait'))
        self.assertFalse(form.has_error('tag'))


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
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': ''}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_missing_traits(self):
        """Form is invalid if traits is omitted."""
        form_data = {'traits': [], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))

    def test_invalid_traits_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        form_data = {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        for trait in self.traits:
            self.assertIn(trait, form.fields['traits'].queryset)
        for trait in traits2:
            self.assertNotIn(trait, form.fields['traits'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when a trait in 'traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'traits': [self.traits[0].pk], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user, archived=True)
        form_data = {'traits': [self.traits[0].pk], 'tag': self.tag.pk}
        form = self.form_class(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))


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
        form_data = {'traits': [x.pk for x in self.traits[0:5]], }
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())

    def test_valid_missing_tag(self):
        """Form is valid if tag is omitted."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': ''}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.has_error('tag'))

    def test_invalid_missing_traits(self):
        """Form is invalid if traits is omitted."""
        form_data = {'traits': [], }
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))

    def test_invalid_traits_from_other_study(self):
        """Form is invalid if the selected trait is from a study not in the user's taggable_studies."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        form_data = {'traits': [str(x.pk) for x in traits2], }
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))
        for trait in self.traits:
            self.assertIn(trait, form.fields['traits'].queryset)
        for trait in traits2:
            self.assertNotIn(trait, form.fields['traits'].queryset)

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when a trait in 'traits' is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user)
        form_data = {'traits': [self.traits[0].pk], }
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], creator=self.user, archived=True)
        form_data = {'traits': [self.traits[0].pk]}
        form = self.form_class(data=form_data, user=self.user, tag_pk=self.tag.pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('traits'))


class TagSpecificTraitFormTest(TestCase):
    form_class = forms.TagSpecificTraitForm

    def setUp(self):
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10)
        self.user = UserFactory.create()

    def test_valid(self):
        """Form is valid with all necessary input."""
        form_data = {'tag': self.tag.pk, }
        form = self.form_class(data=form_data, trait_pk=self.traits[0].pk)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form_data = {'tag': '', }
        form = self.form_class(data=form_data, trait_pk=self.traits[0].pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_trait_already_tagged(self):
        """Form is invalid when the trait is already linked to the given tag."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        form_data = {'tag': self.tag.pk}
        form = self.form_class(data=form_data, trait_pk=self.traits[0].pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))

    def test_invalid_taggedtrait_archived(self):
        """Form is invalid when the selected trait and tag are in an archived TaggedTrait."""
        factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0], archived=True)
        form_data = {'tag': self.tag.pk}
        form = self.form_class(data=form_data, trait_pk=self.traits[0].pk)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tag'))


class DCCReviewFormTestMixin(object):

    def test_valid_if_need_review_with_comment(self):
        """Form is valid if the tagged trait needs followup and a comment is given."""
        form_data = {'comment': 'foo', 'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_need_review_with_no_comment(self):
        """Form is invalid if the tagged trait needs followup and no comment is given."""
        form_data = {'comment': '', 'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='followup_comment'))

    def test_invalid_if_need_review_with_whitespace_comment(self):
        """Form is invalid if the tagged trait needs followup and no comment is given."""
        form_data = {'comment': ' ', 'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='followup_comment'))

    def test_valid_if_confirmed_with_no_comment(self):
        """Form is valid if the tagged trait is confirmed and no comment is given."""
        form_data = {'comment': '', 'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_valid_if_confirmed_with_whitespace_comment(self):
        """Form is valid if the tagged trait is confirmed and a whitespace-only comment is given."""
        form_data = {'comment': '  ', 'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_confirmed_with_comment(self):
        """Form is invalid if the tagged trait is confirmed and a comment is given."""
        form_data = {'comment': 'foo', 'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='confirmed_comment'))

    def test_invalid_missing_status(self):
        form_data = {'comment': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('status'))


class DCCReviewByTagAndStudyFormTest(DCCReviewFormTestMixin, TestCase):

    form_class = forms.DCCReviewByTagAndStudyForm

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()


class DCCReviewFormTest(DCCReviewFormTestMixin, TestCase):

    form_class = forms.DCCReviewForm

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()


class DCCReviewAdminFormTest(TestCase):
    form_class = forms.DCCReviewAdminForm

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def test_valid_if_need_review_with_comment(self):
        """Form is valid if the tagged trait needs followup and a comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': 'foo',
                     'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_need_review_with_no_comment(self):
        """Form is invalid if the tagged trait needs followup and no comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': '', 'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='followup_comment'))

    def test_invalid_if_need_review_with_whitespace_comment(self):
        """Form is invalid if the tagged trait needs followup and no comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': ' ',
                     'status': models.DCCReview.STATUS_FOLLOWUP}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='followup_comment'))

    def test_valid_if_confirmed_with_no_comment(self):
        """Form is valid if the tagged trait is confirmed and no comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': '',
                     'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_valid_if_confirmed_with_whitespace_comment(self):
        """Form is valid if the tagged trait is confirmed and a whitespace-only comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': '  ',
                     'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_confirmed_with_comment(self):
        """Form is invalid if the tagged trait is confirmed and a comment is given."""
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': 'foo',
                     'status': models.DCCReview.STATUS_CONFIRMED}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='confirmed_comment'))

    def test_invalid_missing_status(self):
        form_data = {'tagged_trait': self.tagged_trait.pk, 'comment': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('status'))

    def test_invalid_missing_tagged_trait(self):
        form_data = {'status': models.DCCReview.STATUS_CONFIRMED, 'comment': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('tagged_trait'))


class DCCReviewTagAndStudySelectFormTest(TestCase):

    form_class = forms.DCCReviewTagAndStudySelectForm

    def setUp(self):
        super(DCCReviewTagAndStudySelectFormTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )

    def test_valid(self):
        """Form is valid with all necessary input."""
        form = self.form_class({'tag': self.tag.pk, 'study': self.study.pk})
        self.assertTrue(form.is_valid())

    def test_invalid_missing_tag(self):
        """Form is invalid if tag is omitted."""
        form = self.form_class({'tag': '', 'study': self.study.pk})
        self.assertFalse(form.is_valid())

    def test_invalid_missing_trait(self):
        """Form is invalid if study is omitted."""
        form = self.form_class({'tag': self.tag.pk, 'study': ''})
        self.assertFalse(form.is_valid())

    def test_no_tagged_traits(self):
        """Form is invalid if there are no tagged traits matching the selected tag and study."""
        self.tagged_trait.delete()
        form = self.form_class({'tag': self.tag.pk, 'study': self.study.pk})
        self.assertFalse(form.is_valid())

    def test_no_unreviewed_tagged_traits(self):
        """Form is invalid if there are no unreviewed tagged traits matching the selected tag and study."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait)
        form = self.form_class({'tag': self.tag.pk, 'study': self.study.pk})
        self.assertFalse(form.is_valid())

    def test_no_archived_tagged_traits(self):
        """Form is invalid if there are no non-archived tagged traits matching the selected tag and study."""
        self.tagged_trait.archive()
        form = self.form_class({'tag': self.tag.pk, 'study': self.study.pk})
        self.assertFalse(form.is_valid())


class StudyResponseDisagreeFormTest(TestCase):

    form_class = forms.StudyResponseDisagreeForm

    def test_valid(self):
        """Form is valid with all necessary input."""
        form = self.form_class({'comment': 'a comment'})
        self.assertTrue(form.is_valid())

    def test_invalid_missing_comment(self):
        """Form is invalid if missing comment."""
        form = self.form_class({})
        self.assertFalse(form.is_valid())

    def test_invalid_whitespace_comment(self):
        """Form is invalid if comment is only whitespace."""
        form = self.form_class({'comment': ' '})
        self.assertFalse(form.is_valid())


class StudyResponseFormTestMixin(object):

    def test_valid_if_disagree_with_comment(self):
        """Form is valid if the study disagrees and a comment is given."""
        form_data = {'comment': 'foo', 'status': models.StudyResponse.STATUS_DISAGREE}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_disagree_with_no_comment(self):
        """Form is invalid if the study disagrees and no comment is given."""
        form_data = {'comment': '', 'status': models.StudyResponse.STATUS_DISAGREE}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='disagree_comment'))

    def test_invalid_if_disagree_with_whitespace_comment(self):
        """Form is invalid if the study disagrees and no comment is given."""
        form_data = {'comment': ' ', 'status': models.StudyResponse.STATUS_DISAGREE}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='disagree_comment'))

    def test_valid_if_agree_with_no_comment(self):
        """Form is valid if the study agrees and no comment is given."""
        form_data = {'comment': '', 'status': models.StudyResponse.STATUS_AGREE}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_valid_if_agree_with_whitespace_comment(self):
        """Form is valid if the study agrees and a whitespace-only comment is given."""
        form_data = {'comment': '  ', 'status': models.StudyResponse.STATUS_AGREE}
        form = self.form_class(form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_if_agree_with_comment(self):
        """Form is invalid if the study agrees and a comment is given."""
        form_data = {'comment': 'foo', 'status': models.StudyResponse.STATUS_AGREE}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('comment', code='agree_comment'))

    def test_invalid_missing_status(self):
        """Form is invalid if status is missing."""
        form_data = {'comment': ''}
        form = self.form_class(form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('status'))


class StudyResponseAdminFormTest(StudyResponseFormTestMixin, TestCase):

    form_class = forms.StudyResponseAdminForm
