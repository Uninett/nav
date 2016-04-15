define('jquery', [], function() {
    return jQuery;
});

require([
    'plugins/accordion_maker',
    'libs/foundation.min',
    'libs/select2.min',
    'plugins/megadrop',
], function (accordionMaker) {


    /** Enable slash to navigate to search, whereas escape removes focus from search */
    function addSearchFocusHandlers() {
        var $searchInput = $('#query');

        // Listen to keypress for slash, go to search if pressed.
        $(document).keypress(function (event) {
            if (event.keyCode === 47) {
                event.preventDefault();
                $searchInput.focus();
            }
        });

        // Remove focus when escape is pressed
        $searchInput.keyup(function (event) {
            if (event.keyCode === 27) {
                $searchInput.blur();
            }
        });

    }

    $(function () {
        /* Add redirect to login on AJAX-requests if session has timed out */
        $(document).ajaxError(function (event, request) {
            if (request.status === 401) {
                window.location = '/index/login/?origin=' + encodeURIComponent(window.location.href);
            }
        });

        $(document).foundation();   // Apply foundation javascript on load
        accordionMaker($('.tabs')); // Apply accordionmaker for tabs
        $('select.select2').select2();

        // addSearchFocusHandlers();  Fix this to not grab every / before activating

    });
});


