from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field, Reset
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions, InlineCheckboxes

from . models import Study, SourceTrait

class SourceTraitCrispySearchForm(forms.Form):
    text = forms.CharField(label="search text", max_length=100)

    # may need to move this into an __init__ method?
    # but it seems to be ok for now.
    # we will not be adding studies frequently, anyway
    STUDIES = [[x.pk, x.name] for x in Study.objects.all().order_by('name')]

    # allow selection of multiple studies in which to search
    studies = forms.MultipleChoiceField(choices=STUDIES,
        widget=forms.CheckboxSelectMultiple(), required=False,
        help_text="If no study is selected, source traits from all studies will be searched")

    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.label_class = 'col-lg-2'
    helper.field_class = 'col-lg-8'
    helper.form_method = 'get'

    helper.layout = Layout(
        Field('text'),
        # make the study checkboxes collapsible
        HTML("""
            <hr>
            <a class="btn btn-default" role="button" data-toggle="collapse" href="#traitStudyFilterField" aria-expanded="false" aria-controls="collapseMountainRange">
  Select by study:
    </a>
    <div class="collapse" id="traitStudyFilterField">
        <div class="well">
        """),
   
        InlineCheckboxes('studies'),
        # end the collapsible divs
        # the <hr> adds some space between this button and the submit button
        HTML("""
              </div>
            </div>
            <hr>
            """),
        FormActions(
            Submit('submit', 'Search', css_class="btn-primary btn-disable"),
            Reset('name', 'Reset', css_class="btn-disable"),
            )
        )


