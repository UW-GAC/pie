"""Test the functions and classes for recipes.views."""

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

import core.utils
from core.factories import UserFactory, SuperUserFactory, USER_FACTORY_PASSWORD
from trait_browser.factories import SourceTraitFactory

from . import factories
from . import models


class UnitRecipeViewsTestCase(core.utils.RecipeSubmitterLoginTestCase):

    def test_create_unit_recipe(self):
        """The CreateUnitRecipe view can be navigated to."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_unit_recipe_creates_new_object(self):
        """The CreateUnitRecipe view creates a new UnitRecipe and redirects to its detail page."""
        new_unit_name = 'Example study name, subcohort 5.'
        source_traits = SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': new_unit_name,
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.UNIT_RECODE
                 }
        url = reverse('recipes:unit:create')
        response = self.client.post(url, input)
        new_unit = models.UnitRecipe.objects.filter(name=new_unit_name)
        self.assertTrue(len(new_unit) == 1)
        new_unit = new_unit[0]
        self.assertIsInstance(new_unit.pk, int)
        self.assertRedirects(response, new_unit.get_absolute_url())

    def test_update_unit_recipe(self):
        """The UpdateUnitRecipe view can be navigated to."""
        new_recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_unit_recipe_changes_object(self):
        """The UpdateUnitRecipe view updates the name field."""
        source_traits = SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        new_unit = factories.UnitRecipeFactory.create(
            creator=self.user, age_variables=[source_traits[0]], batch_variables=[source_traits[1]],
            phenotype_variables=[source_traits[2]])
        url = reverse('recipes:unit:edit', kwargs={'pk': new_unit.pk})
        edited_name = 'Hi ho there, Kermit the frog here.'
        input = {'name': edited_name,
                 'instructions': new_unit.instructions,
                 'age_variables': [str(v.pk) for v in new_unit.age_variables.all()],
                 'batch_variables': [str(v.pk) for v in new_unit.batch_variables.all()],
                 'phenotype_variables': [str(v.pk) for v in new_unit.phenotype_variables.all()],
                 'type': models.UnitRecipe.OTHER,
                 }
        response = self.client.post(url, input)
        # self.assertRedirects(response, new_unit.get_absolute_url())
        new_unit.refresh_from_db()
        self.assertEqual(new_unit.name, edited_name)

    def test_update_unit_recipe_error_on_invalid_pk(self):
        """The UpdateUnitRecipe view gives an error when given an invalid pk."""
        url = reverse('recipes:unit:edit', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unit_recipe_detail(self):
        """The UnitRecipeDetail view is viewable for a valid pk."""
        new_recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_recipe_detail_error_for_invalid_pk(self):
        """The UnitRecipeDetail view gives an error for an invalid pk."""
        url = reverse('recipes:unit:detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unit_recipe_detail_error_for_other_user_recipes(self):
        """A user cannot view detail pages for other users' UnitRecipes."""
        new_recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A different recipe_submitter cannot view the page.
        submitter = UserFactory.create()
        submitter.groups.add(Group.objects.get(name='recipe_submitters'))
        self.client.logout()
        self.client.login(username=submitter.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # A dcc_analyst can view the page.
        analyst = UserFactory.create(is_staff=True)
        analyst.groups.add(Group.objects.get(name='dcc_analysts'))
        self.client.logout()
        self.client.login(username=analyst.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A dcc_developer cannot view the page.
        developer = UserFactory.create(is_staff=True)
        developer.groups.add(Group.objects.get(name='dcc_developers'))
        self.client.logout()
        self.client.login(username=developer.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A superuser cannot view the page.
        superuser = SuperUserFactory.create(is_staff=True)
        self.client.logout()
        self.client.login(username=superuser.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_unit_recipe_cannot_edit_other_user_recipes(self):
        """A user cannot access UpdateUnitRecipe view for another user's saved unit recipe."""
        new_recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A different recipe_submitter cannot view the page.
        submitter = UserFactory.create()
        submitter.groups.add(Group.objects.get(name='recipe_submitters'))
        self.client.logout()
        self.client.login(username=submitter.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # A dcc_analyst cannot view the page.
        analyst = UserFactory.create(is_staff=True)
        analyst.groups.add(Group.objects.get(name='dcc_analysts'))
        self.client.logout()
        self.client.login(username=analyst.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A dcc_developer cannot view the page.
        developer = UserFactory.create(is_staff=True)
        developer.groups.add(Group.objects.get(name='dcc_developers'))
        self.client.logout()
        self.client.login(username=developer.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A superuser cannot view the page.
        superuser = SuperUserFactory.create(is_staff=True)
        self.client.logout()
        self.client.login(username=superuser.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class HarmonizationRecipeViewsTestCase(core.utils.RecipeSubmitterLoginTestCase):

    def test_create_harmonization_recipe(self):
        """The CreateHarmonizationRecipe view can be navigated to."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_harmonization_recipe_creates_new_object(self):
        """The CreateHarmonizationRecipe view creates a new HarmonizationRecipe and redirects to its detail page."""
        new_harmonization_name = 'Harmonization of BMI across all time points.'
        units = factories.UnitRecipeFactory.create_batch(3, creator=self.user)
        input = {'name': new_harmonization_name,
                 'units': [str(u.pk) for u in units],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        url = reverse('recipes:harmonization:create')
        response = self.client.post(url, input)
        new_harmonization = models.HarmonizationRecipe.objects.filter(name=new_harmonization_name)
        self.assertTrue(len(new_harmonization) == 1)
        new_harmonization = new_harmonization[0]
        self.assertIsInstance(new_harmonization.pk, int)
        self.assertRedirects(response, new_harmonization.get_absolute_url())

    def test_update_harmonization_recipe(self):
        """The UpdateHarmonizationRecipe view can be navigated to."""
        new_recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_harmonization_recipe_changes_object(self):
        """The UpdateHarmonizationRecipe view updates the name field."""
        units = factories.UnitRecipeFactory.create_batch(3, creator=self.user)
        new_harmonization = factories.HarmonizationRecipeFactory.create(creator=self.user, units=units)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': new_harmonization.pk})
        edited_name = 'Hi ho there, Kermit the frog here.'
        input = {'name': edited_name,
                 'units': [str(u.pk) for u in new_harmonization.units.all()],
                 'target_name': new_harmonization.target_name,
                 'target_description': new_harmonization.target_description,
                 'encoded_values': new_harmonization.encoded_values,
                 'measurement_unit': new_harmonization.measurement_unit,
                 }
        response = self.client.post(url, input)
        # self.assertRedirects(response, new_harmonization.get_absolute_url())
        new_harmonization.refresh_from_db()
        self.assertEqual(new_harmonization.name, edited_name)

    def test_update_harmonization_recipe_error_on_invalid_pk(self):
        """The UpdateHarmonizationRecipe view gives an error when given an invalid pk."""
        url = reverse('recipes:harmonization:edit', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_harmonization_recipe_detail(self):
        """The HarmonizationRecipeDetail view is viewable for a valid pk."""
        new_recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_recipe_detail_error_for_invalid_pk(self):
        """The UnitRecipeDetail view gives an error for an invalid pk."""
        url = reverse('recipes:harmonization:detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_harmonization_recipe_detail_error_for_other_user_recipes(self):
        """A user cannot view detail pages for other users' HarmonizationRecipes."""
        new_recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A different recipe_submitter cannot view the page.
        submitter = UserFactory.create()
        submitter.groups.add(Group.objects.get(name='recipe_submitters'))
        self.client.logout()
        self.client.login(username=submitter.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # A dcc_analyst can view the page.
        analyst = UserFactory.create(is_staff=True)
        analyst.groups.add(Group.objects.get(name='dcc_analysts'))
        self.client.logout()
        self.client.login(username=analyst.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A dcc_developer can view the page.
        developer = UserFactory.create(is_staff=True)
        developer.groups.add(Group.objects.get(name='dcc_developers'))
        self.client.logout()
        self.client.login(username=developer.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A superuser can view the page.
        superuser = SuperUserFactory.create(is_staff=True)
        self.client.logout()
        self.client.login(username=superuser.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_harmonization_recipe_cannot_edit_other_user_recipes(self):
        """A user cannot access UpdateHarmonizationRecipe view for another user's saved unit recipe."""
        new_recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A different recipe_submitter cannot view the page.
        submitter = UserFactory.create()
        submitter.groups.add(Group.objects.get(name='recipe_submitters'))
        self.client.logout()
        self.client.login(username=submitter.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # A dcc_analyst can view the page.
        analyst = UserFactory.create(is_staff=True)
        analyst.groups.add(Group.objects.get(name='dcc_analysts'))
        self.client.logout()
        self.client.login(username=analyst.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A dcc_developer can view the page.
        developer = UserFactory.create(is_staff=True)
        developer.groups.add(Group.objects.get(name='dcc_developers'))
        self.client.logout()
        self.client.login(username=developer.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # A superuser can view the page.
        superuser = SuperUserFactory.create(is_staff=True)
        self.client.logout()
        self.client.login(username=superuser.email, password=USER_FACTORY_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class GrouplessUserRecipeViewsTest(core.utils.UserLoginTestCase):

    def test_unit_create_forbidden_to_groupless(self):
        """The CreateUnitRecipe view can't be accessed by groupless users."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_harmonization_create_forbidden_to_groupless(self):
        """The CreateHarmonizationRecipe view can't be accessed by groupless users."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_unit_edit_forbidden_to_groupless(self):
        """The UpdateUnitRecipe view can't be accessed by groupless users."""
        recipe = factories.UnitRecipeFactory.create()
        url = reverse('recipes:unit:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_harmonization_edit_forbidden_to_groupless(self):
        """The UpdateHarmonizationRecipe view can't be accessed by groupless users."""
        recipe = factories.HarmonizationRecipeFactory.create()
        url = reverse('recipes:harmonization:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_unit_detail_forbidden_to_groupless(self):
        """The UnitRecipeDetail view can't be accessed by groupless users."""
        recipe = factories.UnitRecipeFactory.create()
        url = reverse('recipes:unit:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_harmonization_detail_forbidden_to_groupless(self):
        """The HarmonizationRecipeDetail view can't be accessed by groupless users."""
        recipe = factories.HarmonizationRecipeFactory.create()
        url = reverse('recipes:harmonization:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_recipes_not_on_homepage(self):
        """The harmonization recipe elements don't appear on the home page for groupless users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<h2>Submit a harmonization recipe</h2>', html=True)
        self.assertNotContains(response,
                               """<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button"
                               aria-haspopup="true" aria-expanded="false">Harmonization recipes
                               <span class="caret"></span></a>""",
                               html=True)

    def test_recipes_not_on_profile_page(self):
        """The harmonization recipe tabs don't appear on the profile page for groupless users."""
        url = reverse('profiles:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            '<li role="presentation"><a href="#unitrecipes" role="tab" data-toggle="tab">Unit Recipes</a></li>',
            html=True)
        self.assertNotContains(
            response,
            '<li role="presentation"><a href="#harmonizationrecipes" role="tab" data-toggle="tab">Harmonization Recipes</a></li>',  # noqa: E501
            html=True)


class DCCAnalystRecipeViewsTest(core.utils.DCCAnalystLoginTestCase):

    def test_unit_create_viewable_to_groupless(self):
        """The CreateUnitRecipe view can be accessed by dcc_analysts users.."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_create_viewable_to_groupless(self):
        """The CreateHarmonizationRecipe view can be accessed by dcc_analysts users.."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_edit_viewable_to_groupless(self):
        """The UpdateUnitRecipe view can be accessed by dcc_analysts users.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_edit_viewable_to_groupless(self):
        """The UpdateHarmonizationRecipe view can be accessed by dcc_analysts users.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_viewable_to_groupless(self):
        """The UnitRecipeDetail view can be accessed by dcc_analysts users.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_detail_viewable_to_groupless(self):
        """The HarmonizationRecipeDetail view can be accessed by dcc_analysts users.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recipes_on_homepage(self):
        """The harmonization recipe elements don't appear on the home page for DCC analyst users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Submit a harmonization recipe</h2>', html=True)
        self.assertContains(response,
                            """<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button"
                            aria-haspopup="true" aria-expanded="false">Harmonization recipes
                            <span class="caret"></span></a>""",
                            html=True)

    def test_recipes_on_profile_page(self):
        """The harmonization recipe tabs don't appear on the profile page for DCC analyst users."""
        url = reverse('profiles:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#unitrecipes" role="tab" data-toggle="tab">Unit Recipes</a></li>',
            html=True)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#harmonizationrecipes" role="tab" data-toggle="tab">Harmonization Recipes</a></li>',  # noqa: E501
            html=True)


class DCCDeveloperRecipeViewsTest(core.utils.DCCDeveloperLoginTestCase):

    def test_unit_create_viewable_to_groupless(self):
        """The CreateUnitRecipe view can be accessed by dcc_developers users.."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_create_viewable_to_groupless(self):
        """The CreateHarmonizationRecipe view can be accessed by dcc_developers users.."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_edit_viewable_to_groupless(self):
        """The UpdateUnitRecipe view can be accessed by dcc_developers users.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_edit_viewable_to_groupless(self):
        """The UpdateHarmonizationRecipe view can be accessed by dcc_developers users.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_viewable_to_groupless(self):
        """The UnitRecipeDetail view can be accessed by dcc_developers users.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_detail_viewable_to_groupless(self):
        """The HarmonizationRecipeDetail view can be accessed by dcc_developers users.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recipes_on_homepage(self):
        """The harmonization recipe elements don't appear on the home page for DCC developer users."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Submit a harmonization recipe</h2>', html=True)
        self.assertContains(response,
                            """<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button"
                            aria-haspopup="true" aria-expanded="false">Harmonization recipes
                            <span class="caret"></span></a>""",
                            html=True)

    def test_recipes_on_profile_page(self):
        """The harmonization recipe tabs don't appear on the profile page for DCC developer users."""
        url = reverse('profiles:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#unitrecipes" role="tab" data-toggle="tab">Unit Recipes</a></li>',
            html=True)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#harmonizationrecipes" role="tab" data-toggle="tab">Harmonization Recipes</a></li>',  # noqa: E501
            html=True)


class SuperuserRecipeViewsTest(core.utils.SuperuserLoginTestCase):

    def test_unit_create_viewable_to_groupless(self):
        """The CreateUnitRecipe view can be accessed by superusers.."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_create_viewable_to_groupless(self):
        """The CreateHarmonizationRecipe view can be accessed by superusers.."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_edit_viewable_to_groupless(self):
        """The UpdateUnitRecipe view can be accessed by superusers.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_edit_viewable_to_groupless(self):
        """The UpdateHarmonizationRecipe view can be accessed by superusers.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_detail_viewable_to_groupless(self):
        """The UnitRecipeDetail view can be accessed by superusers.."""
        recipe = factories.UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_detail_viewable_to_groupless(self):
        """The HarmonizationRecipeDetail view can be accessed by superusers.."""
        recipe = factories.HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recipes_on_homepage(self):
        """The harmonization recipe elements don't appear on the home page for superusers."""
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Submit a harmonization recipe</h2>', html=True)
        self.assertContains(response,
                            """<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button"
                            aria-haspopup="true" aria-expanded="false">Harmonization recipes
                            <span class="caret"></span></a>""",
                            html=True)

    def test_recipes_on_profile_page(self):
        """The harmonization recipe tabs don't appear on the profile page for superusers."""
        url = reverse('profiles:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#unitrecipes" role="tab" data-toggle="tab">Unit Recipes</a></li>',
            html=True)
        self.assertContains(
            response,
            '<li role="presentation"><a href="#harmonizationrecipes" role="tab" data-toggle="tab">Harmonization Recipes</a></li>',  # noqa: E501
            html=True)


class RecipesLoginRequiredTestCase(core.utils.LoginRequiredTestCase):

    def test_recipes_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls('recipes')
