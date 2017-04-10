$(document).ready(function() {

    // change opacity of main home divs on mouseover
    $(".action-home:not(.action-disabled)").hover(function() {
        $(this).stop().fadeTo(200, 1) },
        function() {
        $(this).stop().fadeTo(300, 0.6)
    });
    
    // disable search button after searching
    $('form').submit(function() {
        $(this).find(".btn-disable").prop('disabled',true);
    });
})