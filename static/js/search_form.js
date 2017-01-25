$(document).ready( function() {

    $("#save-search-btn").click( function(event) {
        // identify requested URL
        var params = window.location.search
        $.get('/phenotypes/source/search/save/', {searchParams: params});
        // button should be "dimmed" if it's been clicked
        // button should be un-"dimmed" on a new search
    });
});
