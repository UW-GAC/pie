$(document).ready(function() {

  var tag_field = $("select[name$=tag]");
  var study_field = $("select[name$=study]");

  // Load the page with a disabled study field.
  study_field.prop('disabled', true);

  // Reset the study field if the tag field changes.
  tag_field.on('change', function() {
    // Get the field prefix, ie. if this comes from a formset form
    var prefix = $(this).getFormPrefix();
    console.log(prefix)

    // Clear the autocomplete with the same prefix
    $(':input[name=' + prefix + 'study]').val(null).trigger('change');

    // Remove the disabled attribute from the study field.
    study_field.prop('disabled', false);
  });

})
