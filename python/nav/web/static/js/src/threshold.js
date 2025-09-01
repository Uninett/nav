require(['libs/spin.min', 'libs/jquery-ui.min'], function (Spinner) {
    /* The global variable metric is set in the base template of the threshold page */

    var $inputElement = $('#id_target'),
        $rawButton = $('#id_raw'),
        $refreshButton = $('#refresh-graph'),
        $dataElement = $inputElement.parents('.dataelement'),
        metric = $dataElement.attr('data-metric'),
        $metricGraph = $('.metricGraph'),
        fetching = false,
        spinner = new Spinner();

    $(function () {
        $inputElement.autocomplete(
            {
                'delay': 300,
                'minLength': 3,
                'source': function(query, callback) {
                    var url = $dataElement.attr('data-url');
                    $.getJSON(url, query, function(data) {
                        callback(data.items);
                    });
                },
                'select': handleSelect
            }
        );

        /* Prevent form submission on enter, draw graph instead */
        $inputElement.keydown(function (event) {
            if (event.which === 13) {
                event.preventDefault();
                displayMetricInfo($inputElement.val());
            }
        });

        if (metric) {
            displayMetricInfo(metric);
        }

        /* Redraw graph when raw checkbox is clicked */
        $rawButton.on('click', function () {
            displayMetricInfo($inputElement.val());
        });

        /* Redraw graph when refreshbutton is clicked */
        $refreshButton.on('click', function () {
            displayMetricInfo($inputElement.val());
        });
    });

    function handleSelect(event, ui) {
        if (ui.item.expandable) {
            window.setTimeout(
                function() {
                    $inputElement.autocomplete('search', ui.item.value + '.');
                }, 0);
        } else {
            displayMetricInfo(ui.item.value);
        }
    }

    function displayMetricInfo(metric) {
        if (fetching) {
            return;
        }
        fetching = true;
        $metricGraph.empty();
        startSpinner();
        var image = new Image();
        var url = $dataElement.attr('data-renderurl') + '?metric=' + encodeURIComponent(metric);
        if ($rawButton.prop('checked')) {
            url += '&raw=true';
        }
        image.src = url;
        image.onload = function () {
            stopSpinner();
            $(image).appendTo($metricGraph);
            fetching = false;
        };
        image.onerror = function () {
            stopSpinner();
            $metricGraph.append('<span class="alert-box alert">Error loading graph</span>');
            fetching = false;
        };
    }

    function startSpinner() {
        $metricGraph.addClass('spinContainer');
        spinner.spin($metricGraph.get(0));  // Remember that spin does not accept jquery objects
    }

    function stopSpinner() {
        spinner.stop();
        $metricGraph.removeClass('spinContainer');
    }

});
