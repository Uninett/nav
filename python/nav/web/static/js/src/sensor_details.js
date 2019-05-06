require([
    "plugins/graphfetcher_controller",
    "plugins/gauge",
], function(graphfetcher_controller, Gauge) {
    $(function() {
        var $gauge = $('.sensor-gauge');
        var thresholds = $gauge.data('thresholds') ? $gauge.data('thresholds').split(',') : [];
        var _gauge = new Gauge({
            node: $gauge[0],
            min: $gauge.data('min'),
            max: $gauge.data('max'),
            url: $gauge.data('url'),
            symbol: ' ',
            unit: $gauge.data('unit'),
            thresholds: thresholds
        });

        $('#add-to-dashboard-button').on('click', function (event) {
            event.preventDefault();
            var $button = $(this);
            var request = $.post($button.data('dashboardUrl'));
            request.done(function() {
                $button.removeClass('secondary').addClass('success');
            });
            request.fail(function() {
                $button.removeClass('secondary').addClass('failure');
            });
        });
    });
});
