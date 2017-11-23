"""Tests of views in the tags app."""

from faker import Faker

from django.core.urlresolvers import reverse

from core.utils import LoginRequiredTestCase, PhenotypeTaggerLoginTestCase, UserLoginTestCase
from core.factories import UserFactory
from profiles.models import UserData
from trait_browser.factories import SourceTraitFactory, StudyFactory
from . import factories
from . import forms
from . import models
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
        self.assertTrue('tag' in context)
        self.assertIsInstance(context['tag'], models.Tag)


class TaggedTraitCreateTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(self.trait.source_dataset.source_study_version.study)

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


class TaggedTraitCreateByTagTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(TaggedTraitCreateByTagTest, self).setUp()
        self.trait = SourceTraitFactory.create()
        self.tag = factories.TagFactory.create()
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(self.trait.source_dataset.source_study_version.study)

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


class ManyTaggedTraitsCreateTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=study)
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(study)

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

    def test_creates_new_object(self):
        """Posting valid data to the form correctly tags a single trait."""
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)],
                                     'tag': self.tag.pk, 'recommended': False})
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
        # Check on redirection to detail page, M2M links, and creation message.
        response = self.client.post(self.get_url(),
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
        response = self.client.post(self.get_url(), {'traits': '', 'tag': self.tag.pk, 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))

    def test_post_blank_trait(self):
        """Posting bad data to the form doesn't tag the trait and shows a form error."""
        response = self.client.post(self.get_url(), {'traits': '', 'tag': self.tag.pk, 'recommended': False})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertTrue('Oops!' in str(messages[0]))
        form = response.context['form']
        self.assertTrue(form.has_error('traits'))
        self.assertNotIn(self.tag, self.traits[0].tag_set.all())

    def test_adds_user(self):
        """When a trait is successfully tagged, it has the appropriate creator."""
        response = self.client.post(self.get_url(),
                                    {'traits': [str(self.traits[0].pk)],
                                     'tag': self.tag.pk, 'recommended': False})
        new_object = models.TaggedTrait.objects.latest('pk')
        self.assertEqual(self.user, new_object.creator)


class ManyTaggedTraitsCreateByTagTest(PhenotypeTaggerLoginTestCase):

    def setUp(self):
        super(ManyTaggedTraitsCreateByTagTest, self).setUp()
        self.tag = factories.TagFactory.create()
        study = StudyFactory.create()
        self.traits = SourceTraitFactory.create_batch(10, source_dataset__source_study_version__study=study)
        UserData.objects.create(user=self.user)
        self.user.refresh_from_db()
        self.user.userdata_set.first().taggable_studies.add(study)

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
                                    {'traits': [str(self.traits[0].pk)],'recommended': False})
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
        response = self.client.post(self.get_url(self.tag.pk), {'traits': '','recommended': False})
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


class TagsLoginRequiredTestCase(LoginRequiredTestCase):

    def test_recipes_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('tags')
