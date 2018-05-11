"""Tests of models for the tags app."""

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from core.factories import UserFactory
# from core.utils import UserLoginTestCase
from trait_browser.factories import SourceTraitFactory, StudyFactory
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
        self.assertIn(trait, tag.traits.all())


class StudyTaggedTraitsTest(TestCase):

    def setUp(self):
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study)

    def test_get_tagged_traits(self):
        """Returns the correct set of tagged traits for a study."""
        self.assertEqual(list(self.study.get_tagged_traits()), self.tagged_traits)

    def test_get_tagged_traits_empty(self):
        """Returns an empty queryset when a study has no tagged traits."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(list(self.study.get_tagged_traits()), [])

    def test_get_tagged_traits_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(list(self.study.get_tagged_traits()), self.tagged_traits)
        self.assertEqual(list(another_study.get_tagged_traits()), more_tagged_traits)

    def test_get_tagged_trait_count(self):
        """Returns the correct number of tagged traits for a study."""
        self.assertEqual(self.study.get_tagged_trait_count(), len(self.tagged_traits))

    def test_get_tagged_trait_count_empty(self):
        """Returns 0 when a study has no tagged traits."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(self.study.get_tagged_trait_count(), 0)

    def test_get_tagged_trait_count_two_studies(self):
        """Returns the correct set of tagged traits for a study, when other studies and tagged traits exist."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(self.study.get_tagged_trait_count(), len(self.tagged_traits))
        self.assertEqual(another_study.get_tagged_trait_count(), len(more_tagged_traits))

    def test_get_tag_count(self):
        """Returns the correct number of tags for a study."""
        self.assertEqual(self.study.get_tag_count(), models.Tag.objects.all().count())

    def test_get_tag_count_none(self):
        """Returns the correct number of tags for a study when there are none."""
        models.TaggedTrait.objects.all().delete()
        self.assertEqual(self.study.get_tag_count(), 0)

    def test_get_tag_count_no_tags(self):
        """Returns the correct number of tags for a study when there are none."""
        models.TaggedTrait.objects.all().delete()
        models.Tag.objects.all().delete()
        self.assertEqual(self.study.get_tag_count(), 0)

    def test_get_tag_count_two_studies(self):
        """Returns the correct number of tags for a study."""
        another_study = StudyFactory.create()
        more_tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=another_study)
        self.assertEqual(self.study.get_tag_count(),
                         models.Tag.objects.filter(
                         traits__source_dataset__source_study_version__study=self.study).distinct().count()
                         )
        self.assertEqual(another_study.get_tag_count(),
                         models.Tag.objects.filter(
                         traits__source_dataset__source_study_version__study=another_study).distinct().count()
                         )


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

    def test_unreviewed_queryset_method(self):
        """Only TaggedTraits that have not been reviewed are returned by the .unreviewed() filter."""
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create()
        tagged_trait_followup = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_followup, status=models.DCCReview.STATUS_FOLLOWUP,
                                          comment='foo')
        tagged_trait_confirmed = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_confirmed,
                                          status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.unreviewed()
        self.assertTrue(tagged_trait_unreviewed in qs)
        self.assertFalse(tagged_trait_followup in qs)
        self.assertFalse(tagged_trait_confirmed in qs)

    def test_need_followup_queryset_method(self):
        """Only TaggedTraits that need study followup are returned by the .needs_followup() filter."""
        tagged_trait_unreviewed = factories.TaggedTraitFactory.create()
        tagged_trait_followup = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_followup, status=models.DCCReview.STATUS_FOLLOWUP,
                                          comment='foo')
        tagged_trait_confirmed = factories.TaggedTraitFactory.create()
        factories.DCCReviewFactory.create(tagged_trait=tagged_trait_confirmed,
                                          status=models.DCCReview.STATUS_CONFIRMED)
        qs = models.TaggedTrait.objects.need_followup()
        self.assertTrue(tagged_trait_followup in qs)
        self.assertFalse(tagged_trait_unreviewed in qs)
        self.assertFalse(tagged_trait_confirmed in qs)


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
