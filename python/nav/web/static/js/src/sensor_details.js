require([
    "plugins/graphfetcher_controller",
    "plugins/gauge",
], function(graphfetcher_controller, Gauge) {
    $(function() {
        var $gauge = $('.sensor-gauge');
        if ($gauge.length) {
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
        } else {
            var $sensor = $('.sensor');
            var request = $.get($sensor.data('url'));

            request.done(function(data) {
                if (data.length === 0) {
                    return;
                }

                var datapoints = data[0].datapoints.reverse();

                for (var i=0; i<datapoints.length; i++) {
                    var value = datapoints[i][0];
                    var epoch = datapoints[i][1];
                    if (value !== null) {
                        var on_state = $sensor.data('on-state');
                        if (value === on_state ) {
                            $(".off").addClass('hidden');
                            $(".on").removeClass('hidden');
                        } else {
                            $(".on").addClass('hidden');
                            $(".off").removeClass('hidden');
                        }
                        break;
                    }
                }
            });
        }

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
