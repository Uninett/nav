require(['libs/jquery', 'libs/jquery-ui-1.8.21.custom.min', 'libs/spin.min'], function () {
    var $inputElement = $('#metricsearchinput'),
        $infoElement = $('#metricInfo'),
        $metricName = $infoElement.find('.metricName'),
        $metricGraph = $infoElement.find('.metricGraph'),
        spinner = new Spinner();

    $(function () {
        $inputElement.autocomplete(
            {
                'delay': 300,
                'minLength': 3,
                'source': $inputElement.attr('data-url'),
                'select': handleSelect
            }
        );
    });

    function handleSelect(event, ui) {
        if (ui.item.expandable) {
            $inputElement.autocomplete('search', ui.item.value + '.');
        } else {
            displayGraph(ui.item.value);
        }
    }

    function displayGraph(metric) {
        $metricName.empty().text(metric);
        startSpinner();

        $.get($inputElement.attr('data-renderurl'),
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
