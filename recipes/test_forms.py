"""Test the functions and classes from forms.py, especially the custom validation."""

from django.test import TestCase
from django.core.urlresolvers import reverse

from .forms import HarmonizationRecipeForm, UnitRecipeForm
from .factories import HarmonizationRecipeFactory, UnitRecipeFactory
from .models import HarmonizationRecipe
from core.factories import UserFactory
from trait_browser.factories import SourceTraitFactory


class UnitRecipeFormTestCase(TestCase):
    
    def test_form_with_valid_input(self):
        """Test that the UnitRecipeForm is valid with valid input data and a valid user set on the form."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_no_input(self):
        """Test that the UnitRecipeForm is not bound when it's not given input data."""
        form = UnitRecipeForm()
        self.assertFalse(form.is_bound)
    
    def test_form_without_optional_input(self):
        """Test that the UnitRecipeForm is valid when given input that does not include optional fields."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_blank_name_is_invalid(self):
        """Test that a blank input for the name field makes the UnitRecipeForm not valid, and gives an error on the name field."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())
        
    def test_form_with_blank_instructions_is_invalid(self):
        """Test that a blank input for the instructions field makes the UnitRecipeForm not valid, and gives an error on the instructions field."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('instructions'))
        self.assertFalse(form.is_valid())

    def test_form_with_blank_age_variables_is_invalid(self):
        """Test that a blank input for the age variables field makes the UnitRecipeForm not valid, and gives an error on the age_variables field."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_blank_phenotype_variables_is_invalid(self):
        """Test that a blank input for the phenotype variables field makes the UnitRecipeForm not valid, and gives an error on the phenotype_variables field."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_nonunique_name_for_user_is_invalid(self):
        """Test that a name that already exists for the user makes the UnitRecipeForm invalid, and gives an error."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        user = UserFactory.create()
        unit_recipe1 = UnitRecipeFactory.create(creator=user)
        input = {'name': unit_recipe1.name,
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_batch_and_phenotype_is_invalid(self):
        """Test that the UnitRecipeForm is invalid if a trait is included as all three kinds of variable."""
        source_trait = SourceTraitFactory.create()
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait.pk), ] ,
                 'batch_variables': [str(source_trait.pk), ] ,
                 'phenotype_variables': [str(source_trait.pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_batch_is_invalid(self):
        """Test that the UnitRecipeForm is invalid if a trait is included as age variable and batch variable."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[0].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertFalse(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_phenotype_is_invalid(self):
        """Test that the UnitRecipeForm is invalid if a trait is included as age variable and phenotype variable."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[1].pk), ] ,
                 'phenotype_variables': [str(source_traits[0].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_phenotype_and_batch_is_invalid(self):
        """Test that the UnitRecipeForm is invalid if a trait is included as phenotype variable and batch variable."""
        source_traits = SourceTraitFactory.create_batch(3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ] ,
                 'batch_variables': [str(source_traits[2].pk), ] ,
                 'phenotype_variables': [str(source_traits[2].pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertFalse(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_traits_from_multiple_global_studies_is_invalid(self):
        """Test that the UnitRecipeForm is invalid if the variables included are from multiple global studies."""
        source_trait1 = SourceTraitFactory.create(source_dataset__source_study_version__study__global_study__i_id=1)
        source_trait2 = SourceTraitFactory.create(source_dataset__source_study_version__study__global_study__i_id=2)
        source_trait3 = SourceTraitFactory.create(source_dataset__source_study_version__study__global_study__i_id=3)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait1.pk), ] ,
                 'batch_variables': [str(source_trait2.pk), ] ,
                 'phenotype_variables': [str(source_trait3.pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_traits_from_multiple_global_studies_is_invalid_when_batch_variables_blank(self):
        """Test that the UnitRecipeForm is invalid if the variables included are from multiple global studies."""
        source_trait1 = SourceTraitFactory.create(source_dataset__source_study_version__study__global_study__i_id=1)
        source_trait3 = SourceTraitFactory.create(source_dataset__source_study_version__study__global_study__i_id=3)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait1.pk), ] ,
                 'phenotype_variables': [str(source_trait3.pk), ] ,
                 }
        form = UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())


class HarmonizationRecipeFormTestCase(TestCase):
    
    def test_form_with_valid_input_type_unit_recode(self):
        """Test that the HarmonizationRecipeForm is valid with good input data and type=UNIT_RECODE."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.UNIT_RECODE,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_valid_input_type_category_recode(self):
        """Test that the HarmonizationRecipeForm is valid with good input data and type=CATEGORY_RECODE."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.CATEGORY_RECODE,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_valid_input_type_formula(self):
        """Test that the HarmonizationRecipeForm is valid with good input data and type=FORMULA."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.FORMULA,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_valid_input_type_other(self):
        """Test that the HarmonizationRecipeForm is valid with good input data and type=OTHER."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_no_input(self):
        """Test that the HarmonizationRecipeForm is not bound when it's not given input data."""
        form = HarmonizationRecipeForm()
        self.assertFalse(form.is_bound)
    
    def test_form_without_optional_input_is_valid(self):
        """Test that the HarmonizationRecipeForm is valid when given input that does not include optional fields."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())
    
    def test_form_with_missing_name_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid when name is not submitted."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())
    
    def test_form_with_missing_units_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid if no harmonization units are selected."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('units'))
        self.assertFalse(form.is_valid())
    
    def test_form_with_missing_target_name_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid if target_name is not submitted."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_description': 'This is a test variable.',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())
    
    def test_form_with_missing_target_description_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid if target description is not submitted."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('target_description'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_type_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid if the type field is not submitted."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('type'))
        self.assertFalse(form.is_valid())
    
    def test_form_with_missing_measurement_unit_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid if a measurement unit is not submitted."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'type': HarmonizationRecipe.OTHER,
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('measurement_unit'))
        self.assertFalse(form.is_valid())

    def test_form_with_nonunique_name_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid with a name that is nonunique for the user."""
        user = UserFactory.create()
        harm_recipe = HarmonizationRecipeFactory.create(creator=user)
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': harm_recipe.name,
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_bad_encoded_values_format_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid when the encoded values input is not formatted properly."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1:blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('encoded_values'))
        self.assertFalse(form.is_valid())

    def test_form_is_valid_with_encoded_values_including_spaces(self):
        """Test that the HarmonizationRecipeForm is valid when the encoded values (category and value) contain spaces."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': 'non smoker: this person is a non-smoker\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_bad_type_value_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid when the input type value is invalid."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': 'not_a_type',
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('type'))
        self.assertFalse(form.is_valid())
        
    def test_form_with_spaces_in_target_name_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid when target_name contains spaces."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'Bad Variable Name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())

    def test_form_with_special_character_in_target_name_is_invalid(self):
        """Test that the HarmonizationRecipeForm is invalid when target_name contains special characters."""
        user = UserFactory.create()
        unit_recipes = UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'Bad Variable Name @#!$',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'type': HarmonizationRecipe.OTHER,
                 'measurement_unit': 'kilograms',
                 }
        form = HarmonizationRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())