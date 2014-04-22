require(['libs/jquery'], function () {
    $(function () {
        $('#watchdog-tests').on('click', '.label.alert', function (event) {
            $(event.target).next().toggle();
        });

        /* Fetch overview. This is done with AJAX because it may be very slow */
        var $overview = $('#watchdog-overview'),
            url = $overview.attr('data-url'),
            request = $.get(url, function (data) { $overview.html(data); });

        request.fail(function () {
            $overview.html('<div class="alert-box alert">Error fetching overview</div>');
        });

    });
});
