"""Tests of views in the tags app."""

import copy
from faker import Faker

from django.contrib.auth.models import Group
from django.urls import reverse

from core.factories import UserFactory
from core.utils import (LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase,
                        DCCAnalystLoginTestCase, DCCDeveloperLoginTestCase, get_autocomplete_view_ids)
from trait_browser.factories import SourceTraitFactory, StudyFactory
from trait_browser.models import SourceTrait
from . import factories
from . import models
from . import tables
from . import forms
from . import views

fake = Faker()


class TagDetailTest(UserLoginTestCase):

    def setUp(self):
        super(TagDetailTest, self).setUp()
        self.tag = factories.TagFactory.create()

    def get_url(self, *args):
        return reverse('tags:tag:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)

    def test_no_tagging_button(self):
        """Regular user does not see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertNotContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagDetailPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TagDetailPhenotypeTaggerTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('tags:tag:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_has_tagging_button(self):
        """A phenotype tagger does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagDetailDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TagDetailDCCAnalystTest, self).setUp()
        self.study = StudyFactory.create()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('tags:tag:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_has_tagging_button(self):
        """A DCC analyst does see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertContains(response, reverse('tags:add-many:by-tag', kwargs={'pk': self.tag.pk}))


class TagListTest(UserLoginTestCase):

    def setUp(self):
        super(TagListTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(20)

    def get_url(self, *args):
        return reverse('tags:list')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('tag_table' in context)
        self.assertIsInstance(context['tag_table'], tables.TagTable)


class TaggedTraitDetailTestsMixin(object):
    """Mixin to run standard tests for the TaggedTraitDetail view, for use with TestCase or subclass of TestCase."""

    def get_url(self, *args):
        return reverse('tags:tagged-traits:pk:detail', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)


class TaggedTraitDetailTest(TaggedTraitDetailTestsMixin, UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def test_no_delete_button(self):
        """Regular user does not see a button to delete the tagged trait on this detail page."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_no_dcc_review_info(self):
        """A regular user does not see DCC review info on this detail page."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='dcc test comment'
        )
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, dcc_review.get_status_display())
        self.assertNotContains(response, dcc_review.comment)


class TaggedTraitDetailPhenotypeTaggerTest(TaggedTraitDetailTestsMixin, PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            trait__source_dataset__source_study_version__study=self.study,
            creator=self.user
        )
        self.user.refresh_from_db()

    def test_delete_button(self):
        """A phenotype tagger does see a button to delete the tagged trait."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_delete_button_for_other_studies(self):
        """A phenotype tagger does see a button to delete the tagged trait."""
        tagged_trait = factories.TaggedTraitFactory.create()
        response = self.client.get(self.get_url(tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': tagged_trait.pk}))

    def test_disabled_delete_button_for_reviewed_tagged_trait(self):
        """A phenotype tagger sees a disabled button to delete the tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP,
                                          comment='foo')
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_disabled_delete_button_for_confirmed_tagged_trait(self):
        """A phenotype tagger sees a disabled button to delete the tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_dcc_review_info(self):
        """A phenotype tagger does not see DCC review info on this detail page."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='dcc test comment'
        )
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, dcc_review.get_status_display())
        self.assertNotContains(response, dcc_review.comment)


class TaggedTraitDetailDCCAnalystTest(TaggedTraitDetailTestsMixin, DCCAnalystLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()
        self.user.refresh_from_db()

    def test_delete_button(self):
        """A DCC analyst does see a button to delete the tagged trait."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_disabled_delete_button_for_reviewed_tagged_trait(self):
        """A phenotype tagger sees a disabled button to delete the tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_FOLLOWUP,
                                          comment='foo')
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_disabled_delete_button_for_confirmed_tagged_trait(self):
        """A phenotype tagger sees a disabled button to delete the tagged trait."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertNotContains(response, reverse('tags:tagged-traits:pk:delete', kwargs={'pk': self.tagged_trait.pk}))

    def test_dcc_review_info(self):
        """A DCC analyst does see DCC review info on this detail page."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='dcc test comment'
        )
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertContains(response, dcc_review.get_status_display())
        self.assertContains(response, dcc_review.comment)


class TaggedTraitTagCountsByStudyTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitTagCountsByStudyTest, self).setUp()

    def make_fake_data(self):
        self.tags = factories.TagFactory.create_batch(2)
        self.studies = StudyFactory.create_batch(2)
        self.taggedtraits = []
        for tag in self.tags:
            for study in self.studies:
                self.taggedtraits.append(
                    factories.TaggedTraitFactory.create_batch(
                        2, tag=tag, trait__source_dataset__source_study_version__study=study)
                )

    def get_url(self, *args):
        return reverse('tags:tagged-traits:by-study')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('taggedtrait_tag_counts_by_study', context)

    def test_context_data_is_correct(self):
        """Data in the context is correct."""
        self.make_fake_data()
        response = self.client.get(self.get_url())
        context = response.context
        for study in context['taggedtrait_tag_counts_by_study']:
            for tag in study[1]:
                tag_study_count = models.TaggedTrait.objects.filter(
                    tag__pk=tag['tag_pk'],
                    trait__source_dataset__source_study_version__study__pk=study[0]['study_pk']).count()
                self.assertEqual(tag['tt_count'], tag_study_count)


class TaggedTraitStudyCountsByTagTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitStudyCountsByTagTest, self).setUp()

    def make_fake_data(self):
        self.tags = factories.TagFactory.create_batch(2)
        self.studies = StudyFactory.create_batch(2)
        self.taggedtraits = []
        for tag in self.tags:
            for study in self.studies:
                self.taggedtraits.append(
                    factories.TaggedTraitFactory.create_batch(
                        2, tag=tag, trait__source_dataset__source_study_version__study=study)
                )

    def get_url(self, *args):
        return reverse('tags:tagged-traits:by-tag')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('taggedtrait_study_counts_by_tag', context)

    def test_context_data_is_correct(self):
        """Data in the context is correct."""
        self.make_fake_data()
        response = self.client.get(self.get_url())
        context = response.context
        for tag in context['taggedtrait_study_counts_by_tag']:
            for study in tag[1]:
                study_tag_count = models.TaggedTrait.objects.filter(
                    tag__pk=tag[0]['tag_pk'],
                    trait__source_dataset__source_study_version__study__pk=study['study_pk']).count()
                self.assertEqual(study['tt_count'], study_tag_count)


class TaggedTraitByTagAndStudyListTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListTest, self).setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, tag=self.tag, trait__source_dataset__source_study_version__study=self.study)

    def get_url(self, *args):
        return reverse('tags:tag:study:list', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)

    def test_table_class(self):
        """For non-taggers, the tagged trait table class does not have delete buttons."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTable)

    def test_view_table_contains_correct_records(self):
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        table = context['tagged_trait_table']
        self.assertEqual(len(table.data), len(self.tagged_traits))
        for tagged_trait in self.tagged_traits:
            self.assertIn(tagged_trait, table.data, msg='tagged_trait_table does not contain {}'.format(tagged_trait))

    def test_view_works_with_no_tagged_traits_in_study(self):
        other_study = StudyFactory.create()
        other_tag = factories.TagFactory.create()
        response = self.client.get(self.get_url(other_tag.pk, other_study.pk))
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(len(context['tagged_trait_table'].data), 0)

    def test_view_does_not_show_tagged_traits_from_a_different_study(self):
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag, trait__source_dataset__source_study_version__study=other_study)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)

    def test_view_does_not_show_tagged_traits_from_a_different_tag(self):
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag, trait__source_dataset__source_study_version__study=self.study)
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertNotIn(other_tagged_trait, context['tagged_trait_table'].data)


class TaggedTraitByTagAndStudyListPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListPhenotypeTaggerTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study, tag=self.tag)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.study)

    def get_url(self, *args):
        return reverse('tags:tag:study:list', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the tag pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)

    def test_table_class(self):
        """For taggers, the tagged trait table class has delete buttons."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableWithDelete)


class TaggedTraitByTagAndStudyListDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitByTagAndStudyListDCCAnalystTest, self).setUp()
        self.study = StudyFactory.create()
        self.tag = factories.TagFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study, tag=self.tag)
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('tags:tag:study:list', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_study_pk(self):
        """View returns 404 response code when the study pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_view_with_invalid_tag_pk(self):
        """View returns 404 response code when the tag pk doesn't exist."""
        response = self.client.get(self.get_url(self.tag.pk + 1, self.study.pk))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tag', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)
        self.assertEqual(context['tag'], self.tag)

    def test_table_class(self):
        """For DCC Analysts, the tagged trait table class has delete buttons."""
        response = self.client.get(self.get_url(self.tag.pk, self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableWithDCCReview)


class TaggedTraitCreateTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertRedirects(response, reverse('tags:tag:detail', args=[new_object.tag.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_tags_traits_from_two_studies(self):
        """Correctly able to tag traits from two different studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        # Tag the two traits.
        response1 = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        response2 = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response1, self.tag.get_absolute_url())
        self.assertRedirects(response2, self.tag.get_absolute_url())
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in [self.trait.pk, trait2.pk]:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['trait'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)


class TaggedTraitCreateDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertRedirects(response, reverse('tags:tag:detail', args=[new_object.tag.pk]))
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['trait'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'trait': self.trait.pk, 'tag': self.tag.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_tag_other_study_trait(self):
        """Tagging a trait from another study works since the analyst doesn't have taggable_studies."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, })
        # View redirects to success url.
        self.assertRedirects(response, reverse('tags:tag:detail', args=[self.tag.pk]))
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)


class TaggedTraitDeleteTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitDeleteTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()
        self.tagged_trait = models.TaggedTrait.objects.create(trait=self.trait, tag=self.tag, creator=self.user)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:delete', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_deletes_object(self):
        """Posting 'submit' to the form correctly deletes the tagged_trait."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_deletes_object_tagged_by_other_user(self):
        """User can delete a tagged trait that was created by someone else from the same study."""
        trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        other_user = UserFactory.create()
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        other_user.groups.add(phenotype_taggers)
        other_user.profile.taggable_studies.add(self.study)
        other_user_tagged_trait = models.TaggedTrait.objects.create(trait=trait, tag=self.tag, creator=other_user)
        response = self.client.post(self.get_url(other_user_tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.study.pk]))
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            other_user_tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 1)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_post_anything_deletes_object(self):
        """Posting anything at all, even an empty dict, deletes the object."""
        # Is this really the behavior I want? I'm not sure...
        # Sounds like it might be:
        # https://stackoverflow.com/questions/17678689/how-to-add-a-cancel-button-to-deleteview-in-django
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_wrong_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_confirmed_tagged_trait_get_request_redirects_before_confirmation_view(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_cannot_delete_a_confirmed_trait(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_needs_followup_tagged_trait_get_request_redirects_before_confirmation_view(self):
        """Redirect when trying to delete a TaggedTrait that was reviewed with needs followup."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, comment='foo',
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_cannot_delete_a_reviewed_trait(self):
        """Cannot delete a TaggedTrait that was reviewed with needs followup."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, comment='foo',
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))


class TaggedTraitDeleteDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitDeleteDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()
        self.tagged_trait = models.TaggedTrait.objects.create(trait=self.trait, tag=self.tag, creator=self.user)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:delete', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.tagged_trait.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_deletes_object(self):
        """Posting 'submit' to the form correctly deletes the tagged_trait."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_post_anything_deletes_object(self):
        """Posting anything at all, even an empty dict, deletes the object."""
        # Is this really the behavior I want? I'm not sure...
        # Sounds like it might be:
        # https://stackoverflow.com/questions/17678689/how-to-add-a-cancel-button-to-deleteview-in-django
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        with self.assertRaises(models.TaggedTrait.DoesNotExist):
            self.tagged_trait.refresh_from_db()
        self.assertEqual(models.TaggedTrait.objects.count(), 0)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """DCC user can access the view even when they're not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """DCC user can access the view even with no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_cannot_delete_a_confirmed_trait(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_confirmed_tagged_trait_get_request_redirects_before_confirmation_view(self):
        """Cannot delete a TaggedTrait that has been confirmed by the DCC."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait,
                                                       status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_needs_followup_tagged_trait_get_request_redirects_before_confirmation_view(self):
        """Redirect when trying to delete a TaggedTrait that was reviewed with needs followup."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, comment='foo',
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))

    def test_cannot_delete_a_reviewed_trait(self):
        """Cannot delete a TaggedTrait that was reviewed with needs followup."""
        dcc_review = factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, comment='foo',
                                                       status=models.DCCReview.STATUS_FOLLOWUP)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {'submit': ''})
        self.assertRedirects(response, reverse('trait_browser:source:studies:pk:traits:tagged',
                                               args=[self.trait.source_dataset.source_study_version.study.pk]))
        # Make sure it wasn't deleted.
        self.assertIn(self.tagged_trait, models.TaggedTrait.objects.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn(views.REVIEWED_TAGGED_TRAIT_DELETE_ERROR_MESSAGE, str(messages[0]))


class TaggedTraitCreateByTagTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateByTagTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('tag' in context)
        self.assertEqual(context['tag'], self.tag)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        form_data = {'trait': self.trait.pk, }
        response = self.client.post(self.get_url(self.tag.pk), form_data)
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_tags_traits_from_two_studies(self):
        """Correctly able to tag traits from two different studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        # Tag the two traits.
        response1 = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        response2 = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response1, self.tag.get_absolute_url())
        self.assertRedirects(response2, self.tag.get_absolute_url())
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in [self.trait.pk, trait2.pk]:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('trait'))
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'trait': self.trait.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)


class TaggedTraitCreateByTagDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateByTagDCCAnalystTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-one:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)
        self.assertTrue('tag' in context)
        self.assertEqual(context['tag'], self.tag)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        form_data = {'trait': self.trait.pk, }
        response = self.client.post(self.get_url(self.tag.pk), form_data)
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.trait)
        self.assertIn(self.trait, self.tag.traits.all())
        self.assertIn(self.tag, self.trait.tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('trait'))
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'trait': self.trait.pk, })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_tag_other_study_trait(self):
        """DCC user can tag a trait even when it's not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, })
        # View redirects to success url.
        self.assertRedirects(response, reverse('tags:tag:detail', args=[self.tag.pk]))
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group_taggers(self):
        """DCC user can access the view even though they're not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """DCC user can access the view even without any taggable_studies."""
        self.user.profile.taggable_studies.remove(self.trait.source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)


class ManyTaggedTraitsCreateTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_single_trait(self):
        """Posting valid data to the form correctly tags a single trait."""
        this_trait = self.traits[0]
        form_data = {'traits': [this_trait.pk], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        tagged_trait = models.TaggedTrait.objects.get(trait=this_trait, tag=self.tag)
        self.assertIn(this_trait, self.tag.traits.all())
        self.assertIn(self.tag, this_trait.tag_set.all())

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(),
                                    {'traits': [str(t.pk) for t in some_traits], 'tag': self.tag.pk})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_creates_all_new_objects_from_multiple_studies(self):
        """Correctly tags traits from two different studies in the user's taggable_studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        more_traits = SourceTraitFactory.create_batch(2, source_dataset__source_study_version__study=study2)
        more_traits = self.traits[:2] + more_traits
        form_data = {'traits': [x.pk for x in more_traits], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'traits': '', 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_all_traits(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': [], 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)], 'tag': self.tag.pk})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(
            self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)


class ManyTaggedTraitsCreateDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateDCCAnalystTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, )
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:main')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_single_trait(self):
        """Posting valid data to the form correctly tags a single trait."""
        this_trait = self.traits[0]
        form_data = {'traits': [this_trait.pk], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        tagged_trait = models.TaggedTrait.objects.get(trait=this_trait, tag=self.tag)
        self.assertIn(this_trait, self.tag.traits.all())
        self.assertIn(self.tag, this_trait.tag_set.all())

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(),
                                    {'traits': [str(t.pk) for t in some_traits], 'tag': self.tag.pk})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'tag': self.tag.pk}
        response = self.client.post(self.get_url(), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'traits': '', 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_all_traits(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': [], 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)], 'tag': self.tag.pk})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_tag_other_study_traits(self):
        """DCC user can tag traits without any taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk, })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)


class ManyTaggedTraitsCreateByTagTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(self.traits[0].pk)]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.traits[0])
        self.assertIn(self.traits[0], self.tag.traits.all())
        self.assertIn(self.tag, self.traits[0].tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(t.pk) for t in some_traits]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(t.pk) for t in self.traits], })
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in self.traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects_from_multiple_studies(self):
        """Correctly tags traits from two different studies in the user's taggable_studies."""
        study2 = StudyFactory.create()
        self.user.profile.taggable_studies.add(study2)
        more_traits = SourceTraitFactory.create_batch(2, source_dataset__source_study_version__study=study2)
        more_traits = self.traits[:2] + more_traits
        form_data = {'traits': [x.pk for x in more_traits], }
        response = self.client.post(self.get_url(self.tag.pk), form_data)
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))
        # Correctly creates a tagged_trait for each trait.
        for trait_pk in form_data['traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(self.traits[0].pk)], })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged(self):
        """Tagging traits fails when two selected traits are already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_forbidden_non_taggers(self):
        """View returns 403 code when the user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_empty_taggable_studies(self):
        """View returns 403 code when the user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(
            self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 403)


class ManyTaggedTraitsCreateByTagDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagDCCAnalystTest, self).setUp()
        self.tag = factories.TagFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, )
        self.user.refresh_from_db()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:add-many:by-tag', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tag.pk))
        context = response.context
        self.assertTrue('form' in context)

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(self.traits[0].pk)]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertIsInstance(new_object, models.TaggedTrait)
        self.assertEqual(new_object.tag, self.tag)
        self.assertEqual(new_object.trait, self.traits[0])
        self.assertIn(self.traits[0], self.tag.traits.all())
        self.assertIn(self.tag, self.traits[0].tag_set.all())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(self.tag.pk), {'traits': [str(t.pk) for t in some_traits]})
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in some_traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_creates_all_new_objects(self):
        """Posting valid data to the form correctly tags all of the traits listed."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(t.pk) for t in self.traits], 'tag': self.tag.pk, })
        self.assertRedirects(response, self.tag.get_absolute_url())
        for trait in self.traits:
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
        new_objects = models.TaggedTrait.objects.all()
        for tt in new_objects:
            self.assertEqual(tt.tag, self.tag)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', })
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(self.traits[0].pk)], })
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_tag_other_study_traits(self):
        """DCC user can tag traits without any taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, })
        # Correctly goes to the tag's detail page and shows a success message.
        self.assertRedirects(response, self.tag.get_absolute_url())
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertFalse('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged(self):
        """Tagging traits fails when two selected traits are already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]], })
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_view_success_without_phenotype_taggers_group(self):
        """View is accessible even when the DCC user is not in phenotype_taggers."""
        phenotype_taggers = Group.objects.get(name='phenotype_taggers')
        self.user.groups.remove(phenotype_taggers)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_success_with_empty_taggable_studies(self):
        """View is accessible when the DCC user has no taggable_studies."""
        self.user.profile.taggable_studies.remove(self.traits[0].source_dataset.source_study_version.study)
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertEqual(response.status_code, 200)


class TaggedTraitReviewByTagAndStudySelectDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10,
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:select', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertTrue('form' in context)
        self.assertIsInstance(context['form'], forms.TaggedTraitReviewSelectForm)

    def test_post_blank_trait(self):
        """Posting bad data to the form shows a form error and doesn't set session variables."""
        response = self.client.post(self.get_url(), {'tag': '', 'study': ''})
        self.assertFormError(response, 'form', 'tag', 'This field is required.')
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_post_valid_form(self):
        """Posting valid data to the form sets session variables and redirects appropriately."""
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        # Check session variables.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))
        # The success url redirects again to a new page, so include the target_status_code argument.
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_session_variable_tagged_with_tag(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given tag."""
        other_tag = factories.TagFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_session_variable_tagged_with_study(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given study."""
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_session_variable_tagged_with_study_and_tag(self):
        """Posting valid data to the form sets tagged_trait_pks to only those from the given study and tag."""
        other_tag = factories.TagFactory.create()
        other_study = StudyFactory.create()
        other_tagged_trait = factories.TaggedTraitFactory.create(
            tag=other_tag,
            trait__source_dataset__source_study_version__study=other_study
        )
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} unexpectedly not in session tagged_trait_pks'.format(tt.pk))
        self.assertNotIn(other_tagged_trait, session_info['tagged_trait_pks'],
                         msg='TaggedTrait {} unexpectedly in session tagged_trait_pks'.format(tt.pk))

    def test_no_tagged_traits_with_study_and_tag(self):
        """Redirects to list view of no tagged traits for this study and tag."""
        study = StudyFactory.create()
        tag = factories.TagFactory.create()
        response = self.client.post(self.get_url(), {'tag': tag.pk, 'study': study.pk})
        self.assertEqual(response.status_code, 200)
        # Form errors.
        self.assertIn('form', response.context)
        self.assertFormError(response, 'form', None, forms.TaggedTraitReviewSelectForm.ERROR_NO_TAGGED_TRAITS)
        # Make sure no variables were set.
        session = self.client.session
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', session)

    def test_resets_session_variables(self):
        """A preexisting session variable is overwritten with new data upon successful form submission."""
        self.client.session['tagged_trait_review_by_tag_and_study_info'] = {
            'study_pk': self.study.pk + 1,
            'tag_pk': self.tag.pk + 1,
            'tagged_trait_pks': [],
        }
        self.client.session.save()
        response = self.client.post(self.get_url(), {'tag': self.tag.pk, 'study': self.study.pk})
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('study_pk', session_info)
        self.assertEqual(session_info['study_pk'], self.study.pk)
        self.assertIn('tag_pk', session_info)
        self.assertEqual(session_info['tag_pk'], self.tag.pk)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(len(session_info['tagged_trait_pks']), len(self.tagged_traits))
        for tt in self.tagged_traits:
            self.assertIn(tt.pk, session_info['tagged_trait_pks'],
                          msg='TaggedTrait {} not in session tagged_trait_pks'.format(tt.pk))

    def test_link_to_review_views(self):
        """The link to review tagged traits appears on the home page for DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitReviewByTagAndStudySelectDCCAnalystTest(TaggedTraitReviewByTagAndStudySelectDCCTestsMixin,
                                                         DCCAnalystLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudySelectDCCTestsMixin, as a DCC analyst.
    pass


class TaggedTraitReviewByTagAndStudySelectDCCDeveloperTest(TaggedTraitReviewByTagAndStudySelectDCCTestsMixin,
                                                           DCCDeveloperLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudySelectDCCTestsMixin, as a DCC developer.
    pass


class TaggedTraitReviewByTagAndStudySelectOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:select', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_link_not_in_navbar(self):
        """The link to review tagged traits doesn't appear on the home page for non-DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitReviewByTagAndStudyNextDCCTestsMixin(object):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:next', args=args)

    def test_view_success_with_no_session_variables(self):
        """View redirects correctly when no session variables are set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_view_success_with_tagged_traits_to_review(self):
        """View redirects correctly when there are tagged traits to review."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        response = self.client.get(self.get_url())
        # Make sure a pk session variable was set
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        self.assertIn('pk', session['tagged_trait_review_by_tag_and_study_info'])
        self.assertEqual(session['tagged_trait_review_by_tag_and_study_info']['pk'], tagged_trait.pk)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:review'))

    def test_view_success_with_no_tagged_traits_left(self):
        """View redirects correctly when no tagged traits are left to review."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tag:study:list', args=[tag.pk, study.pk]))

    def test_session_variables_are_unset_when_reviewing_completed(self):
        """View unsets session variables when no tagged traits are left to review."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [],
        }
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)

    def test_skips_tagged_trait_that_has_been_reviewed(self):
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits],
        }
        session.save()
        factories.DCCReviewFactory.create(tagged_trait=tagged_traits[0])
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_skips_deleted_tagged_trait(self):
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits],
        }
        session.save()
        # Now delete it and try loading the view.
        tagged_traits[0].delete()
        response = self.client.get(self.get_url())
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('tagged_trait_pks', session_info)
        self.assertEqual(session_info['tagged_trait_pks'], [tagged_traits[1].pk])
        self.assertNotIn('pk', session_info)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_session_variables_are_not_properly_set(self):
        """Redirects to select view if expected session variable is not set."""
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_required_keys(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        tag = factories.TagFactory.create()
        study = StudyFactory.create()
        tagged_traits = factories.TaggedTraitFactory.create_batch(
            2,
            tag=tag,
            trait__source_dataset__source_study_version__study=study
        )
        template = {
            'study_pk': study.pk,
            'tag_pk': tag.pk,
            'tagged_trait_pks': [x.pk for x in tagged_traits]
        }
        for key in template.keys():
            session_info = copy.copy(template)
            session_info.pop(key)
            session = self.client.session
            session['tagged_trait_review_by_tag_and_study_info'] = session_info
            session.save()
            response = self.client.get(self.get_url())
            self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
            self.assertRedirects(response, reverse('tags:tagged-traits:review:select'),
                                 msg_prefix='did not redirect when missing {} in session'.format(key))

    def test_continue_reviewing_link_in_navbar_if_session_variable_is_present(self):
        """The link to continue reviewing traits appears on the home page for DCC users if session variable exists."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<a href="{}">""".format(self.get_url()))

    def test_continue_reviewing_link_not_in_navbar_if_session_variable_is_missing(self):
        """The link to continue reviewing doesn't appear on the home page for DCC users if no session variable."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitReviewByTagAndStudyNextDCCAnalystTest(TaggedTraitReviewByTagAndStudyNextDCCTestsMixin,
                                                       DCCAnalystLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudyNextDCCTestsMixin, as a DCC analyst.
    pass


class TaggedTraitReviewByTagAndStudyNextDCCDeveloperTest(TaggedTraitReviewByTagAndStudyNextDCCTestsMixin,
                                                         DCCDeveloperLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudyNextDCCTestsMixin, as a DCC developer.
    pass


class TaggedTraitReviewByTagAndStudyNextOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:next', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_continue_reviewing_link_in_navbar_if_session_variable_is_present(self):
        """The link to continue reviewing traits doesn't appear on the home page for non-DCC users."""
        tagged_trait = factories.TaggedTraitFactory.create()
        tag = tagged_trait.tag
        study = tagged_trait.trait.source_dataset.source_study_version.study
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'tag_pk': tag.pk,
            'study_pk': study.pk,
            'tagged_trait_pks': [tagged_trait.pk],
        }
        session.save()
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitReviewByTagAndStudyDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tag = factories.TagFactory.create()
        self.study = StudyFactory.create()
        self.tagged_trait = factories.TaggedTraitFactory.create(
            tag=self.tag,
            trait__source_dataset__source_study_version__study=self.study
        )
        # Set expected session variables.
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'] = {
            'study_pk': self.study.pk,
            'tag_pk': self.tag.pk,
            'tagged_trait_pks': [self.tagged_trait.pk],
            'pk': self.tagged_trait.pk,
        }
        session.save()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:review', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], 1)

    def test_context_data_with_multiple_remaining_tagged_traits(self):
        """View has appropriate data in the context if there are multiple tagged traits to review."""
        session = self.client.session
        info = session['tagged_trait_review_by_tag_and_study_info']
        info['tagged_trait_pks'] = [self.tagged_trait.pk, self.tagged_trait.pk + 1]
        session.save()
        response = self.client.get(self.get_url())
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewByTagAndStudyForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)
        self.assertIn('tag', context)
        self.assertEqual(context['tag'], self.tag)
        self.assertIn('study', context)
        self.assertEqual(context['study'], self.study)
        self.assertIn('n_tagged_traits_remaining', context)
        self.assertEqual(context['n_tagged_traits_remaining'], 2)

    def test_successful_post_with_confirmed_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'foo'}
        response = self.client.post(self.get_url(), form_data)
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # The pk session variable is correctly unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))
        # Correctly redirects to the next view (remembering that it is a redirect view).
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_post_bad_data(self):
        """Posting bad data to the form shows a form error and doesn't unset session variables."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # The pk session variable is not unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertIn('pk', session_info)
        self.assertEqual(session_info['pk'], self.tagged_trait.pk)
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_skip_tagged_trait(self):
        """Skipping a TaggedTrait unsets pk and redirects to the next view."""
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_SKIP: 'Skip'}
        response = self.client.post(self.get_url(), form_data)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # Session variables are properly set/unset.
        session = self.client.session
        self.assertIn('tagged_trait_review_by_tag_and_study_info', session)
        session_info = session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # The redirect view unsets some session variables, so check it at the end.
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_non_existent_tagged_trait(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        self.tagged_trait.delete()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 404)

    def test_already_reviewed_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='a comment'
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_already_reviewed_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_CONFIRMED,
            comment=''
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_can_skip_already_reviewed_tagged_trait(self):
        """Redirects without a message if an already-reviewed tagged trait is skipped."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_CONFIRMED,
            comment=''
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewByTagAndStudyForm.SUBMIT_SKIP: 'Skip', 'comment': ''}
        response = self.client.post(self.get_url(), form_data)
        # Check session variables.
        self.assertIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        session_info = self.client.session['tagged_trait_review_by_tag_and_study_info']
        self.assertNotIn('pk', session_info)
        self.assertIn('tagged_trait_pks', session_info)
        self.assertNotIn(self.tagged_trait.pk, session_info['tagged_trait_pks'])
        # Check that no message was generated.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_session_variables_are_not_properly_set_with_get_request(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variables_are_not_properly_set_with_post_request(self):
        """Redirects to select view if expected session variable is not set."""
        session = self.client.session
        del session['tagged_trait_review_by_tag_and_study_info']
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_tag_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_study_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_tagged_trait_pks_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.get(self.get_url())
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_pk_with_get_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.get(self.get_url())
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)

    def test_session_variable_missing_key_tag_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tag_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_study_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('study_pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_tagged_trait_pks_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('tagged_trait_pks')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertNotIn('tagged_trait_review_by_tag_and_study_info', self.client.session)
        self.assertRedirects(response, reverse('tags:tagged-traits:review:select'))

    def test_session_variable_missing_key_pk_with_post_request(self):
        """Redirects to select view if expected session variable dictionary keys are missing."""
        session = self.client.session
        session['tagged_trait_review_by_tag_and_study_info'].pop('pk')
        session.save()
        response = self.client.post(self.get_url(), {})
        self.assertRedirects(response, reverse('tags:tagged-traits:review:next'), target_status_code=302)


class TaggedTraitReviewByTagAndStudyDCCAnalystTest(TaggedTraitReviewByTagAndStudyDCCTestsMixin,
                                                   DCCAnalystLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudyDCCTestsMixin, as a DCC analyst.
    pass


class TaggedTraitReviewByTagAndStudyDCCDeveloperTest(TaggedTraitReviewByTagAndStudyDCCTestsMixin,
                                                     DCCDeveloperLoginTestCase):

    # Run all tests in TaggedTraitReviewByTagAndStudyDCCTestsMixin, as a DCC developer.
    pass


class TaggedTraitReviewByTagAndStudyOtherUserTest(UserLoginTestCase):

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:review:review', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(), {})
        self.assertEqual(response.status_code, 403)

    def test_link_not_in_navbar(self):
        """The link to continue reviewing traits doesn't appear on the home page for non-DCC users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, """<a href="{}">""".format(self.get_url()))


class TaggedTraitReviewDCCTestsMixin(object):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:review:new', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 200)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], forms.DCCReviewForm)
        self.assertIn('tagged_trait', context)
        self.assertEqual(context['tagged_trait'], self.tagged_trait)

    def test_successful_post_with_confirmed_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_successful_post_with_needs_followup_tagged_trait(self):
        """Posting valid data to the form correctly creates a DCCReview."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': 'foo'}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Correctly creates a DCCReview for this TaggedTrait.
        dcc_review = models.DCCReview.objects.all().latest('created')
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)
        # Check for success message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Successfully reviewed', str(messages[0]))

    def test_post_bad_data(self):
        """Posting bad data to the form shows a form error."""
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Require study followup', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertEqual(response.status_code, 200)
        # Does not create a DCCReview for this TaggedTrait.
        self.assertFalse(hasattr(self.tagged_trait, 'dcc_review'))
        # No messages.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)

    def test_get_non_existent_tagged_trait(self):
        """Returns a 404 page with a get request if the tagged trai doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_non_existent_tagged_trait(self):
        """Returns a 404 page if the session varaible pk doesn't exist."""
        url = self.get_url(self.tagged_trait.pk)
        self.tagged_trait.delete()
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 404)

    def test_get_already_reviewed_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='a comment'
        )
        # Now try to review it through the web interface.
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)

    def test_post_already_reviewed_tagged_trait(self):
        """Shows warning message and does not save review if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='a comment'
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewForm.SUBMIT_CONFIRM: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)

    def test_post_already_reviewed_tagged_trait_with_form_error(self):
        """Shows warning message and redirects if TaggedTrait is already reviewed."""
        dcc_review = factories.DCCReviewFactory.create(
            tagged_trait=self.tagged_trait,
            status=models.DCCReview.STATUS_FOLLOWUP,
            comment='a comment'
        )
        # Now try to review it through the web interface.
        form_data = {forms.DCCReviewForm.SUBMIT_FOLLOWUP: 'Confirm', 'comment': ''}
        response = self.client.post(self.get_url(self.tagged_trait.pk), form_data)
        self.assertRedirects(response, self.tagged_trait.get_absolute_url())
        # Check for warning message.
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('already been reviewed', str(messages[0]))
        # The previous DCCReview was not updated.
        self.assertEqual(self.tagged_trait.dcc_review, dcc_review)


class TaggedTraitReviewDCCAnalystTest(TaggedTraitReviewDCCTestsMixin, DCCAnalystLoginTestCase):

    # Run all tests in TaggedTraitReviewDCCTestsMixin, as a DCC analyst.
    pass


class TaggedTraitReviewDCCDeveloperTest(TaggedTraitReviewDCCTestsMixin, DCCDeveloperLoginTestCase):

    # Run all tests in TaggedTraitReviewDCCTestsMixin, as a DCC developer.
    pass


class TaggedTraitReviewOtherUserTest(UserLoginTestCase):

    def setUp(self):
        super().setUp()
        self.tagged_trait = factories.TaggedTraitFactory.create()

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:pk:review:new', args=args)

    def test_forbidden_get_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)

    def test_forbidden_get_request_with_existing_review(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.get(self.get_url(self.tagged_trait.pk))
        self.assertEqual(response.status_code, 403)

    def test_forbidden_post_request_with_existing_review(self):
        """Returns a response with a forbidden status code for non-DCC users."""
        factories.DCCReviewFactory.create(tagged_trait=self.tagged_trait, status=models.DCCReview.STATUS_CONFIRMED)
        response = self.client.post(self.get_url(self.tagged_trait.pk), {})
        self.assertEqual(response.status_code, 403)


class TagsLoginRequiredTest(LoginRequiredTestCase):

    def test_tags_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('tags')


class TagAutocompleteTest(UserLoginTestCase):
    """Autocomplete view works as expected."""

    def setUp(self):
        super(TagAutocompleteTest, self).setUp()
        self.tags = factories.TagFactory.create_batch(10)

    def get_url(self, *args):
        return reverse('tags:autocomplete')

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)

    def test_returns_all_traits(self):
        """Queryset returns all of the tags with no query (when there are 10, which is the page limit)."""
        url = self.get_url()
        response = self.client.get(url)
        pks = get_autocomplete_view_ids(response)
        self.assertEqual(sorted([tag.pk for tag in self.tags]), sorted(pks))

    def test_proper_tag_in_queryset(self):
        """Queryset returns only the proper tag by title."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_upper_case(self):
        """Queryset returns only the proper tag by title when query is in upper case."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title.upper()})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_lower_case(self):
        """Queryset returns only the proper tag by title when query is in lower case."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title.lower()})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) == 1)
        self.assertEqual(tag.pk, pks[0])

    def test_proper_tag_in_queryset_partial_query(self):
        """The results contain the desired trait when a single letter is used for the query."""
        tag = self.tags[0]
        response = self.client.get(self.get_url(), {'q': tag.title[0]})
        pks = get_autocomplete_view_ids(response)
        self.assertTrue(len(pks) >= 1)
        self.assertIn(tag.pk, pks)
