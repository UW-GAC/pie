$(document).ready(function() {
    // change opacity of glyphicons on mouseover
    $(".glyphicon-home:not(.glyphicon-disabled)").hover(function() {
        $(this).stop().fadeTo(200, 1) },
        function() {
        $(this).stop().fadeTo(300, 0.4)
    });
})