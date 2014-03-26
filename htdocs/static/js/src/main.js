require([
    'plugins/accordion_maker',
    'libs/foundation.min',
    'libs/select2.min',
    'plugins/megadrop'
], function (accordionMaker) {
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
    });
});


