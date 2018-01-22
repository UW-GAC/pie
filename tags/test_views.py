"""Tests of views in the tags app."""

from faker import Faker

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from core.utils import (LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase,
                        DCCAnalystLoginTestCase, get_autocomplete_view_ids)
from profiles.models import Profile
from trait_browser.factories import SourceTraitFactory, StudyFactory
from trait_browser.models import SourceTrait
from . import factories
from . import models
from . import tables

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
        self.assertIn('tagged_trait_table', context)
        self.assertIsInstance(context['tagged_trait_table'], tables.TagDetailTraitTable)

    def test_no_tagging_button(self):
        """Regular user does not see a button to add tags on this detail page."""
        response = self.client.get(self.get_url(self.tag.pk))
        self.assertNotContains(response, 'Tag phenotypes as "{}"'.format(self.tag.title))


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
        self.assertContains(response, 'Tag phenotypes as "{}"'.format(self.tag.title))


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


class StudyTaggedTraitListTest(UserLoginTestCase):

    def setUp(self):
        super(StudyTaggedTraitListTest, self).setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(20)

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
        self.assertTrue('study_table' in context)
        self.assertIsInstance(context['study_table'], tables.StudyTaggedTraitTable)


class TaggedTraitByStudyListTest(UserLoginTestCase):

    def setUp(self):
        super(TaggedTraitByStudyListTest, self).setUp()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:study:tagged', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)

    def test_table_class(self):
        """For non-taggers, the tagged trait table class does not have delete buttons."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTable)


class TaggedTraitByStudyListPhenotypeTaggerTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitByStudyListPhenotypeTaggerTest, self).setUp()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()
        self.user.profile.taggable_studies.add(self.study)

    def get_url(self, *args):
        return reverse('trait_browser:source:study:tagged', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)

    def test_table_class(self):
        """For taggers, the tagged trait table class has delete buttons."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableWithDelete)


class TaggedTraitByStudyListDCCAnalystTest(DCCAnalystLoginTestCase):

    def setUp(self):
        super(TaggedTraitByStudyListDCCAnalystTest, self).setUp()
        self.study = StudyFactory.create()
        self.tagged_traits = factories.TaggedTraitFactory.create_batch(
            10, trait__source_dataset__source_study_version__study=self.study)
        self.user.refresh_from_db()

    def get_url(self, *args):
        return reverse('trait_browser:source:study:tagged', args=args)

    def test_view_success_code(self):
        """View returns successful response code."""
        response = self.client.get(self.get_url(self.study.pk))
        self.assertEqual(response.status_code, 200)

    def test_view_with_invalid_pk(self):
        """View returns 404 response code when the pk doesn't exist."""
        response = self.client.get(self.get_url(self.study.pk + 1))
        self.assertEqual(response.status_code, 404)

    def test_context_data(self):
        """View has appropriate data in the context."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIn('study', context)
        self.assertIn('tagged_trait_table', context)
        self.assertEqual(context['study'], self.study)

    def test_table_class(self):
        """For taggers, the tagged trait table class has delete buttons."""
        response = self.client.get(self.get_url(self.study.pk))
        context = response.context
        self.assertIsInstance(context['tagged_trait_table'], tables.TaggedTraitTableWithDelete)


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
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False})
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
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'trait': '', 'tag': self.tag.pk, 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertEqual(form['trait'].errors, [u'This field is required.'])
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(), {'trait': trait2.pk, 'tag': self.tag.pk, 'recommended': False})
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(), {'trait': self.trait.pk, 'tag': self.tag.pk, 'recommended': False})
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


class TaggedTraitDeleteTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitDeleteTest, self).setUp()
        self.trait = SourceTraitFactory.create(source_dataset__source_study_version__study=self.study)
        self.tag = factories.TagFactory.create()
        self.user.refresh_from_db()
        self.tagged_trait = models.TaggedTrait.objects.create(
            trait=self.trait, tag=self.tag, creator=self.user, recommended=False)

    def get_url(self, *args):
        """Get the url for the view this class is supposed to test."""
        return reverse('tags:tagged-traits:delete', args=args)

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
        self.assertRedirects(response, reverse('trait_browser:source:study:tagged',
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
        self.assertRedirects(response, reverse('trait_browser:source:study:tagged',
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
        form_data = {'trait': self.trait.pk, 'recommended': False}
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
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'trait': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('trait'))
        self.assertNotIn(self.tag, self.trait.tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'trait': self.trait.pk, 'recommended': False})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_trait(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': trait2.pk, 'recommended': False})
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_trait_is_already_tagged(self):
        """Tagging a trait fails when the trait has already been tagged with this tag."""
        tagged_trait = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.trait)
        response = self.client.post(self.get_url(self.tag.pk), {'trait': self.trait.pk, 'recommended': False})
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
        form_data = {'traits': [this_trait.pk], 'recommended_traits': [],
                     'tag': self.tag.pk}
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
        self.assertFalse(tagged_trait.recommended)

    def test_creates_single_recommended_trait(self):
        """Posting valid data to the form correctly tags a single recommended trait."""
        this_trait = self.traits[0]
        form_data = {'traits': [], 'recommended_traits': [this_trait.pk],
                     'tag': self.tag.pk}
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
        self.assertTrue(tagged_trait.recommended)

    def test_creates_two_new_objects(self):
        """Posting valid data to the form correctly tags two traits."""
        # Check on redirection to detail page, M2M links, and creation message.
        some_traits = self.traits[:2]
        response = self.client.post(self.get_url(),
                                    {'traits': [str(t.pk) for t in some_traits],
                                     'tag': self.tag.pk, 'recommended': False})
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
        form_data = {'traits': [x.pk for x in self.traits[0:5]], 'recommended_traits': [x.pk for x in self.traits[5:]],
                     'tag': self.tag.pk}
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
            self.assertFalse(tagged_trait.recommended)
        # Correctly creates a tagged_trait with recommended = True for each trait in recommended_traits.
        for trait_pk in form_data['recommended_traits']:
            trait = SourceTrait.objects.get(pk=trait_pk)
            tagged_trait = models.TaggedTrait.objects.get(trait__pk=trait_pk, tag=self.tag)
            self.assertIn(trait, self.tag.traits.all())
            self.assertIn(self.tag, trait.tag_set.all())
            self.assertTrue(tagged_trait.recommended)

    def test_invalid_form_message(self):
        """Posting invalid data results in a message about the invalidity."""
        response = self.client.post(self.get_url(), {'traits': '', 'recommended_traits': [], 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_all_traits(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': [], 'recommended_traits': [], 'tag': self.tag.pk})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertTrue(form.has_error('recommended_traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)], 'recommended_traits': [],
                                     'tag': self.tag.pk})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk,
                                     'recommended_traits': []})
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_with_repeated_trait(self):
        """Tagging traits fails when a trait is repeated in 'traits' and 'recommended_traits'."""
        response = self.client.post(self.get_url(),
                                    {'traits': [self.traits[0].pk], 'tag': self.tag.pk,
                                     'recommended_traits': [self.traits[0].pk]})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk,
                                     'recommended_traits': [self.traits[-1].pk]})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged(self):
        """Tagging traits fails when two selected traits are already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1])
        response = self.client.post(self.get_url(),
                                    {'traits': [t.pk for t in self.traits[0:5]], 'tag': self.tag.pk,
                                     'recommended_traits': [self.traits[-1].pk]})
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
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(self.traits[0].pk)], 'recommended': False})
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
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(t.pk) for t in some_traits], 'recommended': False})
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
                                    {'traits': [str(t.pk) for t in self.traits],
                                     'tag': self.tag.pk, 'recommended': False})
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
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '', 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(self.traits[0].pk)], 'recommended': False})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)

    def test_fails_with_other_study_traits(self):
        """Tagging a trait fails when the trait is not in the user's taggable_studies'."""
        study2 = StudyFactory.create()
        traits2 = SourceTraitFactory.create_batch(5, source_dataset__source_study_version__study=study2)
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [str(x.pk) for x in traits2], 'tag': self.tag.pk, 'recommended': False})
        # They have taggable studies and they're in the phenotype_taggers group, so view is still accessible.
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_with_repeated_trait(self):
        """Tagging traits fails when a trait is repeated in 'traits' and 'recommended_traits'."""
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [self.traits[0].pk], 'recommended_traits': [self.traits[0].pk]})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_one_trait_is_already_tagged(self):
        """Tagging traits fails when a selected trait is already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]],
                                     'recommended_traits': [self.traits[-1].pk]})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_fails_when_two_traits_are_already_tagged(self):
        """Tagging traits fails when two selected traits are already tagged with the tag."""
        already_tagged = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[0])
        already_tagged2 = factories.TaggedTraitFactory.create(tag=self.tag, trait=self.traits[1])
        response = self.client.post(self.get_url(self.tag.pk),
                                    {'traits': [t.pk for t in self.traits[0:5]],
                                     'recommended_traits': [self.traits[-1].pk]})
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


class TagsLoginRequiredTestCase(LoginRequiredTestCase):

    def test_recipes_login_required(self):
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