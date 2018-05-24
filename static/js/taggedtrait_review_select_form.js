$(document).ready(function() {

  // Reset the study field if the tag field changes.
  $(':input[name$=tag]').on('change', function() {
    // Get the field prefix, ie. if this comes from a formset form
    var prefix = $(this).getFormPrefix();

    // Clear the autocomplete with the same prefix
    $(':input[name=' + prefix + 'study]').val(null).trigger('change');
  });

})
