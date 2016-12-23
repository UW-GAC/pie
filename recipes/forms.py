"""Form classes for the trait_browser app."""

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete

from .models import UnitRecipe, HarmonizationRecipe


class UnitRecipeForm(forms.ModelForm):
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

    def get_model_name(self):
        """ """
        return self.instance._meta.verbose_name


class HarmonizationRecipeForm(forms.ModelForm):
    """Form to create/edit HarmonizationRecipe objects."""
    
    def __init__(self, *args, **kwargs):
        super(HarmonizationRecipeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('Save', 'Save'))
        
    class Meta:
        model = HarmonizationRecipe
        fields = ('name', 'target_name', 'target_description', 'units', 'category_description', )
        widgets = {'units': autocomplete.ModelSelect2Multiple(url='recipes:unit_autocomplete'), }
    
    def get_model_name(self):
        """ """
        return self.instance._meta.verbose_name