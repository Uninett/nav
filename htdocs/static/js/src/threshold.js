require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min', 'libs/spin.min'], function () {
    /* The global variable metric is set in the base template of the threshold page */

    var $inputElement = $('#id_target'),
        $dataElement = $inputElement.parents('.dataelement'),
        metric = $dataElement.attr('data-metric'),
        $metricGraph = $('.metricGraph'),
        spinner = new Spinner();

    $(function () {
        $inputElement.autocomplete(
            {
                'delay': 300,
                'minLength': 3,
                'source': $dataElement.attr('data-url'),
                'select': handleSelect
            }
        );

        if (metric) {
            displayMetricInfo(metric);
        }
    });

    function handleSelect(event, ui) {
        if (ui.item.expandable) {
            $inputElement.autocomplete('search', ui.item.value + '.');
        } else {
            displayMetricInfo(ui.item.value);
        }
    }

    function displayMetricInfo(metric) {
        startSpinner();

        $.get($dataElement.attr('data-renderurl'),
            {'metric': metric},
            function (data) {
                var image = new Image();
                image.src = data.url;
                image.onload = function () {
                    stopSpinner();
                    $(image).appendTo($metricGraph);
                };
            }
        );
    }

    function startSpinner() {
        $metricGraph.empty();
        $metricGraph.addClass('spinContainer');
        spinner.spin($metricGraph.get(0));  // Remember that spin does not accept jquery objects
    }

    function stopSpinner() {
        spinner.stop();
        $metricGraph.removeClass('spinContainer');
    }

});
