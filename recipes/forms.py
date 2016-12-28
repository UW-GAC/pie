"""Form classes for the trait_browser app."""

from django import forms

from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete

from .models import UnitRecipe, HarmonizationRecipe


class UnitRecipeForm(UserKwargModelFormMixin, forms.ModelForm):
    """Form to create/edit UnitRecipe model objects."""
    
    def __init__(self, *args, **kwargs):
        super(UnitRecipeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('Save', 'Save'))
        
    class Meta:
        model = UnitRecipe
        fields = ('name', 'age_variables', 'batch_variables', 'phenotype_variables', 'instructions', )
        widgets = {'age_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source_autocomplete'),
            'batch_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source_autocomplete'),
            'phenotype_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source_autocomplete'),
        }
        help_texts = {'name': 'A unique and informative name for the harmonization unit.',
            'age_variables': 'Enter the DCC id(s) of the variable(s) needed to derive age for your harmonized variable <strong>in this harmonization unit</strong>.',
            'batch_variables': 'Enter the DCC id(s) of the variable(s) needed to derive a harmonized batch variable <strong>in this harmonization unit</strong>. (optional)',
            'phenotype_variables': 'Enter the DCC id(s) of the variable(s) needed to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
            'instructions': 'Describe how to use the age variables to derive age, how to use the batch variables to derive a harmonized batch, and how to use the phenotype variables to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
        }

    def clean(self):
        cleaned_data = super(UnitRecipeForm, self).clean()
        name = cleaned_data.get('name', '')
        existing_names_for_user = [u.name for u in self.user.units_created_by.all()]
        if name in existing_names_for_user:
            del cleaned_data['name']
            self.add_error('name', forms.ValidationError(u'A harmonization unit named {} already exists for user {}.'.format(name, self.user.username)))
        return cleaned_data
    
    def get_model_name(self):
        """ """
        return self.instance._meta.verbose_name


class HarmonizationRecipeForm(UserKwargModelFormMixin, forms.ModelForm):
    """Form to create/edit HarmonizationRecipe objects."""
    
    def __init__(self, *args, **kwargs):
        super(HarmonizationRecipeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('Save', 'Save'))
        
    class Meta:
        model = HarmonizationRecipe
        fields = ('name', 'target_name', 'target_description', 'measurement_unit', 'type', 'units', 'encoded_values', )
        # widgets = {'units': autocomplete.ModelSelect2Multiple(url='recipes:unit_autocomplete'), }
        help_texts = {
            'name': 'A unique and informative name for your harmonization recipe.',
            'target_name': 'A short and informative name for your harmonized variable. Only letters, numbers, and underscores allowed.',
            'target_description': 'A detailed description of your harmonized variable. This description will appear in documentation and data dictionaries.',
            'measurement_unit': 'The units of measurement for your target harmonized variable.',
            'type': 'The general type of harmonization required to produce your target variable.',
            'units': 'The harmonization units to include in your target harmonized variable.',
            'encoded_values': 'Values and descriptions for encoded values for your target harmonized variable. Define one encoded value per line, separating the value from its description with a semicolon and a single space.<br>Example:<br>1: blue<br>2: red<br>3: green',
        }
        
    def clean(self):
        cleaned_data = super(HarmonizationRecipeForm, self).clean()
        name = cleaned_data.get('name', '')
        existing_names_for_user = [u.name for u in self.user.harmonization_recipes_created_by.all()]
        if name in existing_names_for_user:
            del cleaned_data['name']
            self.add_error('name', forms.ValidationError(u'A harmonization unit named {} already exists for user {}.'.format(name, self.user.username)))
        return cleaned_data

    def get_model_name(self):
        """ """
        return self.instance._meta.verbose_name