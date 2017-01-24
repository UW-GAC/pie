$(document).ready( function() {

    $("#save-search-btn").click( function(event) {
        // get value from search field
        var search_text = $("#id_text").filter(":input").val()
        $.get('/phenotypes/source/search/save/', {text: search_text});
        // button should be "dimmed" if it's been clicked
        // button should be un-"dimmed" on a new search
    });
});
