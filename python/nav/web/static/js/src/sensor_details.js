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
        }
    });
});
