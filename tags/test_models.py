"""Tests of models for the tags app."""

from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query import QuerySet
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.exceptions import DeleteNotAllowedError
from core.factories import UserFactory
from core.utils import SuperuserLoginTestCase
# from core.utils import UserLoginTestCase
from trait_browser.factories import SourceStudyVersionFactory, SourceTraitFactory, StudyFactory
from trait_browser.models import SourceTrait

from . import factories
from . import models


class TagTest(TestCase):
    model = models.Tag
    model_factory = factories.TagFactory

    def setUp(self):
        self.user = UserFactory.create()
        self.model_args = {'title': 'hdl', 'description': 'high density lipoprotein cholesterol',
                           'instructions': 'fill this out carefully', 'creator': self.user}

    def test_model_saving(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_factory(self):
        """Creation using the model factory."""
        instance = self.model_factory.create()
        self.assertIsInstance(self.model_factory._meta.model.objects.get(pk=instance.pk),
                              self.model_factory._meta.model)

    def test_printing(self):
        """The custom __str__ method returns a string."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance.__str__(), str)

    def test_unique_lower_title(self):
        """Saving a new object with a non-unique lower_title fails."""
        instance = self.model(**self.model_args)
        instance.save()
        model_args2 = self.model_args.copy()
        model_args2['title'] = self.model_args['title'].upper()
        instance2 = self.model(**model_args2)
        with self.assertRaises(IntegrityError):
            instance2.save()

    def test_lower_title_updates(self):
        """Changing the title of an existing Tag object correctly updates lower_title."""
        instance = self.model(**self.model_args)
        instance.save()
        new_title = 'koo6mooYa2ga'
        self.assertNotEqual(new_title, instance.title)
        instance.title = new_title
        instance.save()
        self.assertEqual(instance.title, new_title)
        self.assertEqual(instance.lower_title, new_title.lower())

    def test_trailing_spaces_in_title(self):
        """Trailing spaces in the title aren't counted for uniqueness of lower_title."""
        instance = self.model(**self.model_args)
        instance.save()
        model_args2 = self.model_args.copy()
        model_args2['title'] = self.model_args['title'] + '  '
        instance2 = self.model(**model_args2)
        with self.assertRaises(IntegrityError):
            instance2.save()

    def test_leading_spaces_in_title(self):
        """Leading spaces in the title aren't counted for uniqueness of lower_title."""
        instance = self.model(**self.model_args)
        instance.save()
        model_args2 = self.model_args.copy()
        model_args2['title'] = '  ' + self.model_args['title']
        instance2 = self.model(**model_args2)
        with self.assertRaises(IntegrityError):
            instance2.save()

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = self.model_factory.create()
        url = instance.get_absolute_url()
        # Just test that this function works.

    def test_add_m2m_adds_traits(self):
        """Creating the M2M TaggedTrait object adds a trait to tag.traits manager."""
        trait = SourceTraitFactory.create()
        tag = factories.TagFactory.create()
        tagged_trait = models.TaggedTrait(trait=trait, tag=tag, creator=self.user)
        tagged_trait.save()
        self.assertIn(trait, tag.all_traits.all())

    def test_archived_traits_and_non_archived_traits(self):
        """Archived traits and non archived traits linked to the tag are where they should be."""
        tag = factories.TagFactory.create()
        archived = factories.TaggedTraitFactory.create(archived=True, tag=tag)
        non_archived = factories.TaggedTraitFactory.create(archived=False, tag=tag)
        self.assertIn(archived.trait, tag.all_traits.all())
        self.assertIn(non_archived.trait, tag.all_traits.all())
        self.assertIn(archived.trait, tag.archived_traits)
        self.assertIn(non_archived.trait, tag.non_archived_traits)
        self.assertNotIn(archived.trait, tag.non_archived_traits)
        self.assertNotIn(non_archived.trait, tag.archived_traits)

    def test_archived_traits_and_non_archived_traits_are_querysets(self):
        """The properties archived_traits and non_archived_traits are QuerySets."""
        # These need to be querysets to behave similarly to tag.traits and trait.tag_set.
        tag = factories.TagFactory.create()
        archived = factories.TaggedTraitFactory.create(archived=True, tag=tag)
        non_archived = factories.TaggedTraitFactory.create(archived=False, tag=tag)
        self.assertIsInstance(tag.archived_traits, QuerySet)
        self.assertIsInstance(tag.non_archived_traits, QuerySet)

    def test_multiple_archived_traits(self):
        """Archived tagged traits show up in the archived_trait property with multiple tagged traits of each type."""
        tag = factories.TagFactory.create()
        archived = factories.TaggedTraitFactory.create_batch(5, archived=True, tag=tag)
        non_archived = factories.TaggedTraitFactory.create_batch(6, archived=False, tag=tag)
        for tagged_trait in archived:
            self.assertIn(tagged_trait.trait, tag.all_traits.all())
            self.assertIn(tagged_trait.trait, tag.archived_traits)
            self.assertNotIn(tagged_trait.trait, tag.non_archived_traits)
        self.assertEqual(len(archived), tag.archived_traits.count())

    def test_multiple_non_archived_traits(self):
        """Non-archived tagged traits show up in the non_archived_trait property with multiple of each type."""
        tag = factories.TagFactory.create()
        archived = factories.TaggedTraitFactory.create_batch(5, archived=True, tag=tag)
        non_archived = factories.TaggedTraitFactory.create_batch(6, archived=False, tag=tag)
        for tagged_trait in non_archived:
            self.assertIn(tagged_trait.trait, tag.all_traits.all())
            self.assertIn(tagged_trait.trait, tag.non_archived_traits)
            self.assertNotIn(tagged_trait.trait, tag.archived_traits)
        self.assertEqual(len(non_archived), tag.non_archived_traits.count())

    def test_traits(self):
        """Test the method to get all of the tag's linked traits."""
        tag = factories.TagFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(10, tag=tag)
        self.assertListEqual(list(SourceTrait.objects.all()), list(tag.all_traits.all()))

    def test_cannot_delete_user_who_created_tag(self):
        """Unable to delete a user who has created a tag."""
        tag = factories.TagFactory.create()
        with self.assertRaises(ProtectedError):
            tag.creator.delete()


class StudyGetAllTaggedTraitsTest(TestCase):

    def setUp(self):
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study)

    def test_get_all_tagged_traits(self):
        """Returns the correct set of tagged traits for a study."""
        self.assertEqual(list(self.study.get_all_tagged_traits()), self.tagged_traits)

    def test_get_all_tagged_traits_empty(self):
        """Returns an empty queryset when a study has no tagged traits."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(list(self.study.get_all_tagged_traits()), [])

    def test_get_all_tagged_traits_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(list(self.study.get_all_tagged_traits()), self.tagged_traits)
        self.assertEqual(list(another_study.get_all_tagged_traits()), more_tagged_traits)

    def test_get_all_tagged_traits_deprecated(self):
        """Does not return a tagged trait does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(list(self.study.get_all_tagged_traits()), self.tagged_traits)

    def test_get_all_traits_tagged_count(self):
        """Returns the correct number of tagged traits for a study."""
        self.assertEqual(self.study.get_all_traits_tagged_count(), len(self.tagged_traits))

    def test_get_all_traits_tagged_count_empty(self):
        """Returns 0 when a study has no tagged traits."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(self.study.get_all_traits_tagged_count(), 0)

    def test_get_all_traits_tagged_count_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(self.study.get_all_traits_tagged_count(), len(self.tagged_traits))
        self.assertEqual(another_study.get_all_traits_tagged_count(), len(more_tagged_traits))

    def test_get_all_traits_tagged_count_multiple_tags_per_trait(self):
        """Returns the correct number of tagged traits for a study when a trait has multiple tags."""
        trait = self.tagged_traits[0].trait
        unused_tags = models.Tag.objects.exclude(pk=self.tagged_traits[0].tag.pk)
        tag1 = unused_tags[0]
        tag2 = unused_tags[1]
        factories.TaggedTraitFactory.create(tag=tag1, trait=trait)
        factories.TaggedTraitFactory.create(tag=tag2, trait=trait)
        self.assertEqual(self.study.get_all_traits_tagged_count(), SourceTrait.objects.count())

    def test_get_all_traits_tagged_count_deprecated(self):
        """Does not return a tagged trait does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_all_traits_tagged_count(), len(self.tagged_traits))

    def test_get_all_tags_count(self):
        """Returns the correct number of tags for a study."""
        self.assertEqual(self.study.get_all_tags_count(), models.Tag.objects.all().count())

    def test_get_all_tags_count_none(self):
        """Returns the correct number of tags for a study when there are none."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(self.study.get_all_tags_count(), 0)

    def test_get_all_tags_count_no_tags(self):
        """Returns the correct number of tags for a study when there are none."""
        models.TaggedTrait.objects.all().delete()
        models.Tag.objects.all().delete()
        self.assertEqual(self.study.get_all_tags_count(), 0)

    def test_get_all_tags_count_two_studies(self):
        """Returns the correct number of tags for a study."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(self.study.get_all_tags_count(), len(self.tagged_traits))
        self.assertEqual(another_study.get_all_tags_count(), len(more_tagged_traits))

    def test_get_all_tags_count_deprecated(self):
        """Does not return a tagged trait does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_all_tags_count(), len(self.tagged_traits))

    def test_get_all_tags_count_deprecated_two_studies(self):
        """Does not return a tag for a deprecated tagged traits with another study."""
        new_tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True,
            tag=new_tag
        )
        other_tagged_trait = factories.TaggedTraitFactory.create(tag=new_tag)
        self.assertEqual(self.study.get_all_tags_count(), len(self.tagged_traits))


class StudyGetArchivedTaggedTraitsTest(TestCase):

    def setUp(self):
        self.study = StudyFactory.create()
        self.archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            5, trait__source_dataset__source_study_version__study=self.study, archived=True)
        self.non_archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            4, trait__source_dataset__source_study_version__study=self.study, archived=False)

    def test_get_archived_tagged_traits(self):
        """Returns the correct set of tagged traits for a study."""
        self.assertEqual(list(self.study.get_archived_tagged_traits()), self.archived_tagged_traits)

    def test_get_archived_tagged_traits_empty(self):
        """Returns an empty queryset when a study has no tagged traits."""
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(list(self.study.get_archived_tagged_traits()), [])

    def test_get_archived_tagged_traits_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(list(self.study.get_archived_tagged_traits()), self.archived_tagged_traits)

    def test_get_archived_tagged_traits_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            archived=True,
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(list(self.study.get_archived_tagged_traits()), self.archived_tagged_traits)

    def test_get_archived_traits_tagged_count(self):
        """Returns the correct number of tagged traits for a study."""
        self.assertEqual(self.study.get_archived_traits_tagged_count(), len(self.archived_tagged_traits))

    def test_get_archived_traits_tagged_count_empty(self):
        """Returns 0 when a study has no archived tagged traits."""
        models.TaggedTrait.objects.archived().hard_delete()
        self.assertEqual(self.study.get_archived_traits_tagged_count(), 0)

    def test_get_archived_traits_tagged_count_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(self.study.get_archived_traits_tagged_count(), len(self.archived_tagged_traits))

    def test_get_archived_traits_tagged_count_multiple_tags_per_trait(self):
        """Returns the correct number of tagged traits for a study when a trait has multiple tags."""
        models.TaggedTrait.objects.all().hard_delete()
        trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        tags = factories.TagFactory.create_batch(2)
        factories.TaggedTraitFactory.create(tag=tags[0], trait=trait, archived=True)
        factories.TaggedTraitFactory.create(tag=tags[1], trait=trait, archived=True)
        self.assertEqual(self.study.get_archived_traits_tagged_count(), 1)

    def test_get_archived_traits_tagged_count_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            archived=True,
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_archived_traits_tagged_count(), len(self.archived_tagged_traits))

    def test_get_archived_tags_count(self):
        """Returns the correct number of tags for a study."""
        self.assertEqual(self.study.get_archived_tags_count(), len(self.archived_tagged_traits))

    def test_get_archived_tags_count_none(self):
        """Returns the correct number of archived tags for a study when there are none."""
        models.TaggedTrait.objects.archived().hard_delete()
        self.assertEqual(self.study.get_archived_tags_count(), 0)

    def test_get_archived_tags_count_no_tags(self):
        """Returns the correct number of archived tags for a study when there are none."""
        models.TaggedTrait.objects.archived().hard_delete()
        self.assertEqual(self.study.get_archived_tags_count(), 0)

    def test_get_archived_tags_count_two_studies(self):
        """Returns the correct number of tags for a study."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            6, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(self.study.get_archived_tags_count(), len(self.archived_tagged_traits))

    def test_get_archived_tags_count_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            archived=True,
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_archived_tags_count(), len(self.archived_tagged_traits))

    def test_get_archived_tags_count_deprecated_two_studies(self):
        """Does not include deprecated tagged traits with another study."""
        new_tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            archived=True,
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True,
            tag=new_tag
        )
        other_tagged_trait = factories.TaggedTraitFactory.create(tag=new_tag, archived=True)
        self.assertEqual(self.study.get_archived_tags_count(), len(self.archived_tagged_traits))


class StudyGetNonArchivedTaggedTraitsTest(TestCase):

    def setUp(self):
        self.study = StudyFactory.create()
        self.archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            5, trait__source_dataset__source_study_version__study=self.study, archived=True)
        self.non_archived_tagged_traits = factories.TaggedTraitFactory.create_batch(
            4, trait__source_dataset__source_study_version__study=self.study, archived=False)

    def test_get_non_archived_tagged_traits(self):
        """Returns the correct set of tagged traits for a study."""
        self.assertEqual(list(self.study.get_non_archived_tagged_traits()), self.non_archived_tagged_traits)

    def test_get_non_archived_tagged_traits_empty(self):
        """Returns an empty queryset when a study has no tagged traits."""
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(list(self.study.get_non_archived_tagged_traits()), [])

    def test_get_non_archived_tagged_traits_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(list(self.study.get_non_archived_tagged_traits()), self.non_archived_tagged_traits)

    def test_get_non_archived_tagged_traits_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(list(self.study.get_non_archived_tagged_traits()), self.non_archived_tagged_traits)

    def test_get_non_archived_traits_tagged_count(self):
        """Returns the correct number of tagged traits for a study."""
        self.assertEqual(self.study.get_non_archived_traits_tagged_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_traits_tagged_count_empty(self):
        """Returns 0 when a study has no archived tagged traits."""
        models.TaggedTrait.objects.non_archived().hard_delete()
        self.assertEqual(self.study.get_non_archived_traits_tagged_count(), 0)

    def test_get_non_archived_traits_tagged_count_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(self.study.get_non_archived_traits_tagged_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_traits_tagged_count_multiple_tags_per_trait(self):
        """Returns the correct number of tagged traits for a study when a trait has multiple tags."""
        models.TaggedTrait.objects.all().hard_delete()
        trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        tags = factories.TagFactory.create_batch(2)
        factories.TaggedTraitFactory.create(tag=tags[0], trait=trait, archived=False)
        factories.TaggedTraitFactory.create(tag=tags[1], trait=trait, archived=False)
        self.assertEqual(self.study.get_non_archived_traits_tagged_count(), 1)

    def test_get_non_archived_traits_tagged_count_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_non_archived_traits_tagged_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_tags_count(self):
        """Returns the correct number of tags for a study."""
        self.assertEqual(self.study.get_non_archived_tags_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_tags_count_none(self):
        """Returns the correct number of archived tags for a study when there are none."""
        models.TaggedTrait.objects.non_archived().hard_delete()
        self.assertEqual(self.study.get_non_archived_tags_count(), 0)

    def test_get_non_archived_tags_count_no_tags(self):
        """Returns the correct number of archived tags for a study when there are none."""
        models.TaggedTrait.objects.non_archived().hard_delete()
        self.assertEqual(self.study.get_non_archived_tags_count(), 0)

    def test_get_non_archived_tags_count_two_studies(self):
        """Returns the correct number of tags for a study."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            6, trait__source_dataset__source_study_version__study=another_study, archived=True)
        self.assertEqual(self.study.get_non_archived_tags_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_tags_count_deprecated(self):
        """Does not include deprecated tagged traits."""
        deprecated_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True
        )
        self.assertEqual(self.study.get_non_archived_tags_count(), len(self.non_archived_tagged_traits))

    def test_get_non_archived_tags_count_deprecated_two_studies(self):
        """Does not include deprecated tagged traits with another study."""
        new_tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            trait__source_dataset__source_study_version__i_is_deprecated=True,
            tag=new_tag
        )
        other_tagged_trait = factories.TaggedTraitFactory.create(tag=new_tag, archived=True)
        self.assertEqual(self.study.get_non_archived_tags_count(), len(self.non_archived_tagged_traits))


class SourceStudyVersionApplyPreviousTagsTest(SuperuserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study = StudyFactory.create()
        now = timezone.now()
        self.deprecated_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_is_deprecated=True, i_date_added=now - timedelta(hours=2))
        self.updated_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_version=self.deprecated_study_version.i_version + 1,
            i_date_added=now - timedelta(hours=1))
        # Convert the querysets to lists to ensure that they are evaluated now.
        self.deprecated_source_traits = list(SourceTraitFactory.create_batch(
            5, source_dataset__source_study_version=self.deprecated_study_version))
        for deprecated_trait in self.deprecated_source_traits:
            SourceTraitFactory.create(
                source_dataset__source_study_version=self.updated_study_version,
                i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession
            )
        self.updated_source_traits = list(SourceTrait.objects.filter(
            source_dataset__source_study_version=self.updated_study_version
        ))

    def test_no_previous_version(self):
        """Does not fail if there are no previous versions of this study."""
        self.deprecated_study_version.delete()
        self.updated_study_version.apply_previous_tags(self.user)
        for trait in self.updated_source_traits:
            self.assertEqual(trait.all_tags.count(), 0)

    def test_no_tags_in_previous_version(self):
        """Does not apply any tags if there are no tagged traits in the immediately previous version of this study."""
        self.updated_study_version.apply_previous_tags(self.user)
        for trait in self.updated_source_traits:
            self.assertEqual(trait.all_tags.count(), 0)

    def test_one_trait_with_one_tag(self):
        """Successfully applies one tag to one trait using the previous version of this study."""
        tag = factories.TagFactory.create()
        deprecated_trait = self.deprecated_source_traits[0]
        factories.TaggedTraitFactory.create(tag=tag, trait=deprecated_trait)
        self.updated_study_version.apply_previous_tags(self.user)
        updated_trait = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession)
        self.assertEqual(updated_trait.all_tags.count(), 1)
        self.assertEqual(updated_trait.all_tags.first(), tag)

    def test_one_trait_with_two_tags(self):
        """Successfully applies two tags to one trait using the previous version of this study."""
        deprecated_trait = self.deprecated_source_traits[0]
        deprecated_tagged_traits = factories.TaggedTraitFactory.create_batch(2, trait=deprecated_trait)
        tag_pks = sorted([x.tag.pk for x in deprecated_tagged_traits])
        self.updated_study_version.apply_previous_tags(self.user)
        updated_trait = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession)
        self.assertEqual(updated_trait.all_tags.count(), 2)
        self.assertEqual(sorted([x.pk for x in updated_trait.all_tags.all()]), tag_pks)

    def test_two_traits_with_tags(self):
        """Successfully applies tags to multiple traits using the previous version of this study."""
        deprecated_trait_1 = self.deprecated_source_traits[0]
        deprecated_tagged_traits_1 = factories.TaggedTraitFactory.create_batch(2, trait=deprecated_trait_1)
        deprecated_trait_2 = self.deprecated_source_traits[3]
        deprecated_tagged_trait_2 = factories.TaggedTraitFactory.create(trait=deprecated_trait_2)
        self.updated_study_version.apply_previous_tags(self.user)
        tag_pks_1 = sorted([x.tag.pk for x in deprecated_tagged_traits_1])
        # Check the first trait with tags.
        updated_trait_1 = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait_1.i_dbgap_variable_accession)
        self.assertEqual(updated_trait_1.all_tags.count(), 2)
        self.assertEqual(sorted([x.pk for x in updated_trait_1.all_tags.all()]), tag_pks_1)
        # Check the second trait with tags.
        updated_trait_2 = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait_2.i_dbgap_variable_accession)
        self.assertEqual(updated_trait_2.all_tags.count(), 1)
        self.assertEqual(updated_trait_2.all_tags.all()[0], deprecated_tagged_trait_2.tag)

    def test_ignores_newer_version(self):
        """Ignores tags in a newer version of this study."""
        tag = factories.TagFactory.create()
        updated_trait = self.updated_source_traits[0]
        factories.TaggedTraitFactory.create(tag=tag, trait=updated_trait)
        self.deprecated_study_version.apply_previous_tags(self.user)
        deprecated_trait = SourceTrait.objects.get(
            source_dataset__source_study_version=self.deprecated_study_version,
            i_dbgap_variable_accession=updated_trait.i_dbgap_variable_accession)
        self.assertEqual(deprecated_trait.all_tags.count(), 0)

    def test_ignores_older_version(self):
        """Ignores tags in older versions of this study."""
        deprecated_trait = self.deprecated_source_traits[0]
        new_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_is_deprecated=False, i_date_added=timezone.now(),
            i_version=self.updated_study_version.i_version + 1)
        new_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=new_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession)
        factories.TaggedTraitFactory.create(trait=deprecated_trait)
        new_study_version.apply_previous_tags(self.user)
        new_trait.refresh_from_db()
        self.assertEqual(new_trait.all_tags.count(), 0)

    def test_no_previous_trait(self):
        """Does not fail if a new trait has been added in this version of a study."""
        new_trait = SourceTraitFactory.create(source_dataset__source_study_version=self.updated_study_version)
        self.updated_study_version.apply_previous_tags(self.user)
        new_trait.refresh_from_db()
        self.assertEqual(new_trait.all_tags.count(), 0)

    def test_ignores_archived_tagged_traits(self):
        """Ignores archived tagged traits in a previous version."""
        deprecated_trait = self.deprecated_source_traits[0]
        factories.TaggedTraitFactory.create(trait=deprecated_trait, archived=True)
        self.updated_study_version.apply_previous_tags(self.user)
        updated_trait = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession)
        self.assertEqual(updated_trait.all_tags.count(), 0)

    def test_works_if_study_version_is_deprecated(self):
        """Successfully applies tags even if the study version is deprecated."""
        tag = factories.TagFactory.create()
        deprecated_trait = self.deprecated_source_traits[0]
        factories.TaggedTraitFactory.create(tag=tag, trait=deprecated_trait)
        self.updated_study_version.i_is_deprecated = True
        self.updated_study_version.save()
        self.updated_study_version.apply_previous_tags(self.user)
        updated_trait = SourceTrait.objects.get(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=deprecated_trait.i_dbgap_variable_accession)
        self.assertEqual(updated_trait.all_tags.count(), 1)
        self.assertEqual(updated_trait.all_tags.first(), tag)


class SourceTraitApplyPreviousTagsTest(SuperuserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.study = StudyFactory.create()
        now = timezone.now()
        self.deprecated_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_is_deprecated=True, i_date_added=now - timedelta(hours=2))
        self.updated_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_version=self.deprecated_study_version.i_version + 1,
            i_date_added=now - timedelta(hours=1))
        self.deprecated_source_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=self.deprecated_study_version)
        self.updated_source_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=self.updated_study_version,
            i_dbgap_variable_accession=self.deprecated_source_trait.i_dbgap_variable_accession
        )

    def test_no_previous_tags(self):
        """Successfully applies no tags if none exist."""
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 0)

    def test_one_previous_tag(self):
        """Successfully applies one previous tag."""
        tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(tag=tag, trait=self.deprecated_source_trait)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 1)
        updated_tagged_trait = self.updated_source_trait.all_taggedtraits.first()
        self.assertEqual(updated_tagged_trait.tag, deprecated_tagged_trait.tag)
        self.assertEqual(updated_tagged_trait.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait.archived)
        self.assertEqual(updated_tagged_trait.creator, self.user)
        self.assertEqual(updated_tagged_trait.previous_tagged_trait, deprecated_tagged_trait)
        self.assertTrue(hasattr(updated_tagged_trait, 'dcc_review'))
        self.assertEqual(updated_tagged_trait.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait.dcc_review.creator, self.user)

    def test_two_previous_tags(self):
        """Successfully applies two previous tags."""
        tag_1 = factories.TagFactory.create()
        tag_2 = factories.TagFactory.create()
        deprecated_tagged_trait_1 = factories.TaggedTraitFactory.create(tag=tag_1, trait=self.deprecated_source_trait)
        deprecated_tagged_trait_2 = factories.TaggedTraitFactory.create(tag=tag_2, trait=self.deprecated_source_trait)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 2)
        self.assertEqual(sorted(self.updated_source_trait.all_taggedtraits.all().values_list('tag__pk', flat=True)),
                         sorted([tag_1.pk, tag_2.pk]))
        # Check the first tagged trait.
        updated_tagged_trait_1 = self.updated_source_trait.all_taggedtraits.get(tag=tag_1)
        self.assertEqual(updated_tagged_trait_1.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait_1.archived)
        self.assertEqual(updated_tagged_trait_1.creator, self.user)
        self.assertEqual(updated_tagged_trait_1.previous_tagged_trait, deprecated_tagged_trait_1)
        self.assertTrue(hasattr(updated_tagged_trait_1, 'dcc_review'))
        self.assertEqual(updated_tagged_trait_1.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait_1.dcc_review.creator, self.user)
        # Check the second trait.
        updated_tagged_trait_2 = self.updated_source_trait.all_taggedtraits.get(tag=tag_2)
        self.assertEqual(updated_tagged_trait_2.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait_2.archived)
        self.assertEqual(updated_tagged_trait_2.creator, self.user)
        self.assertEqual(updated_tagged_trait_2.previous_tagged_trait, deprecated_tagged_trait_2)
        self.assertTrue(hasattr(updated_tagged_trait_2, 'dcc_review'))
        self.assertEqual(updated_tagged_trait_2.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait_2.dcc_review.creator, self.user)

    def test_no_tag_on_immediately_previous_version(self):
        """Does not apply a tag on a trait from two versions ago."""
        tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(tag=tag, trait=self.deprecated_source_trait)
        newer_study_version = SourceStudyVersionFactory.create(
            study=self.study, i_version=self.updated_study_version.i_version + 1,
            i_date_added=timezone.now() - timedelta(minutes=30))
        newer_source_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=newer_study_version,
            i_dbgap_variable_accession=self.deprecated_source_trait.i_dbgap_variable_accession
        )
        newer_source_trait.apply_previous_tags(self.user)
        newer_source_trait.refresh_from_db()
        self.assertEqual(newer_source_trait.all_taggedtraits.count(), 0)

    def test_ignores_newer_version(self):
        """Ignores a newer version when applying tags."""
        updated_tagged_trait = factories.TaggedTraitFactory.create(trait=self.updated_source_trait)
        self.deprecated_source_trait.apply_previous_tags(self.user)
        self.deprecated_source_trait.refresh_from_db()
        self.assertEqual(self.deprecated_source_trait.all_taggedtraits.count(), 0)

    def test_works_if_all_tags_already_applied(self):
        """Returns gracefully if the tagged traits already exist."""
        tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(tag=tag, trait=self.deprecated_source_trait)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 1)
        updated_tagged_trait = self.updated_source_trait.all_taggedtraits.first()
        other_user = UserFactory.create()
        self.updated_source_trait.apply_previous_tags(other_user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(updated_tagged_trait.tag, deprecated_tagged_trait.tag)
        self.assertEqual(updated_tagged_trait.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait.archived)
        self.assertEqual(updated_tagged_trait.creator, self.user)
        self.assertEqual(updated_tagged_trait.previous_tagged_trait, deprecated_tagged_trait)
        self.assertTrue(hasattr(updated_tagged_trait, 'dcc_review'))
        self.assertEqual(updated_tagged_trait.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait.dcc_review.creator, self.user)

    def test_works_if_some_tags_already_applied(self):
        """Applies new tags if some already exist."""
        other_user = UserFactory.create()
        tag_1 = factories.TagFactory.create()
        tag_2 = factories.TagFactory.create()
        deprecated_tagged_trait_1 = factories.TaggedTraitFactory.create(tag=tag_1, trait=self.deprecated_source_trait)
        deprecated_tagged_trait_2 = factories.TaggedTraitFactory.create(tag=tag_2, trait=self.deprecated_source_trait)
        # Create one tag for the updated trait.
        factories.TaggedTraitFactory.create(tag=tag_1, trait=self.updated_source_trait, creator=other_user)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 2)
        self.assertEqual(sorted(self.updated_source_trait.all_taggedtraits.all().values_list('tag__pk', flat=True)),
                         sorted([tag_1.pk, tag_2.pk]))
        # Check the first tagged trait.
        updated_tagged_trait_1 = self.updated_source_trait.all_taggedtraits.get(tag=tag_1)
        self.assertEqual(updated_tagged_trait_1.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait_1.archived)
        self.assertEqual(updated_tagged_trait_1.creator, other_user)
        self.assertIsNone(updated_tagged_trait_1.previous_tagged_trait)
        self.assertFalse(hasattr(updated_tagged_trait_1, 'dcc_review'))
        # Check the second trait.
        updated_tagged_trait_2 = self.updated_source_trait.all_taggedtraits.get(tag=tag_2)
        self.assertEqual(updated_tagged_trait_2.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait_2.archived)
        self.assertEqual(updated_tagged_trait_2.creator, self.user)
        self.assertEqual(updated_tagged_trait_2.previous_tagged_trait, deprecated_tagged_trait_2)
        self.assertTrue(hasattr(updated_tagged_trait_2, 'dcc_review'))
        self.assertEqual(updated_tagged_trait_2.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait_2.dcc_review.creator, self.user)

    def test_skips_archived_tag(self):
        """Does not apply an archived tag."""
        tag = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(
            tag=tag, trait=self.deprecated_source_trait, archived=True)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 0)

    def test_skips_archived_tag_with_non_archived_tag(self):
        """Applies only the non-archived tag if both an archived and non-archived tag exist."""
        tag_1 = factories.TagFactory.create()
        tag_2 = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(tag=tag_1, trait=self.deprecated_source_trait)
        archived_tagged_trait = factories.TaggedTraitFactory.create(
            tag=tag_2, trait=self.deprecated_source_trait, archived=True)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 1)
        updated_tagged_trait = self.updated_source_trait.all_taggedtraits.first()
        self.assertEqual(updated_tagged_trait.tag, tag_1)
        self.assertEqual(updated_tagged_trait.trait, self.updated_source_trait)
        self.assertFalse(updated_tagged_trait.archived)
        self.assertEqual(updated_tagged_trait.creator, self.user)
        self.assertEqual(updated_tagged_trait.previous_tagged_trait, deprecated_tagged_trait)
        self.assertTrue(hasattr(updated_tagged_trait, 'dcc_review'))
        self.assertEqual(updated_tagged_trait.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(updated_tagged_trait.dcc_review.creator, self.user)

    def test_no_previous_trait(self):
        """Does not apply any tags if there is no previous tagged trait."""
        self.deprecated_study_version.delete()
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 0)

    def test_does_not_remove_existing_tags(self):
        """Does not remove an existing tag."""
        other_user = UserFactory.create()
        tag_1 = factories.TagFactory.create()
        tag_2 = factories.TagFactory.create()
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(tag=tag_2, trait=self.deprecated_source_trait)
        existing_tagged_trait_1 = factories.TaggedTraitFactory.create(
            tag=tag_1, trait=self.updated_source_trait, creator=other_user)
        self.updated_source_trait.apply_previous_tags(self.user)
        self.updated_source_trait.refresh_from_db()
        self.assertEqual(self.updated_source_trait.all_taggedtraits.count(), 2)
        # Check the existing tagged trait.
        tagged_trait_1 = self.updated_source_trait.all_taggedtraits.get(tag=tag_1)
        self.assertEqual(tagged_trait_1.tag, tag_1)
        self.assertEqual(tagged_trait_1.trait, self.updated_source_trait)
        self.assertFalse(tagged_trait_1.archived)
        self.assertEqual(tagged_trait_1.creator, other_user)
        self.assertIsNone(tagged_trait_1.previous_tagged_trait)
        self.assertFalse(hasattr(tagged_trait_1, 'dcc_review'))
        # Check the newly-created tagged trait.
        tagged_trait_2 = self.updated_source_trait.all_taggedtraits.get(tag=tag_2)
        self.assertEqual(tagged_trait_2.tag, tag_2)
        self.assertEqual(tagged_trait_2.trait, self.updated_source_trait)
        self.assertFalse(tagged_trait_2.archived)
        self.assertEqual(tagged_trait_2.creator, self.user)
        self.assertEqual(tagged_trait_2.previous_tagged_trait, deprecated_tagged_trait)
        self.assertTrue(hasattr(tagged_trait_2, 'dcc_review'))
        self.assertEqual(tagged_trait_2.dcc_review.status, models.DCCReview.STATUS_CONFIRMED)
        self.assertEqual(tagged_trait_2.dcc_review.creator, self.user)


class TaggedTraitTest(TestCase):
    model = models.TaggedTrait
    model_factory = factories.TaggedTraitFactory

    def setUp(self):
        self.user = UserFactory.create()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.model_args = {'trait': self.trait, 'tag': self.tag, 'creator': self.user}

    def test_model_saving(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_factory(self):
        """Creation using the model factory."""
        instance = self.model_factory.create()
        self.assertIsInstance(self.model_factory._meta.model.objects.get(pk=instance.pk),
                              self.model_factory._meta.model)

    def test_printing(self):
        """The custom __str__ method returns a string."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance.__str__(), str)

    def test_unique_together(self):
        """Adding the same tag and trait combination doesn't work."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        duplicate = factories.TaggedTraitFactory.build(tag=self.tag, trait=self.trait)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = self.model_factory.create()
        url = instance.get_absolute_url()
        # Just test that this function works.

    def test_archive_unarchived_taggedtrait(self):
        """Archive method sets an unarchived taggedtrait to archived."""
        taggedtrait = self.model(archived=False, **self.model_args)
        taggedtrait.save()
        taggedtrait.archive()
        self.assertIn(taggedtrait, models.TaggedTrait.objects.archived())

    def test_unarchive_archived_taggedtrait(self):
        """Archive method sets an unarchived taggedtrait to archived."""
        taggedtrait = self.model(archived=True, **self.model_args)
        taggedtrait.save()
        taggedtrait.unarchive()
        self.assertIn(taggedtrait, models.TaggedTrait.objects.non_archived())

    def test_archive_archived_taggedtrait(self):
        """Archive method sets an unarchived taggedtrait to archived."""
        taggedtrait = self.model(archived=True, **self.model_args)
        taggedtrait.save()
        taggedtrait.archive()
        self.assertIn(taggedtrait, models.TaggedTrait.objects.archived())

    def test_unarchive_unarchived_taggedtrait(self):
        """Archive method sets an unarchived taggedtrait to archived."""
        taggedtrait = self.model(archived=False, **self.model_args)
        taggedtrait.save()
        taggedtrait.unarchive()
        self.assertIn(taggedtrait, models.TaggedTrait.objects.non_archived())

    def test_cannot_delete_user_who_created_tagged_trait(self):
        """Unable to delete a user who has created a tagged_trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        with self.assertRaises(ProtectedError):
            tagged_trait.creator.delete()

    def test_previous_tagged_trait(self):
        """Setting the previous_tagged_trait model field works as expected."""
        previous_tagged_trait = factories.TaggedTraitFactory.create()
        tagged_trait = factories.TaggedTraitFactory.create(previous_tagged_trait=previous_tagged_trait)
        self.assertEqual(tagged_trait.previous_tagged_trait, previous_tagged_trait)
        self.assertEqual(previous_tagged_trait.updated_tagged_trait, tagged_trait)

    def test_previous_tagged_trait_delete(self):
        """Cannot delete a TaggedTrait that is used as a previous_tagged_trait in another object."""
        previous_tagged_trait = factories.TaggedTraitFactory.create()
        tagged_trait = factories.TaggedTraitFactory.create(previous_tagged_trait=previous_tagged_trait)
        with self.assertRaises(ProtectedError):
            previous_tagged_trait.delete()
        # Make sure it was not deleted...
        previous_tagged_trait.refresh_from_db()
        # ...and is still linked to the tagged trait.
        tagged_trait.refresh_from_db()
        self.assertEqual(tagged_trait.previous_tagged_trait, previous_tagged_trait)

    def test_get_latest_version_is_most_recent(self):
        """Returns itself if this is the latest version of the TaggedTrait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        self.assertEqual(tagged_trait.get_latest_version(), tagged_trait)

    def test_get_latest_version_one_updated_version(self):
        """Returns the correct object if there is one updated version of the tagged trait."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        deprecated_study_version = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=2)
        deprecated_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version, i_dbgap_variable_accession=1)
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=1)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=deprecated_trait, tag=tag)
        tagged_trait = factories.TaggedTraitFactory.create(trait=trait, tag=tag)
        self.assertEqual(deprecated_tagged_trait.get_latest_version(), tagged_trait)

    def test_get_latest_version_two_updated_versions(self):
        """Returns the correct object if there are two updated versions of the tagged trait."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        deprecated_study_version_1 = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        deprecated_study_version_2 = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=2)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=3)
        deprecated_trait_1 = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version_1, i_dbgap_variable_accession=1)
        deprecated_trait_2 = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version_2, i_dbgap_variable_accession=1)
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=1)
        deprecated_tagged_trait_1 = factories.TaggedTraitFactory.create(trait=deprecated_trait_1, tag=tag)
        deprecated_tagged_trait_2 = factories.TaggedTraitFactory.create(trait=deprecated_trait_2, tag=tag)
        tagged_trait = factories.TaggedTraitFactory.create(trait=trait, tag=tag)
        self.assertEqual(deprecated_tagged_trait_1.get_latest_version(), tagged_trait)

    def test_get_latest_version_different_tag(self):
        """Returns None if there is no new version with the same tag."""
        study = StudyFactory.create()
        deprecated_study_version = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=2)
        deprecated_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version, i_dbgap_variable_accession=1)
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=1)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=deprecated_trait)
        tagged_trait = factories.TaggedTraitFactory.create(trait=trait)
        self.assertIsNone(deprecated_tagged_trait.get_latest_version())

    def test_get_latest_version_different_trait(self):
        """Does not return anything if there is no new version with the same trait accession."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        deprecated_study_version = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=2)
        deprecated_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version)
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version=study_version)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=deprecated_trait, tag=tag)
        tagged_trait = factories.TaggedTraitFactory.create(trait=trait, tag=tag)
        self.assertIsNone(deprecated_tagged_trait.get_latest_version())

    def test_get_latest_version_trait_removed_in_newer_version(self):
        """Returns None if the trait doesn't exist in the newest version."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        deprecated_study_version = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=2)
        deprecated_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version, i_dbgap_variable_accession=1)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=deprecated_trait, tag=tag)
        self.assertIsNone(deprecated_tagged_trait.get_latest_version())

    def test_get_latest_version_tagged_trait_removed_in_newer_version(self):
        """Returns None if the trait, but not the TaggedTrait, exists in a newer version."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        deprecated_study_version = SourceStudyVersionFactory.create(
            study=study, i_is_deprecated=True, i_version=1)
        study_version = SourceStudyVersionFactory.create(
            study=study, i_version=2)
        deprecated_trait = SourceTraitFactory.create(
            source_dataset__source_study_version=deprecated_study_version, i_dbgap_variable_accession=1)
        trait = SourceTraitFactory.create(
            source_dataset__source_study_version=study_version, i_dbgap_variable_accession=1)
        deprecated_tagged_trait = factories.TaggedTraitFactory.create(trait=deprecated_trait, tag=tag)
        self.assertIsNone(deprecated_tagged_trait.get_latest_version())


class TaggedTraitQuerySetTest(TestCase):
    model = models.TaggedTrait
    model_factory = factories.TaggedTraitFactory

    # unreviewed()
    def test_unreviewed_queryset_excludes_dccreview_followup(self):
        """unreviewed() queryset does not include tagged trait with dcc review of status followup."""
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create()
        tagged_trait_followup = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_followup, status=models.DCCReview.STATUS_FOLLOWUP)
        qs = models.TaggedTrait.objects.unreviewed()
        self.assertIn(tagged_trait_unreviewed, qs)
        self.assertNotIn(tagged_trait_followup, qs)

    def test_unreviewed_queryset_excludes_dccreview_confirmed(self):
        """unreviewed() queryset does not include tagged trait with dcc review of status confirmed."""
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create()
        tagged_trait_confirmed = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_confirmed,
                                          status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.unreviewed()
        self.assertIn(tagged_trait_unreviewed, qs)
        self.assertNotIn(tagged_trait_confirmed, qs)

    def test_unreviewed_queryset_count(self):
        """unreviewed() queryset has the correct number of tagged traits in it."""
        n_unreviewed = 5
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create_batch(n_unreviewed)
        factories.DCCReviewFactory.create_batch(n_unreviewed + 1, status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCReviewFactory.create_batch(n_unreviewed + 2, status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.unreviewed()
        self.assertEqual(qs.count(), n_unreviewed)

    # need_followup()
    def test_need_followup_queryset_excludes_dccreview_confirmed(self):
        """need_followup() queryset does not include tagged trait with dcc review status confirmed."""
        tagged_trait_followup = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_followup, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait_confirmed = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_confirmed,
                                          status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.need_followup()
        self.assertIn(tagged_trait_followup, qs)
        self.assertNotIn(tagged_trait_confirmed, qs)

    def test_need_followup_queryset_excludes_unreviewed(self):
        """need_followup() queryset does not include tagged trait without a dcc review."""
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create()
        tagged_trait_followup = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_followup, status=models.DCCReview.STATUS_FOLLOWUP)
        qs = models.TaggedTrait.objects.need_followup()
        self.assertIn(tagged_trait_followup, qs)
        self.assertNotIn(tagged_trait_unreviewed, qs)

    def test_need_followup_queryset_includes_dccreview_with_studyresponse(self):
        """need_followup() queryset does include a tagged trait with a study response."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=tagged_trait,
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        factories.StudyResponseFactory.create(dcc_review=dcc_review)
        qs = models.TaggedTrait.objects.need_followup()
        self.assertEqual(qs.count(), 1)
        self.assertIn(tagged_trait, qs)

    def test_need_followup_queryset_includes_dccreview_with_dccdecision(self):
        """need_followup() queryset does include a tagged trait with a dcc decision."""
        tagged_trait = factories.TaggedTraitFactory.create()
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        study_response = factories.StudyResponseFactory.create(dcc_review=dcc_review)
        dcc_decision = factories.DCCDecisionFactory.create(dcc_review=dcc_review)
        qs = models.TaggedTrait.objects.need_followup()
        self.assertEqual(qs.count(), 1)
        self.assertIn(tagged_trait, qs)

    # confirmed()
    def test_confirmed_queryset_excludes_unreviewed(self):
        """confirmed() queryset excludes unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        qs = models.TaggedTrait.objects.confirmed()
        self.assertNotIn(tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_confirmed_queryset_excludes_dccreview_followup(self):
        """confirmed() queryset excludes tagged trait with dcc review status followup."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        qs = models.TaggedTrait.objects.confirmed()
        self.assertNotIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_confirmed_queryset_excludes_dccreview_followup_dccdecision_confirm(self):
        """confirmed() queryset excludes tagged trait with remove dcc decision."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        qs = models.TaggedTrait.objects.confirmed()
        self.assertNotIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_confirmed_queryset_includes_dccreview_confirmed(self):
        """confirmed() queryset includes tagged trait with confirmed dcc review."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.confirmed()
        self.assertIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_confirmed_queryset_includes_dccreview_followup_dccdecision_confirm(self):
        """confirmed() queryset includes tagged trait with confirm dcc decision."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        qs = models.TaggedTrait.objects.confirmed()
        self.assertIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_confirmed_queryset_includes_dccreview_confirmed_and_dccdecision_confirm(self):
        """confirmed() queryset includes both dcc review confirmed and dcc decision confirm ."""
        confirmed_dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        confirm_dcc_decision = factories.DCCDecisionFactory.create(decision=models.DCCDecision.DECISION_CONFIRM)
        qs = models.TaggedTrait.objects.confirmed()
        self.assertIn(confirmed_dcc_review.tagged_trait, qs)
        self.assertIn(confirm_dcc_decision.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 2)

    # need_study_response
    def test_need_study_response_queryset_excludes_dccreview_confirmed(self):
        """need_study_response() queryset excludes a tagged trait with a confirmed dcc review."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertNotIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_study_response_queryset_excludes_unreviewed(self):
        """need_study_response() queryset excludes an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertNotIn(tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_study_response_queryset_excludes_dccdecision_no_studyresponse(self):
        """need_study_response() queryset excludes a tagged trait with a dcc decision but no study response."""
        dcc_decision = factories.DCCDecisionFactory.create()
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertNotIn(dcc_decision.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_study_response_queryset_includes_dccreview_followup_no_studyresponse(self):
        """need_study_response() queryset includes a tagged trait with followup dcc review but no study response."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_need_study_response_queryset_includes_dccreview_followup_studyresponse_agree(self):
        """need_study_response() queryset includes a tagged trait with followup dcc review and agree study response."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_AGREE)
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertIn(study_response.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_need_study_response_queryset_includes_dccreview_followup_studyresponse_disagree(self):
        """need_study_response() queryset includes tagged trait with followup dcc review & disagree study response."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        qs = models.TaggedTrait.objects.need_study_response()
        self.assertIn(study_response.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    # need_decision
    def test_need_decision_queryset_excludes_unreviewed(self):
        """need_decision() queryset excludes an unreviewed tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        qs = models.TaggedTrait.objects.need_decision()
        self.assertNotIn(tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_decision_queryset_excludes_dccreview_confirmed(self):
        """need_decision() queryset excludes a tagged trait with confirmed dcc review."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertNotIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_decision_queryset_excludes_studyresponse_agree(self):
        """need_decision() queryset excludes a tagged trait with an agree study response and followup dcc review."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_AGREE)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertNotIn(study_response.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_decision_queryset_excludes_dccreview_followup_no_studyresponse(self):
        """need_decision() queryset excludes a tagged trait with followup dcc review but no study response."""
        dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertNotIn(dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 0)

    def test_need_decision_queryset_includes_dccreview_followup_studyresponse_disagree_no_dccdecision(self):
        """need_decision() queryset includes tagged trait with disagree study response but no dcc decision."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertIn(study_response.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_need_decision_queryset_includes_dccreview_followup_studyresponse_disagree_dccdecision_confirm(self):
        """need_decision() queryset includes tagged trait with confirm dcc decision and disagree study response."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertIn(dcc_decision.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    def test_need_decision_queryset_includes_dccreview_followup_studyresponse_disagree_dccdecision_remove(self):
        """need_decision() queryset includes tagged trait with remove dcc decision and disagree study response."""
        study_response = factories.StudyResponseFactory.create(status=models.StudyResponse.STATUS_DISAGREE)
        dcc_decision = factories.DCCDecisionFactory.create(
            dcc_review=study_response.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        qs = models.TaggedTrait.objects.need_decision()
        self.assertIn(dcc_decision.dcc_review.tagged_trait, qs)
        self.assertEqual(qs.count(), 1)

    # non_archived()
    def test_non_archived_queryset_count(self):
        """non_archived() queryset method returns correct number of tagged traits."""
        n_archived = 12
        n_non_archived = 16
        archived_taggedtraits = self.model_factory.create_batch(n_archived, archived=True)
        non_archived_taggedtraits = self.model_factory.create_batch(n_non_archived, archived=False)
        retrieved_queryset = self.model.objects.non_archived()
        self.assertEqual(n_non_archived, retrieved_queryset.count())

    def test_non_archived_queryset_excludes_archived(self):
        """non_archived() queryset method does not return archived tagged traits."""
        n_archived = 3
        n_non_archived = 4
        archived_taggedtraits = self.model_factory.create_batch(n_archived, archived=True)
        non_archived_taggedtraits = self.model_factory.create_batch(n_non_archived, archived=False)
        retrieved_queryset = self.model.objects.non_archived()
        for archivedtt in archived_taggedtraits:
            self.assertNotIn(archivedtt, retrieved_queryset)
        self.assertEqual(n_non_archived, retrieved_queryset.count())

    # archived()
    def test_archived_queryset_count(self):
        """archived() queryset method returns correct number of tagged traits."""
        n_archived = 12
        n_non_archived = 16
        archived_taggedtraits = self.model_factory.create_batch(n_archived, archived=True)
        non_archived_taggedtraits = self.model_factory.create_batch(n_non_archived, archived=False)
        retrieved_queryset = self.model.objects.archived()
        self.assertEqual(n_archived, retrieved_queryset.count())

    def test_archived_queryset_excludes_non_archived(self):
        """archived() queryset method does not return non-archived tagged traits."""
        n_archived = 3
        n_non_archived = 4
        archived_taggedtraits = self.model_factory.create_batch(n_archived, archived=True)
        non_archived_taggedtraits = self.model_factory.create_batch(n_non_archived, archived=False)
        retrieved_queryset = self.model.objects.archived()
        for nonarchivedtt in non_archived_taggedtraits:
            self.assertNotIn(nonarchivedtt, retrieved_queryset)
        self.assertEqual(n_archived, retrieved_queryset.count())

    # current()
    def test_current_queryset_count(self):
        """current() queryset method returns correct number of tagged traits."""
        n_current = 12
        n_deprecated = 16
        deprecated_taggedtraits = self.model_factory.create_batch(
            n_deprecated, trait__source_dataset__source_study_version__i_is_deprecated=True)
        current_taggedtraits = self.model_factory.create_batch(n_current)
        retrieved_queryset = self.model.objects.current()
        self.assertEqual(n_current, retrieved_queryset.count())

    def test_current_queryset_excludes_deprecated(self):
        """current() queryset method does not return deprecated tagged traits."""
        n_current = 3
        n_deprecated = 4
        deprecated_taggedtraits = self.model_factory.create_batch(
            n_deprecated, trait__source_dataset__source_study_version__i_is_deprecated=True)
        current_taggedtraits = self.model_factory.create_batch(n_current)
        retrieved_queryset = self.model.objects.current()
        for deprecated_tt in deprecated_taggedtraits:
            self.assertNotIn(deprecated_tt, retrieved_queryset)
        for current_tt in current_taggedtraits:
            self.assertIn(current_tt, retrieved_queryset)
        self.assertEqual(n_current, retrieved_queryset.count())


class TaggedTraitDeleteTest(TestCase):
    """Tests of the overridden delete method for the TaggedTrait model."""

    model = models.TaggedTrait
    model_factory = factories.TaggedTraitFactory

    def setUp(self):
        self.user = UserFactory.create()
        self.tag = factories.TagFactory.create()
        self.trait = SourceTraitFactory.create()
        self.model_args = {'trait': self.trait, 'tag': self.tag, 'creator': self.user}

    # Tests of the overridden delete().
    def test_delete_archives_reviewed_needfollowup_taggedtrait(self):
        """Archives a reviewed taggedtrait with status need_followup."""
        tagged_trait = self.model_factory.create(**self.model_args)
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.delete()
        self.assertIn(tagged_trait, models.TaggedTrait.objects.archived())

    def test_delete_raises_error_reviewed_confirmed_taggedtrait(self):
        """Raises an error for a reviewed taggedtrait with status confirmed."""
        tagged_trait = self.model_factory.create(**self.model_args)
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        with self.assertRaises(DeleteNotAllowedError):
            tagged_trait.delete()
        self.assertIn(tagged_trait, models.TaggedTrait.objects.non_archived())

    def test_delete_hard_deletes_unreviewed_taggedtrait(self):
        """Hard deletes an unreviewed taggedtrait."""
        tagged_trait = self.model_factory.create(**self.model_args)
        tagged_trait.delete()
        self.assertNotIn(tagged_trait, models.TaggedTrait.objects.all())

    # Tests of hard_delete().
    def test_hard_delete_need_followup(self):
        """Deletes a need_followup tagged trait."""
        tagged_trait = self.model_factory.create(**self.model_args)
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP)
        tagged_trait.hard_delete()
        self.assertNotIn(tagged_trait, models.TaggedTrait.objects.all())

    def test_hard_delete_confirmed(self):
        """Deletes a confirmed tagged trait."""
        tagged_trait = self.model_factory.create(**self.model_args)
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        tagged_trait.hard_delete()
        self.assertNotIn(tagged_trait, models.TaggedTrait.objects.all())

    def test_hard_delete_unreviewed(self):
        """Deletes an unreviewed tagged trait."""
        tagged_trait = self.model_factory.create(**self.model_args)
        tagged_trait.hard_delete()
        self.assertNotIn(tagged_trait, models.TaggedTrait.objects.all())

    # Tests of the queryset delete().
    def test_queryset_delete_unreviewed(self):
        """Deletes all unreviewed tagged traits."""
        unreviewed = factories.TaggedTraitFactory.create_batch(5)
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), 0)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(), 0)

    def test_queryset_delete_needs_followup(self):
        """Archives all need_followup tagged traits."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_FOLLOWUP)
        needs_followup = models.TaggedTrait.objects.all()
        n_needs_followup = needs_followup.count()
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_needs_followup)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), n_needs_followup)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(), 0)
        self.assertEqual(list(models.TaggedTrait.objects.need_followup().values_list('archived', flat=True)),
                         [True] * n_needs_followup)

    def test_queryset_delete_confirmed(self):
        """Gives an error for confirmed tagged traits."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_CONFIRMED)
        confirmed = models.TaggedTrait.objects.all()
        n_confirmed = confirmed.count()
        with self.assertRaises(DeleteNotAllowedError):
            models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_confirmed)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), 0)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(), n_confirmed)
        self.assertEqual(list(models.TaggedTrait.objects.confirmed().values_list('archived', flat=True)),
                         [False] * n_confirmed)

    def test_queryset_delete_needs_followup_and_unreviewed(self):
        """Archives need_followup and deletes unreviewed tagged traits."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_FOLLOWUP)
        needs_followup = models.TaggedTrait.objects.all()
        n_needs_followup = needs_followup.count()
        unreviewed = factories.TaggedTraitFactory.create_batch(4)
        unreviewed = models.TaggedTrait.objects.unreviewed()
        n_unreviewed = unreviewed.count()
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_needs_followup)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), n_needs_followup)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(), 0)
        self.assertEqual(list(models.TaggedTrait.objects.need_followup().values_list('archived', flat=True)),
                         [True] * n_needs_followup)

    def test_queryset_delete_needs_followup_and_unreviewed_and_confirmed(self):
        """Archives need_followup and deletes unreviewed tagged traits. Raises an error for confirmed."""
        unreviewed = factories.TaggedTraitFactory.create_batch(5)
        dcc_reviews = factories.DCCReviewFactory.create_batch(4, comment='foo',
                                                              status=models.DCCReview.STATUS_FOLLOWUP)
        confirmed_dcc_reviews = factories.DCCReviewFactory.create_batch(3, status=models.DCCReview.STATUS_CONFIRMED)
        unreviewed = models.TaggedTrait.objects.unreviewed()
        confirmed = models.TaggedTrait.objects.confirmed()
        needs_followup = models.TaggedTrait.objects.need_followup()
        n_needs_followup = needs_followup.count()
        n_unreviewed = unreviewed.count()
        n_confirmed = confirmed.count()
        with self.assertRaises(DeleteNotAllowedError):
            models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_needs_followup + n_confirmed + n_unreviewed)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), 0)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(),
                         n_needs_followup + n_confirmed + n_unreviewed)
        self.assertEqual(list(models.TaggedTrait.objects.all().values_list('archived', flat=True)),
                         [False] * models.TaggedTrait.objects.count())

    def test_queryset_delete_unreviewed_and_confirmed(self):
        """Deletes unreviewed tagged traits. Raises an error for confirmed."""
        unreviewed = factories.TaggedTraitFactory.create_batch(5)
        dcc_reviews = factories.DCCReviewFactory.create_batch(4, status=models.DCCReview.STATUS_FOLLOWUP)
        confirmed_dcc_reviews = factories.DCCReviewFactory.create_batch(3, status=models.DCCReview.STATUS_CONFIRMED)
        unreviewed = models.TaggedTrait.objects.unreviewed()
        confirmed = models.TaggedTrait.objects.confirmed()
        needs_followup = models.TaggedTrait.objects.need_followup()
        n_needs_followup = needs_followup.count()
        n_unreviewed = unreviewed.count()
        n_confirmed = confirmed.count()
        with self.assertRaises(DeleteNotAllowedError):
            models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_needs_followup + n_confirmed + n_unreviewed)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), 0)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(),
                         n_needs_followup + n_confirmed + n_unreviewed)
        self.assertEqual(list(models.TaggedTrait.objects.all().values_list('archived', flat=True)),
                         [False] * models.TaggedTrait.objects.count())

    def test_queryset_delete_needs_followup_and_confirmed(self):
        """Archives need_followup and raises an error for confirmed."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(4, status=models.DCCReview.STATUS_FOLLOWUP)
        confirmed_dcc_reviews = factories.DCCReviewFactory.create_batch(3, status=models.DCCReview.STATUS_CONFIRMED)
        confirmed = models.TaggedTrait.objects.confirmed()
        needs_followup = models.TaggedTrait.objects.need_followup()
        n_needs_followup = needs_followup.count()
        n_confirmed = confirmed.count()
        with self.assertRaises(DeleteNotAllowedError):
            models.TaggedTrait.objects.all().delete()
        self.assertEqual(models.TaggedTrait.objects.count(), n_needs_followup + n_confirmed)
        self.assertEqual(models.TaggedTrait.objects.archived().count(), 0)
        self.assertEqual(models.TaggedTrait.objects.non_archived().count(), n_confirmed + n_needs_followup)
        self.assertEqual(list(models.TaggedTrait.objects.need_followup().values_list('archived', flat=True)),
                         [False] * n_needs_followup)
        self.assertEqual(list(models.TaggedTrait.objects.confirmed().values_list('archived', flat=True)),
                         [False] * n_confirmed)

    # Tests of the queryset hard_delete().
    def test_queryset_hard_delete_unreviewed(self):
        """Deletes unreviewed tagged traits."""
        tagged_traits = factories.TaggedTraitFactory.create_batch(5)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)

    def test_queryset_hard_delete_need_followup(self):
        """Deletes need_followup tagged traits."""
        tagged_traits = factories.TaggedTraitFactory.create_batch(5)
        tagged_trait_to_review = tagged_traits[1]
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_to_review, status=models.DCCReview.STATUS_FOLLOWUP)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)

    def test_queryset_hard_delete_confirmed(self):
        """Deletes confirmed tagged traits."""
        tagged_traits = factories.TaggedTraitFactory.create_batch(5)
        tagged_trait_to_review = tagged_traits[1]
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_to_review,
                                          status=models.DCCReview.STATUS_CONFIRMED)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)

    def test_queryset_hard_delete_unreviewed_and_need_followup(self):
        """Deletes unreviewed and need_followup tagged traits."""
        factories.DCCReviewFactory.create_batch(5, comment='foo', status=models.DCCReview.STATUS_FOLLOWUP)
        factories.TaggedTraitFactory.create_batch(5)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)

    def test_queryset_hard_delete_unreviewed_and_confirmed(self):
        """Deletes unreviewed and confirmed tagged traits."""
        factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_CONFIRMED)
        factories.TaggedTraitFactory.create_batch(5)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)

    def test_queryset_hard_delete_unreviewed_and_need_followup_and_confirmed(self):
        """Deletes unreviewed and need_followup and confirmed tagged traits."""
        factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_FOLLOWUP)
        factories.DCCReviewFactory.create_batch(5, status=models.DCCReview.STATUS_CONFIRMED)
        factories.TaggedTraitFactory.create_batch(5)
        models.TaggedTrait.objects.all().hard_delete()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)


class DCCReviewTest(TestCase):
    model = models.DCCReview
    model_factory = factories.DCCReviewFactory

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()
        self.status = self.model.STATUS_CONFIRMED
        self.comment = 'a test comment'
        self.user = UserFactory.create()
        self.model_args = {'tagged_trait': self.tagged_trait, 'status': self.status, 'comment': self.comment,
                           'creator': self.user}

    def test_model_saving(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_saving_with_comment(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_factory(self):
        """Creation using the model factory."""
        instance = self.model_factory.create()
        self.assertIsInstance(self.model_factory._meta.model.objects.get(pk=instance.pk),
                              self.model_factory._meta.model)

    def test_printing(self):
        """The custom __str__ method returns a string."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance.__str__(), str)

    def test_get_absolute_url(self):
        """get_absolute_url function doesn't fail."""
        instance = self.model_factory.create()
        url = instance.get_absolute_url()
        # Just test that this function works.

    def test_cannot_delete_user_who_created_dcc_review(self):
        """Unable to delete a user who has created a dcc_review."""
        dcc_review = factories.DCCReviewFactory.create()
        with self.assertRaises(ProtectedError):
            dcc_review.creator.delete()


class DCCReviewDeleteTest(TestCase):

    model = models.DCCReview
    model_factory = factories.DCCReviewFactory

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()
        self.status = self.model.STATUS_CONFIRMED
        self.comment = 'a test comment'
        self.user = UserFactory.create()
        self.model_args = {'tagged_trait': self.tagged_trait, 'status': self.status, 'comment': self.comment,
                           'creator': self.user}

    # Tests of the overridden delete().
    def test_delete_fails_with_studyresponse_agree(self):
        """A DCCReview with a study response cannot be deleted."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        with self.assertRaises(DeleteNotAllowedError):
            dcc_review.delete()
        dcc_review.refresh_from_db()

    def test_delete_fails_with_studyresponse_disagree(self):
        """A DCCReview with a study response cannot be deleted."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        with self.assertRaises(DeleteNotAllowedError):
            dcc_review.delete()
        dcc_review.refresh_from_db()

    def test_delete_fails_with_dccdecision_confirm(self):
        """A DCCReview with a dcc decision cannot be deleted."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        with self.assertRaises(DeleteNotAllowedError):
            dcc_review.delete()
        dcc_review.refresh_from_db()

    def test_delete_fails_with_dccdecision_remove(self):
        """A DCCReview with a dcc decision cannot be deleted."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            dcc_review.delete()
        dcc_review.refresh_from_db()

    def test_delete_succeeds_without_studyresponse_or_dccdecision(self):
        """A DCCReview without a StudyResponse or DCCDecision can be deleted."""
        dcc_review = self.model_factory.create(**self.model_args)
        dcc_review.delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    # Tests of hard_delete().
    def test_hard_delete_succeeds_dccreview_with_studyresponse_agree(self):
        """A DCCReview with StudyResponse agree status can be deleted with hard_delete."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_AGREE)
        dcc_review.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    def test_hard_delete_succeeds_dccreview_with_studyresponse_disagree(self):
        """A DCCReview with StudyResponse disagree status can be deleted with hard_delete."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.StudyResponseFactory.create(dcc_review=dcc_review, status=models.StudyResponse.STATUS_DISAGREE)
        dcc_review.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    def test_hard_delete_succeeds_dccreview_with_dccdecision_confirm(self):
        """A DCCReview with DCCDecision confirm can be deleted with hard_delete."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        dcc_review.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    def test_hard_delete_succeeds_dccreview_with_dccdecision_remove(self):
        """A DCCReview with DCCDecision remove can be deleted with hard_delete."""
        dcc_review = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        dcc_review.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    def test_hard_delete_succeeds_dccreview_without_studyresponse_or_dccdecision(self):
        """A DCCReview without StudyResponse or DCCDecision can be deleted with hard_delete."""
        dcc_review = self.model_factory.create(**self.model_args)
        dcc_review.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            dcc_review.refresh_from_db()

    # Tests of the queryset delete().
    def test_queryset_delete_fails_with_one_dccreview_with_study_response_agree(self):
        """Does not delete any DCCReviews if one has a StudyResponse with status agree."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.StudyResponseFactory.create(dcc_review=dcc_review_to_respond,
                                              status=models.StudyResponse.STATUS_AGREE)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_fails_with_one_dccreview_with_study_response_disagree(self):
        """Does not delete any DCCReviews if one has a StudyResponse with status disagree."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.StudyResponseFactory.create(dcc_review=dcc_review_to_respond,
                                              status=models.StudyResponse.STATUS_DISAGREE)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_fails_with_multiple_dcc_reviews_with_responses(self):
        """Does not delete any DCCReviews if multiple have a StudyResponse."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        factories.StudyResponseFactory.create(dcc_review=dcc_reviews[1], status=models.StudyResponse.STATUS_AGREE)
        factories.StudyResponseFactory.create(dcc_review=dcc_reviews[3], status=models.StudyResponse.STATUS_DISAGREE)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_fails_with_one_dccreview_with_dccdecision_confirm(self):
        """Does not delete any DCCReviews if one has a DCCDecision with decision confirm."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.DCCDecisionFactory.create(dcc_review=dcc_review_to_respond,
                                            decision=models.DCCDecision.DECISION_CONFIRM)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_fails_with_one_dccreview_with_dccdecision_remove(self):
        """Does not delete any DCCReviews if one has a DCCDecision with decision remove."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.DCCDecisionFactory.create(dcc_review=dcc_review_to_respond,
                                            decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_fails_with_multiple_dcc_reviews_with_dccdecisions(self):
        """Does not delete any DCCReviews if multiple reviews have a DCCDecision."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        factories.DCCDecisionFactory.create(dcc_review=dcc_reviews[1], decision=models.DCCDecision.DECISION_CONFIRM)
        factories.DCCDecisionFactory.create(dcc_review=dcc_reviews[3], decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 5)

    def test_queryset_delete_succeeds_with_no_studyresponses_or_dccdecisions(self):
        """Deletes dcc reviews without StudyResponses."""
        dcc_review = factories.DCCReviewFactory.create_batch(5)
        models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    # Tests of the queryset hard_delete().
    def test_queryset_hard_delete_succeeds_with_one_studyresponse_agree(self):
        """hard_delete deletes DCCReview regardless of StudyResponse agree existence."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.StudyResponseFactory.create(dcc_review=dcc_review_to_respond,
                                              status=models.StudyResponse.STATUS_AGREE)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_one_studyresponse_disagree(self):
        """hard_delete deletes DCCReview regardless of StudyResponse disagree existence."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.StudyResponseFactory.create(dcc_review=dcc_review_to_respond,
                                              status=models.StudyResponse.STATUS_DISAGREE)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_one_studyresponse_remove(self):
        """hard_delete deletes DCCReview that has DCCDecision remove."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.DCCDecisionFactory.create(dcc_review=dcc_review_to_respond,
                                            decision=models.DCCDecision.DECISION_REMOVE)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_one_dccdecision_confirm(self):
        """hard_delete deletes DCCReview that has DCCDecision confirm."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.DCCDecisionFactory.create(dcc_review=dcc_review_to_respond,
                                            decision=models.DCCDecision.DECISION_CONFIRM)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_one_dccdecision_remove(self):
        """hard_delete deletes DCCReview that has DCCDecision remove."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        dcc_review_to_respond = dcc_reviews[1]
        factories.DCCDecisionFactory.create(dcc_review=dcc_review_to_respond,
                                            decision=models.DCCDecision.DECISION_REMOVE)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_multiple_dcc_reviews_with_responses(self):
        """hard_delete deletes multiple dcc reviews regardless of study response and dcc decision existence."""
        dcc_reviews = factories.DCCReviewFactory.create_batch(5)
        factories.StudyResponseFactory.create(dcc_review=dcc_reviews[0], status=models.StudyResponse.STATUS_AGREE)
        factories.StudyResponseFactory.create(dcc_review=dcc_reviews[1], status=models.StudyResponse.STATUS_DISAGREE)
        factories.DCCDecisionFactory.create(dcc_review=dcc_reviews[2], decision=models.DCCDecision.DECISION_CONFIRM)
        factories.DCCDecisionFactory.create(dcc_review=dcc_reviews[3], decision=models.DCCDecision.DECISION_REMOVE)
        models.DCCReview.objects.all().hard_delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_no_studyresponses_or_dccdecisions(self):
        """hard_delete deletes DCCReviews with no StudyResponse or DCCDecision."""
        dcc_review = factories.DCCReviewFactory.create_batch(5)
        models.DCCReview.objects.all().delete()
        self.assertEqual(models.DCCReview.objects.count(), 0)


class StudyResponseTest(TestCase):
    model = models.StudyResponse
    model_factory = factories.StudyResponseFactory

    def setUp(self):
        self.dcc_review = factories.DCCReviewFactory.create()
        self.status = self.model.STATUS_AGREE
        self.comment = ''
        self.user = UserFactory.create()
        self.model_args = {'dcc_review': self.dcc_review, 'status': self.status, 'comment': self.comment,
                           'creator': self.user}

    def test_model_saving(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_saving_with_comment(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_factory(self):
        """Creation using the model factory."""
        instance = self.model_factory.create()
        self.assertIsInstance(self.model_factory._meta.model.objects.get(pk=instance.pk),
                              self.model_factory._meta.model)

    def test_printing(self):
        """The custom __str__ method returns a string."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance.__str__(), str)

    def test_cannot_delete_user_who_created_study_response(self):
        """Unable to delete a user who has created a study_response."""
        study_response = factories.StudyResponseFactory.create()
        with self.assertRaises(ProtectedError):
            study_response.creator.delete()


class StudyResponseDeleteTest(TestCase):

    model = models.StudyResponse
    model_factory = factories.StudyResponseFactory

    def setUp(self):
        self.tagged_trait = factories.TaggedTraitFactory.create()
        self.dcc_review = factories.DCCReviewFactory.create(
            status=models.DCCReview.STATUS_FOLLOWUP, tagged_trait=self.tagged_trait)
        self.status = self.model.STATUS_AGREE
        self.comment = 'a test comment'
        self.user = UserFactory.create()
        self.model_args = {'dcc_review': self.dcc_review, 'status': self.status, 'comment': self.comment,
                           'creator': self.user}

    # Tests of the overridden delete().
    def test_delete_fails_with_dccdecision_confirm(self):
        """A StudyResponse with a dcc decision cannot be deleted."""
        study_response = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=self.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        with self.assertRaises(DeleteNotAllowedError):
            study_response.delete()
        study_response.refresh_from_db()

    def test_delete_fails_with_dccdecision_remove(self):
        """A StudyResponse with a dcc decision cannot be deleted."""
        study_response = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=self.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            study_response.delete()
        study_response.refresh_from_db()

    def test_delete_succeeds_without_dccdecision(self):
        """A StudyResponse without a DCCDecision can be deleted."""
        study_response = self.model_factory.create(**self.model_args)
        study_response.delete()
        with self.assertRaises(ObjectDoesNotExist):
            study_response.refresh_from_db()

    # Tests of hard_delete().
    def test_hard_delete_succeeds_studyresponse_with_dccdecision_confirm(self):
        """A StudyResponse with DCCDecision confirm can be deleted with hard_delete."""
        study_response = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=self.dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        study_response.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            study_response.refresh_from_db()

    def test_hard_delete_succeeds_studyresponse_with_dccdecision_remove(self):
        """A StudyResponse with DCCDecision remove can be deleted with hard_delete."""
        study_response = self.model_factory.create(**self.model_args)
        factories.DCCDecisionFactory.create(dcc_review=self.dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        study_response.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            study_response.refresh_from_db()

    def test_hard_delete_succeeds_studyresponse_without_dccdecision(self):
        """A StudyResponse without DCCDecision can be deleted with hard_delete."""
        study_response = self.model_factory.create(**self.model_args)
        study_response.hard_delete()
        with self.assertRaises(ObjectDoesNotExist):
            study_response.refresh_from_db()

    # Tests of the queryset delete().
    def test_queryset_delete_fails_with_one_studyresponse_with_dccdecision_confirm(self):
        """Does not delete any StudyResponses if one has a DCCDecision with decision confirm."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        study_response_to_decide = study_responses[1]
        factories.DCCDecisionFactory.create(dcc_review=study_response_to_decide.dcc_review,
                                            decision=models.DCCDecision.DECISION_CONFIRM)
        with self.assertRaises(DeleteNotAllowedError):
            models.StudyResponse.objects.all().delete()
        self.assertEqual(models.StudyResponse.objects.count(), 5)

    def test_queryset_delete_fails_with_one_dccreview_with_dccdecision_remove(self):
        """Does not delete any StudyResponses if one has a DCCDecision with decision remove."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        study_response_to_decide = study_responses[1]
        factories.DCCDecisionFactory.create(dcc_review=study_response_to_decide.dcc_review,
                                            decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            models.StudyResponse.objects.all().delete()
        self.assertEqual(models.StudyResponse.objects.count(), 5)

    def test_queryset_delete_fails_with_multiple_dcc_reviews_with_dccdecisions(self):
        """Does not delete any StudyResponses if multiple reviews have a DCCDecision."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        factories.DCCDecisionFactory.create(
            dcc_review=study_responses[1].dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        factories.DCCDecisionFactory.create(
            dcc_review=study_responses[3].dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        with self.assertRaises(DeleteNotAllowedError):
            models.StudyResponse.objects.all().delete()
        self.assertEqual(models.StudyResponse.objects.count(), 5)

    def test_queryset_delete_succeeds_with_no_dccdecisions(self):
        """Deletes StudyResponses without DCCDecisions."""
        study_response = factories.StudyResponseFactory.create_batch(5)
        models.StudyResponse.objects.all().delete()
        self.assertEqual(models.StudyResponse.objects.count(), 0)

    # Tests of the queryset hard_delete().
    def test_queryset_hard_delete_succeeds_with_one_dccdecision_remove(self):
        """hard_delete deletes StudyResponse that has DCCDecision remove."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        study_response_to_decide = study_responses[1]
        factories.DCCDecisionFactory.create(dcc_review=study_response_to_decide.dcc_review,
                                            decision=models.DCCDecision.DECISION_REMOVE)
        models.StudyResponse.objects.all().hard_delete()
        self.assertEqual(models.StudyResponse.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_one_dccdecision_confirm(self):
        """hard_delete deletes StudyResponse that has DCCDecision confirm."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        study_response_to_decide = study_responses[1]
        factories.DCCDecisionFactory.create(dcc_review=study_response_to_decide.dcc_review,
                                            decision=models.DCCDecision.DECISION_CONFIRM)
        models.StudyResponse.objects.all().hard_delete()
        self.assertEqual(models.StudyResponse.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_multiple_studyresponses_with_dccdecisions(self):
        """hard_delete deletes multiple study responses regardless of dcc decision existence."""
        study_responses = factories.StudyResponseFactory.create_batch(5)
        factories.DCCDecisionFactory.create(
            dcc_review=study_responses[2].dcc_review, decision=models.DCCDecision.DECISION_CONFIRM)
        factories.DCCDecisionFactory.create(
            dcc_review=study_responses[3].dcc_review, decision=models.DCCDecision.DECISION_REMOVE)
        models.StudyResponse.objects.all().hard_delete()
        self.assertEqual(models.StudyResponse.objects.count(), 0)

    def test_queryset_hard_delete_succeeds_with_no_dccdecisions(self):
        """hard_delete deletes StudyResponses with no DCCDecision."""
        study_response = factories.StudyResponseFactory.create_batch(5)
        models.StudyResponse.objects.all().hard_delete()
        self.assertEqual(models.StudyResponse.objects.count(), 0)


class DCCDecisionTest(TestCase):
    model = models.DCCDecision
    model_factory = factories.DCCDecisionFactory

    def setUp(self):
        self.dcc_review = factories.DCCReviewFactory.create(status=models.DCCReview.STATUS_FOLLOWUP)
        self.decision = self.model.DECISION_REMOVE
        self.comment = ''
        self.user = UserFactory.create()
        self.model_args = {'dcc_review': self.dcc_review, 'decision': self.decision, 'comment': self.comment,
                           'creator': self.user}

    def test_model_saving(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_saving_with_comment(self):
        """Creation using the model constructor and .save() works."""
        instance = self.model(**self.model_args)
        instance.save()
        self.assertIsInstance(instance, self.model)

    def test_model_factory(self):
        """Creation using the model factory."""
        instance = self.model_factory.create()
        self.assertIsInstance(self.model_factory._meta.model.objects.get(pk=instance.pk),
                              self.model_factory._meta.model)

    def test_printing(self):
        """The custom __str__ method returns a string."""
        instance = self.model_factory.create()
        self.assertIsInstance(instance.__str__(), str)

    def test_cannot_delete_user_who_created_dcc_decision(self):
        """Unable to delete a user who has created a dcc decision."""
        instance = self.model_factory.create()
        with self.assertRaises(ProtectedError):
            instance.creator.delete()
