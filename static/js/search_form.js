$(document).ready( function() {

    $("#save-search-btn").click( function(event) {
        // identify requested URL
        var params = window.location.search
        $.get('/phenotypes/source/search/save/', {searchParams: params});
        // button should be "disabled" if it's been clicked
        $(this).prop('disabled', true)
        $(this).text('Saved')
    });
});
