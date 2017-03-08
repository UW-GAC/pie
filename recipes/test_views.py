"""Test the functions and classes for recipes.views."""

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from core.utils import ViewsAutoLoginTestCase, LoginRequiredTestCase
from core.factories import UserFactory, USER_FACTORY_PASSWORD
from recipes.urls import urlpatterns
from trait_browser.factories import SourceTraitFactory

from .factories import HarmonizationRecipeFactory, UnitRecipeFactory
from .models import HarmonizationRecipe, UnitRecipe
from .views import CreateHarmonizationRecipe, UpdateHarmonizationRecipe, HarmonizationRecipeDetail
from .views import CreateUnitRecipe, UpdateUnitRecipe, UnitRecipeDetail


class UnitRecipeViewsTestCase(ViewsAutoLoginTestCase):
    
    def test_create_unit_recipe(self):
        """Test that CreateUnitRecipe view can be navigated to."""
        url = reverse('recipes:unit:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_unit_recipe_creates_new_object(self):
        """Test that CreateUnitRecipe view creates a new UnitRecipe and redirects to its detail page."""
        new_unit_name = 'Example study name, subcohort 5.'
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': new_unit_name,
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 'type': UnitRecipe.UNIT_RECODE
                 }
        url = reverse('recipes:unit:create')
        response = self.client.post(url, input)
        new_unit = UnitRecipe.objects.filter(name=new_unit_name)
        self.assertTrue(len(new_unit) == 1)
        new_unit = new_unit[0]
        self.assertIsInstance(new_unit.pk, int)
        self.assertRedirects(response, new_unit.get_absolute_url())
        
    def test_update_unit_recipe(self):
        """Test that UpdateUnitRecipe view can be navigated to."""
        new_recipe = UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_update_unit_recipe_changes_object(self):
        """Test that UpdateUnitRecipe view updates the name field."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        new_unit = UnitRecipeFactory.create(creator=self.user,
                                            age_variables=[source_traits[0]],
                                            batch_variables=[source_traits[1]],
                                            phenotype_variables=[source_traits[2]]
                                            )
        url = reverse('recipes:unit:edit', kwargs={'pk': new_unit.pk})
        edited_name = 'Hi ho there, Kermit the frog here.'
        input = {'name': edited_name,
                 'instructions': new_unit.instructions,
                 'age_variables': [str(v.pk) for v in new_unit.age_variables.all()],
                 'batch_variables': [str(v.pk) for v in new_unit.batch_variables.all()] ,
                 'phenotype_variables': [str(v.pk) for v in new_unit.phenotype_variables.all()],
                 'type': UnitRecipe.OTHER,
                 }
        response = self.client.post(url, input)
        # self.assertRedirects(response, new_unit.get_absolute_url())
        new_unit.refresh_from_db()
        self.assertEqual(new_unit.name, edited_name)
        
    def test_update_unit_recipe_cannot_edit_other_user_recipes(self):
        """Test that a user cannot access UpdateUnitRecipe view for another user's saved unit recipe."""
        user2 = UserFactory.create()
        unit2 = UnitRecipeFactory.create(creator=user2)
        url = reverse('recipes:unit:edit', kwargs={'pk': unit2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        login = self.client.login(username=user2.email, password=USER_FACTORY_PASSWORD)
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_unit_recipe_error_on_invalid_pk(self):
        """Test that the UpdateUnitRecipe view gives an error when given an invalid pk."""
        url = reverse('recipes:unit:edit', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_unit_recipe_detail(self):
        """Test that the UnitRecipeDetail view is viewable for a valid pk."""
        new_recipe = UnitRecipeFactory.create(creator=self.user)
        url = reverse('recipes:unit:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_unit_recipe_detail_error_for_other_user_recipes(self):
        """Test that a user cannot view detail pages for other users' UnitRecipes."""
        user2 = UserFactory.create()
        unit2 = UnitRecipeFactory.create(creator=user2)
        url = reverse('recipes:unit:detail', kwargs={'pk': unit2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        login = self.client.login(username=user2.email, password=USER_FACTORY_PASSWORD)
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unit_recipe_detail_error_for_invalid_pk(self):
        """Test that the UnitRecipeDetail view gives an error for an invalid pk."""
        url = reverse('recipes:unit:detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class HarmonizationRecipeViewsTestCase(ViewsAutoLoginTestCase):
    
    def test_create_harmonization_recipe(self):
        """Test that CreateHarmonizationRecipe view can be navigated to."""
        url = reverse('recipes:harmonization:create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_harmonization_recipe_creates_new_object(self):
        """Test that CreateHarmonizationRecipe view creates a new HarmonizationRecipe and redirects to its detail page."""
        new_harmonization_name = 'Harmonization of BMI across all time points.'
        units = UnitRecipeFactory.create_batch(3, creator=self.user)
        input = {'name': new_harmonization_name,
                 'units': [str(u.pk) for u in units],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        url = reverse('recipes:harmonization:create')
        response = self.client.post(url, input)
        new_harmonization = HarmonizationRecipe.objects.filter(name=new_harmonization_name)
        self.assertTrue(len(new_harmonization) == 1)
        new_harmonization = new_harmonization[0]
        self.assertIsInstance(new_harmonization.pk, int)
        self.assertRedirects(response, new_harmonization.get_absolute_url())
        
    def test_update_harmonization_recipe(self):
        """Test that UpdateHarmonizationRecipe view can be navigated to."""
        new_recipe = HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_update_harmonization_recipe_changes_object(self):
        """Test that UpdateHarmonizationRecipe view updates the name field."""
        units = UnitRecipeFactory.create_batch(3, creator=self.user)
        new_harmonization = HarmonizationRecipeFactory.create(creator=self.user, units=units)
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
        
    def test_update_harmonization_recipe_cannot_edit_other_user_recipes(self):
        """Test that a user cannot access UpdateHarmonizationRecipe view for another user's saved harmonization recipe."""
        user2 = UserFactory.create()
        harmonization2 = HarmonizationRecipeFactory.create(creator=user2)
        url = reverse('recipes:harmonization:edit', kwargs={'pk': harmonization2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        login = self.client.login(username=user2.email, password=USER_FACTORY_PASSWORD)
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_harmonization_recipe_error_on_invalid_pk(self):
        """Test that the UpdateHarmonizationRecipe view gives an error when given an invalid pk."""
        url = reverse('recipes:harmonization:edit', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_harmonization_recipe_detail(self):
        """Test that the HarmonizationRecipeDetail view is viewable for a valid pk."""
        new_recipe = HarmonizationRecipeFactory.create(creator=self.user)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': new_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_harmonization_recipe_detail_error_for_other_user_recipes(self):
        """Test that a user cannot view detail pages for other users' HarmonizationRecipes."""
        user2 = UserFactory.create()
        harmonization2 = HarmonizationRecipeFactory.create(creator=user2)
        url = reverse('recipes:harmonization:detail', kwargs={'pk': harmonization2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()
        login = self.client.login(username=user2.email, password=USER_FACTORY_PASSWORD)
        response=self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_harmonization_recipe_detail_error_for_invalid_pk(self):
        """Test that the UnitRecipeDetail view gives an error for an invalid pk."""
        url = reverse('recipes:harmonization:detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class RecipesLoginRequiredTestCase(LoginRequiredTestCase):
    
    def test_recipes_login_required(self):
        """All recipes urls redirect to login page if no user is logged in."""
        self.assert_redirect_all_urls(urlpatterns, 'recipe')
