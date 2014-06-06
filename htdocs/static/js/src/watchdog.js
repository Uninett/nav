require(['libs/jquery', 'libs/spin.min'], function () {
    function fetchOverview() {
        /* Fetch overview. This is done with AJAX because it may be very slow */
        var $overview = $('#watchdog-overview'),
            url = $overview.attr('data-url'),
            spinner = new Spinner();

        /* Start a spinner if the request takes too long */
        var countDown = setTimeout(function () {
            spinner.spin($overview.get(0));
        }, 1000);

        var request = $.get(url);
        request.done(function (html) {
            $overview.html(html);
        });
        request.fail(function () {
            $overview.html('<div class="alert-box alert">Error fetching overview</div>');
        });
        request.always(function () {
            clearTimeout(countDown);
            spinner.stop();
        });
    }

    $(function () {
        $('#watchdog-tests').on('click', '.label.alert', function (event) {
            $(event.target).closest('li').find('ul').toggle();
        });

        fetchOverview();
    });

});
