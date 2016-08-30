"""Form classes for the trait_browser app."""

from django import forms
from django.core.urlresolvers import reverse_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field, Reset
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, InlineCheckboxes

from . models import GlobalStudy, SourceTrait


class SourceTraitCrispySearchForm(forms.Form):
    """Form to handle searching within SourceTrait objects.
    
    This form class is a Subclass of crispy_forms.Form. Crispy forms is a
    Django app that improves upon the built in Django Form object.
    """
    
    # Override the init method, to allow dynamic setting of the choices for the
    # study field, which enables proper testing.
    def __init__(self, *args, **kwargs):
        super(SourceTraitCrispySearchForm, self).__init__(*args, **kwargs)
        self.STUDIES = [[x.pk, x.name] for x in Study.objects.all().order_by('i_name')]
        self.fields['study'] = forms.MultipleChoiceField(choices=self.STUDIES,
            widget=forms.CheckboxSelectMultiple(), required=False,
            help_text='If no studies are selected, source phenotypes from all studies will be searched.')
    
    text = forms.CharField(label='search text', max_length=100,
        help_text='Both phenotype names and descriptions will be searched.')

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.form_method = 'get'
    helper.layout = Layout(
        Field('text'),
        InlineCheckboxes('study'),
        FormActions(
            Submit('submit', 'Search', css_class='btn-primary btn-disable'),
        )
    )