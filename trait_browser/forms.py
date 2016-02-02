from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field, Reset
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, InlineCheckboxes

from . models import Study, SourceTrait

class SourceTraitCrispySearchForm(forms.Form):
    text = forms.CharField(label="search text", max_length=100,
        help_text="Both trait names and descriptions will be searched.")

    # may need to move this into an __init__ method?
    # but it seems to be ok for now.
    # we will not be adding studies frequently, anyway
    STUDIES = [[x.pk, x.name] for x in Study.objects.all().order_by('name')]

    # allow selection of multiple studies in which to search
    study = forms.MultipleChoiceField(choices=STUDIES,
        widget=forms.CheckboxSelectMultiple(), required=False,
        help_text="If no studies are selected, source traits from all studies will be searched.")

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-sm-2'
    helper.field_class = 'col-sm-10'
    helper.form_method = 'get'

    helper.layout = Layout(
        Field('text'),
        InlineCheckboxes('study'),
        FormActions(
            Submit('submit', 'Search', css_class="btn-primary btn-disable"),
            Reset('name', 'Reset', css_class="btn-disable"),
            )
        )


