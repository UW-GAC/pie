$(document).ready( function() {

    $("#save-search-btn").click( function(event) {
        // identify requested URL
        var params = window.location.search
        var type = $(this).data('traittype')
        $.get('/phenotypes/source/search/save/', {search_params: params, trait_type: type});
        // button should be "disabled" if it's been clicked
        $(this).prop('disabled', true)
        $(this).text('Saved')
    });
});
