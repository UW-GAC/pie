"""Test the functions and classes from forms.py, especially the custom validation."""

from django.test import TestCase

from core.factories import UserFactory
import trait_browser.factories

from . import forms
from . import factories
from . import models


class UnitRecipeFormTest(TestCase):

    def test_form_with_valid_input_type_other(self):
        """The UnitRecipeForm is valid with valid input data and a valid user set on the form."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_valid_input_type_unit_recode(self):
        """The UnitRecipeForm is valid with valid input data and a valid user set on the form."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.UNIT_RECODE,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_valid_input_type_category_recode(self):
        """The UnitRecipeForm is valid with valid input data and a valid user set on the form."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.CATEGORY_RECODE,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_valid_input_type_formula(self):
        """The UnitRecipeForm is valid with valid input data and a valid user set on the form."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.FORMULA,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_no_input(self):
        """The UnitRecipeForm is not bound when it's not given input data."""
        form = forms.UnitRecipeForm()
        self.assertFalse(form.is_bound)

    def test_form_without_optional_input(self):
        """The UnitRecipeForm is valid when given input that does not include optional fields."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.is_valid())

    def test_form_with_blank_name_is_invalid(self):
        """Blank name field invalidates the form, and gives an error on the name field."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_blank_instructions_is_invalid(self):
        """Blank instructions field invalidates the form, and gives an error on the instructions field."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('instructions'))
        self.assertFalse(form.is_valid())

    def test_form_with_blank_age_variables_is_invalid(self):
        """Blank age variables field invalidates the form, and gives an error on the age_variables field."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_blank_phenotype_variables_is_invalid(self):
        """Blank phenotype variables field invalidates the form, and gives an error on phenotype_variables field."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_nonunique_name_for_user_is_invalid(self):
        """A name that already exists for the user makes the UnitRecipeForm invalid, and gives an error."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        user = UserFactory.create()
        unit_recipe1 = factories.UnitRecipeFactory.create(creator=user)
        input = {'name': unit_recipe1.name,
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form.user = user
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_batch_and_phenotype_is_invalid(self):
        """The UnitRecipeForm is invalid if a trait is included as all three kinds of variable."""
        source_trait = trait_browser.factories.SourceTraitFactory.create()
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait.pk), ],
                 'batch_variables': [str(source_trait.pk), ],
                 'phenotype_variables': [str(source_trait.pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_batch_is_invalid(self):
        """The UnitRecipeForm is invalid if a trait is included as age variable and batch variable."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[0].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertFalse(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_age_and_phenotype_is_invalid(self):
        """The UnitRecipeForm is invalid if a trait is included as age variable and phenotype variable."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[0].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_trait_in_phenotype_and_batch_is_invalid(self):
        """The UnitRecipeForm is invalid if a trait is included as phenotype variable and batch variable."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[2].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertFalse(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_traits_from_multiple_global_studies_is_invalid(self):
        """The UnitRecipeForm is invalid if the variables included are from multiple global studies."""
        source_trait1 = trait_browser.factories.SourceTraitFactory.create(
            source_dataset__source_study_version__study__global_study__i_id=1)
        source_trait2 = trait_browser.factories.SourceTraitFactory.create(
            source_dataset__source_study_version__study__global_study__i_id=2)
        source_trait3 = trait_browser.factories.SourceTraitFactory.create(
            source_dataset__source_study_version__study__global_study__i_id=3)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait1.pk), ],
                 'batch_variables': [str(source_trait2.pk), ],
                 'phenotype_variables': [str(source_trait3.pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_traits_from_multiple_global_studies_is_invalid_when_batch_variables_blank(self):
        """The UnitRecipeForm is invalid if the variables included are from multiple global studies."""
        source_trait1 = trait_browser.factories.SourceTraitFactory.create(
            source_dataset__source_study_version__study__global_study__i_id=1)
        source_trait3 = trait_browser.factories.SourceTraitFactory.create(
            source_dataset__source_study_version__study__global_study__i_id=3)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_trait1.pk), ],
                 'phenotype_variables': [str(source_trait3.pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('age_variables'))
        self.assertFalse(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_type_is_invalid(self):
        """The UnitRecipeForm is invalid if the type field is not submitted."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('type'))
        self.assertFalse(form.is_valid())

    def test_form_with_bad_type_value_is_invalid(self):
        """The HarmonizationRecipeForm is invalid when the input type value is invalid."""
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Example study name, subcohort 5.',
                 'instructions': 'Do something to combine these variables',
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[1].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': 'not_a_type',
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('type'))
        self.assertFalse(form.is_valid())

    def test_form_with_harmonized_phenotype_variable_is_valid(self):
        """Form is valid when given harmonized phenotype variables, but none of the source trait variables."""
        harmonized_trait = trait_browser.factories.HarmonizedTraitFactory.create()
        input = {'name': 'Only one unit here.',
                 'instructions': 'Do something to combine these variables',
                 'harmonized_phenotype_variables': [str(harmonized_trait.pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertFalse(form.has_error('phenotype_variables'))
        self.assertTrue(form.is_valid())

    def test_form_with_harmonized_and_unharmonized_phenotype_variables_is_invalid(self):
        """Form is invalid when given harmonized phenotype variables, but some of the source trait variables."""
        harmonized_trait = trait_browser.factories.HarmonizedTraitFactory.create()
        source_traits = trait_browser.factories.SourceTraitFactory.create_batch(
            3, source_dataset__source_study_version__study__global_study__i_id=1)
        input = {'name': 'Only one unit here.',
                 'instructions': 'Do something to combine these variables',
                 'harmonized_phenotype_variables': [str(harmonized_trait.pk), ],
                 'age_variables': [str(source_traits[0].pk), ],
                 'batch_variables': [str(source_traits[0].pk), ],
                 'phenotype_variables': [str(source_traits[2].pk), ],
                 'type': models.UnitRecipe.OTHER,
                 }
        form = forms.UnitRecipeForm(input)
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        user = UserFactory.create()
        form.user = user
        self.assertTrue(form.has_error('phenotype_variables'))
        self.assertTrue(form.has_error('age_variables'))
        self.assertTrue(form.has_error('batch_variables'))
        self.assertTrue(form.has_error('harmonized_phenotype_variables'))
        self.assertFalse(form.is_valid())


class HarmonizationRecipeFormTest(TestCase):

    def test_form_with_valid_input(self):
        """The HarmonizationRecipeForm is valid with good input data."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.is_valid())

    def test_form_with_no_input(self):
        """The HarmonizationRecipeForm is not bound when it's not given input data."""
        form = forms.HarmonizationRecipeForm()
        self.assertFalse(form.is_bound)

    def test_form_without_optional_input_is_valid(self):
        """The HarmonizationRecipeForm is valid when given input that does not include optional fields."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.is_valid())

    def test_form_with_missing_name_is_invalid(self):
        """The HarmonizationRecipeForm is invalid when name is not submitted."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_units_is_invalid(self):
        """The HarmonizationRecipeForm is invalid if no harmonization units are selected."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('units'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_target_name_is_invalid(self):
        """The HarmonizationRecipeForm is invalid if target_name is not submitted."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_description': 'This is a test variable.',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_target_description_is_invalid(self):
        """The HarmonizationRecipeForm is invalid if target description is not submitted."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('target_description'))
        self.assertFalse(form.is_valid())

    def test_form_with_missing_measurement_unit_is_invalid(self):
        """The HarmonizationRecipeForm is invalid if a measurement unit is not submitted."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('measurement_unit'))
        self.assertFalse(form.is_valid())

    def test_form_with_nonunique_name_is_invalid(self):
        """The HarmonizationRecipeForm is invalid with a name that is nonunique for the user."""
        user = UserFactory.create()
        harm_recipe = factories.HarmonizationRecipeFactory.create(creator=user)
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': harm_recipe.name,
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('name'))
        self.assertFalse(form.is_valid())

    def test_form_with_bad_encoded_values_format_is_invalid(self):
        """The HarmonizationRecipeForm is invalid when the encoded values input is not formatted properly."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1:blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('encoded_values'))
        self.assertFalse(form.is_valid())

    def test_form_is_valid_with_encoded_values_including_spaces(self):
        """The HarmonizationRecipeForm is valid when the encoded values (category and value) contain spaces."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': 'non smoker: this person is a non-smoker\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.is_valid())

    def test_form_with_spaces_in_target_name_is_invalid(self):
        """The HarmonizationRecipeForm is invalid when target_name contains spaces."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'Bad Variable Name',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())

    def test_form_with_special_character_in_target_name_is_invalid(self):
        """The HarmonizationRecipeForm is invalid when target_name contains special characters."""
        user = UserFactory.create()
        unit_recipes = factories.UnitRecipeFactory.create_batch(5, creator=user)
        input = {'name': 'Harmonization of this specific trait here.',
                 'units': [str(u.pk) for u in unit_recipes],
                 'target_name': 'Bad Variable Name @#!$',
                 'target_description': 'This is a test variable.',
                 'encoded_values': '1: blue\r\n2: red\r\n3: yellow',
                 'measurement_unit': 'kilograms',
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('target_name'))
        self.assertFalse(form.is_valid())

    def test_form_with_units_from_other_user_is_invalid(self):
        """The HarmonizationRecipeForm is invalid if harmonization units from another user are selected."""
        user = UserFactory.create()
        user2 = UserFactory.create()
        user_units = factories.UnitRecipeFactory.create_batch(2, creator=user)
        user2_units = factories.UnitRecipeFactory.create_batch(2, creator=user2)
        input = {'name': 'Harmonization of this specific trait here.',
                 'target_name': 'test_variable_name',
                 'target_description': 'This is a test variable.',
                 'measurement_unit': 'kilograms',
                 'units': [str(u.pk) for u in user_units + user2_units],
                 }
        # Usually form.user is added by a mixin on the View, but have to add it manually here.
        form = forms.HarmonizationRecipeForm(input, user=user)
        self.assertTrue(form.has_error('units'))
        self.assertFalse(form.is_valid())
