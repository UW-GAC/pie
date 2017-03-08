"""Form classes for the trait_browser app."""

from django import forms

from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete

from .models import UnitRecipe, HarmonizationRecipe


# UnitRecipe form classes.
class UnitRecipeCleanMixin(object):
    """Mixin containing a clean method for UnitRecipe ModelForms.
    
    All ModelForms based on UnitRecipe should be able to use this clean method.
    If there are specific cleaning tasks that only apply to some forms, they
    should be added to forms on an individual basis.
    """
    def clean(self):
        """Custom form field validation for UnitRecipeForm."""
        cleaned_data = super(UnitRecipeCleanMixin, self).clean()
        # Check that traits are not repeated in the several variable fields.
        age = cleaned_data.get('age_variables', [])
        batch = cleaned_data.get('batch_variables', [])
        phenotype = cleaned_data.get('phenotype_variables', [])
        # Check for overlap between age and batch variables.
        age_batch = set(age) & set(batch)
        if len(age_batch) > 0:
            age_batch_error = forms.ValidationError(u'Variable(s) {} repeated as an age variable and as a batch variable. This is not allowed.'.format(' and '.join([str(v.i_trait_id) for v in age_batch])))
            self.add_error('age_variables', age_batch_error)
            self.add_error('batch_variables', age_batch_error)
        # Check for overlap between phenotype and batch variables.
        phenotype_batch = set(phenotype) & set(batch)
        if len(phenotype_batch) > 0:
            phenotype_batch_error = forms.ValidationError(u'Variable(s) {} repeated as a phenotype variable and as a batch variable. This is not allowed.'.format(' and '.join([str(v.i_trait_id) for v in phenotype_batch])))
            self.add_error('phenotype_variables', phenotype_batch_error)
            self.add_error('batch_variables', phenotype_batch_error)
        # Check for overlap between age and phenotype variables.
        age_phenotype = set(age) & set(phenotype)
        if len(age_phenotype) > 0:
            age_phenotype_error = forms.ValidationError(u'Variable(s) {} repeated as an age variable and as a phenotype variable. This is not allowed.'.format(' and '.join([str(v.i_trait_id) for v in age_phenotype])))
            self.add_error('age_variables', age_phenotype_error)
            self.add_error('phenotype_variables', age_phenotype_error)
        # Check that all variables used are from the same GlobalStudy.
        global_studies = [trait.source_dataset.source_study_version.study.global_study for trait in list(age) + list(batch) + list(phenotype)]
        if len(set(global_studies)) > 1:
            study_error = forms.ValidationError(u'Variables selected are from more than one TOPMed study. This is not allowed.')
            blank_error = forms.ValidationError(u'')
            self.add_error('age_variables', blank_error)
            if len(batch) > 0:
                self.add_error('batch_variables', blank_error)
            self.add_error('phenotype_variables', blank_error)
            raise forms.ValidationError(study_error)
        return cleaned_data


class UnitRecipeForm(UserKwargModelFormMixin, UnitRecipeCleanMixin, forms.ModelForm):
    """Form to create/edit UnitRecipe model objects."""
    
    def __init__(self, *args, **kwargs):
        super(UnitRecipeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('Save', 'Save'))
        
    class Meta:
        model = UnitRecipe
        fields = ('name', 'age_variables', 'batch_variables', 'phenotype_variables', 'type', 'instructions', )
        widgets = {'age_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
            'batch_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
            'phenotype_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
        }
        help_texts = {'name': 'A unique and informative name for the harmonization unit.',
            'age_variables': 'Enter the DCC id(s) of the variable(s) needed to derive age for your harmonized variable <strong>in this harmonization unit</strong>.',
            'batch_variables': 'Enter the DCC id(s) of the variable(s) needed to derive a harmonized batch variable <strong>in this harmonization unit</strong>. (optional)',
            'phenotype_variables': 'Enter the DCC id(s) of the variable(s) needed to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
            'instructions': 'Describe how to use the age variables to derive age, how to use the batch variables to derive a harmonized batch, and how to use the phenotype variables to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
            'type': 'The general type of harmonization required to produce your target variable.',
        }

    def clean(self):
        """Custom form field validation for UnitRecipeForm."""
        cleaned_data = super(UnitRecipeForm, self).clean()
        # Check that a name is unique for this user, for creation only.
        if self.instance.pk is None:
            name = cleaned_data.get('name', '')
            existing_names_for_user = [u.name for u in self.user.units_created_by.all()]
            if name in existing_names_for_user:
                self.add_error('name', forms.ValidationError(u'A harmonization unit named {} already exists for user {}.'.format(name, self.user.email)))
        return cleaned_data
    
    def get_model_name(self):
        """Get the model name from the ModelForm class. Used in templates."""
        return self.instance._meta.verbose_name


class UnitRecipeAdminForm(UnitRecipeCleanMixin, forms.ModelForm):
    """Form to create/edit UnitRecipe model objects."""
    
    class Meta:
        model = UnitRecipe
        fields = ('name', 'age_variables', 'batch_variables', 'phenotype_variables', 'type', 'instructions', )
        widgets = {'age_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
            'batch_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
            'phenotype_variables': autocomplete.ModelSelect2Multiple(url='trait_browser:source:autocomplete'),
        }
        help_texts = {'name': 'A unique and informative name for the harmonization unit.',
            'age_variables': 'Enter the DCC id(s) of the variable(s) needed to derive age for your harmonized variable <strong>in this harmonization unit</strong>.',
            'batch_variables': 'Enter the DCC id(s) of the variable(s) needed to derive a harmonized batch variable <strong>in this harmonization unit</strong>. (optional)',
            'phenotype_variables': 'Enter the DCC id(s) of the variable(s) needed to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
            'instructions': 'Describe how to use the age variables to derive age, how to use the batch variables to derive a harmonized batch, and how to use the phenotype variables to derive your target harmonized variable <strong>in this harmonization unit</strong>.',
            'type': 'The general type of harmonization required to produce your target variable.',
        }

    def clean(self):
        """Custom form field validation for UnitRecipeAdminForm."""
        cleaned_data = super(UnitRecipeAdminForm, self).clean()
        # This clean() is a placehold and doesn't do any special cleaning now.
        return cleaned_data
    
    def get_model_name(self):
        """Get the model name from the ModelForm class. Used in templates."""
        return self.instance._meta.verbose_name


# HarmonizationRecipe form classes.
class HarmonizationRecipeCleanMixin(object):
    """Mixin containing a clean method for HarmonizationRecipe ModelForms.
    
    All ModelForms based on HarmonizationRecipe should be able to use this clean method.
    If there are specific cleaning tasks that only apply to some forms, they
    should be added to forms on an individual basis.
    """

    def clean(self):
        """Custom form field validation for HarmonizationRecipeForm."""
        # This clean() is a placehold and doesn't do any special cleaning now.
        cleaned_data = super(HarmonizationRecipeCleanMixin, self).clean()
        return cleaned_data
    
    
class HarmonizationRecipeForm(UserKwargModelFormMixin, HarmonizationRecipeCleanMixin, forms.ModelForm):
    """Form to create/edit HarmonizationRecipe objects."""
    
    def __init__(self, *args, **kwargs):
        super(HarmonizationRecipeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout.append(Submit('Save', 'Save'))
        self.fields['units'].queryset = UnitRecipe.objects.filter(creator=self.user)
        
    class Meta:
        model = HarmonizationRecipe
        fields = ('name', 'target_name', 'target_description', 'measurement_unit', 'units', 'encoded_values', )
        # widgets = {'units': autocomplete.ModelSelect2Multiple(url='recipes:unit_autocomplete'), }
        help_texts = {
            'name': 'A unique and informative name for your harmonization recipe.',
            'target_name': 'A short and informative name for your harmonized variable. Only letters, numbers, and underscores allowed.',
            'target_description': 'A detailed description of your harmonized variable. This description will appear in documentation and data dictionaries.',
            'measurement_unit': 'The units of measurement for your target harmonized variable.',
            'units': 'The harmonization units to include in your target harmonized variable.',
            'encoded_values': 'Values and descriptions for encoded values for your target harmonized variable. Define one encoded value per line, separating the value from its description with a semicolon and a single space.<br>Example:<br>1: blue<br>2: red<br>3: green',
        }
        
    def clean(self):
        """Custom form field validation for HarmonizationRecipeForm."""
        cleaned_data = super(HarmonizationRecipeForm, self).clean()
        # Check that a name is unique for this user, for creation only.
        if self.instance.pk is None:
            name = cleaned_data.get('name', '')
            existing_names_for_user = [u.name for u in self.user.harmonization_recipes_created_by.all()]
            if name in existing_names_for_user:
                self.add_error('name', forms.ValidationError(u'A harmonization unit named {} already exists for user {}.'.format(name, self.user.email)))
        # Check that all of the units included belong to the logged in user.
        units = cleaned_data.get('units', [])
        unit_creators = [u.creator for u in units]
        if len(set(unit_creators)) > 1:
            self.add_error('units', forms.ValidationError(u'You can only select harmonization units that were created by you.'))
        return cleaned_data

    def get_model_name(self):
        """Get the model name from the ModelForm class. Used in templates."""
        return self.instance._meta.verbose_name


class HarmonizationRecipeAdminForm(HarmonizationRecipeCleanMixin, forms.ModelForm):
    """Form to create/edit HarmonizationRecipe objects."""
    
    class Meta:
        model = HarmonizationRecipe
        fields = ('name', 'target_name', 'target_description', 'measurement_unit', 'units', 'encoded_values', )
        # widgets = {'units': autocomplete.ModelSelect2Multiple(url='recipes:unit_autocomplete'), }
        help_texts = {
            'name': 'A unique and informative name for your harmonization recipe.',
            'target_name': 'A short and informative name for your harmonized variable. Only letters, numbers, and underscores allowed.',
            'target_description': 'A detailed description of your harmonized variable. This description will appear in documentation and data dictionaries.',
            'measurement_unit': 'The units of measurement for your target harmonized variable.',
            'units': 'The harmonization units to include in your target harmonized variable.',
            'encoded_values': 'Values and descriptions for encoded values for your target harmonized variable. Define one encoded value per line, separating the value from its description with a semicolon and a single space.<br>Example:<br>1: blue<br>2: red<br>3: green',
        }
        
    def clean(self):
        """Custom form field validation for HarmonizationRecipeAdminForm."""
        cleaned_data = super(HarmonizationRecipeAdminForm, self).clean()
        # Check that all units were created by the same user.
        units = cleaned_data.get('units', [])
        unit_creators = [u.creator for u in units]
        if len(set(unit_creators)) > 1:
            self.add_error('units', forms.ValidationError(u'All harmonization units must have been created by the same user.'))
        return cleaned_data

    def get_model_name(self):
        """Get the model name from the ModelForm class. Used in templates."""
        return self.instance._meta.verbose_name