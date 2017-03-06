require([
    'plugins/linear_gauge',
    'plugins/symbols',
    'libs/jquery.sparkline'
], function (LinearGauge, symbol) {

    function getMetrics(selector) {
        return _.object($(selector + ' [data-metric]').map(function () {
            return [[this.dataset.metric, this.id]];
        }));
    }

    function updateDisplay(results, metricMap) {
        _.each(results, function (result) {
            var datapoints = result.datapoints;
            var point = _.find(datapoints.reverse(), function (datapoint) {
                return datapoint[0] != null;
            });

            var value = point[0] ? point[0].toFixed(2) : 'N/A';
            var element = metricMap[result.target];
            var $element = $(document.getElementById(element));
            $element.find('.sparkline').sparkline([null, value, 50], {
                type: 'bullet',
                performanceColor: 'lightsteelblue',
                rangeColors: ['#fff'],
                width: '100%',
                tooltipFormatter: function (data) {
                    // return data.values[1].toFixed(2);
                    return ""
                }
            });
            $element.find('.textvalue').html(value + symbol($element.data('unit')));
        })
    }


    function updatePDUData(results, metricMap) {
        console.log("Updating pdudata");
        _.each(results, function (result) {
            var datapoints = result.datapoints;
            var point = _.find(datapoints.reverse(), function (datapoint) {
                return datapoint[0] != null;
            });

            var value = point[0] ? point[0] : 'N/A';
            var elementId = metricMap[result.target];
            var element = document.getElementById(elementId);

            if ($.data(element, 'gauge')) {
                $.data(element, 'gauge').update(value);
            } else {
                var gauge = new LinearGauge({nodeId: elementId, precision: 2, color: 'lightsteelblue'});
                gauge.update(value);
                $.data(element, 'gauge', gauge);
            }

        });
    }


    function getData(metricMap, updateFunc) {
        var url = '/graphite/render';
        var request = $.getJSON(url,
            {
                target: _.keys(metricMap),
                format: 'json',
                from: '-5min',
                until: 'now'
            }
        );

        request.done(function (data) {
            updateFunc(data, metricMap);
        });

        request.fail(function () {
            // alert('Error on data request')
        });
    }

    //  Run on page load
    $(function () {

        var $sensorModal = $('#sensormodal');
        $('button').on('click', function () {
            console.log(this);
            $.data($sensorModal, 'clickedButton', $(this));
            var column = $(this).closest('.rack-column').data('column');

            $sensorModal.foundation('reveal', 'open', {
                url: NAV.urls.render_add_sensor,
                method: 'post',
                data: {
                    rackid: $(this).closest('.rack').data('rackid'),
                    column: column,
                    is_pdu: column != '1'
                }
            });

        });

        $('#racks').on('click', '.fa-remove', function () {
            console.log(this);
            var rackSensor = $(this).closest('.rack-sensor');
            var request = $.post(NAV.urls.remove_sensor, {
                racksensorid: rackSensor.data('racksensorid')
            });
            request.done(function () {
                rackSensor.remove();
            })
        });


        $(document).on('opened', '#sensormodal', function () {
            var $modal = $('#sensormodal');

            console.log("Modal was opened");
            $modal.find('.sensordropdown').select2();
            $modal.find('.cancelbutton').on('click', function (event) {
                event.preventDefault();
                $modal.foundation('reveal', 'close');
            });

            var $form = $modal.find('form');
            $form.submit(function (event) {
                event.preventDefault();
                var request = $.post($form.attr('action'), $form.serialize());
                request.fail(function () {
                    console.log("Failed to post form");
                });
                request.done(function (data) {
                    $.data($sensorModal, 'clickedButton').siblings('.sensors').append(data);
                    $modal.foundation('reveal', 'close');
                })
            })
        });


        getData(getMetrics('.rack-center'), updateDisplay);
        setInterval(function () {
            getData(getMetrics('.rack-center'), updateDisplay);
        }, 5000);

        getData(getMetrics('.rack-pdu'), updatePDUData);
        setInterval(function () {
            getData(getMetrics('.rack-pdu'), updatePDUData);
        }, 5000);

    });

});
