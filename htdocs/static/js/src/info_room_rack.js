require([
    'plugins/linear_gauge',
    'plugins/symbols',
    'libs/jquery.sparkline'
], function (LinearGauge, symbol) {

    function getMetrics($element) {
        return _.object($element.find('[data-metric]').map(function () {
            return [[this.dataset.metric, this.id]];
        }));
    }

    function getMetric($element) {
        var element = $element[0];
        var obj = {};
        obj[element.dataset.metric] = element.id;
        return obj;
    }

    function getValue(result) {
        var datapoints = result.datapoints;
        var point = _.find(datapoints.reverse(), function (datapoint) {
            return datapoint[0] != null;
        });

        return point[0] ? point[0] : 'N/A';
    }

    function updateSensors(results, metricMap) {
        _.each(results, function (result) {
            var value = getValue(result);
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


    function updatePDUS(results, metricMap) {
        _.each(results, function (result) {
            var value = getValue(result);
            var elementId = metricMap[result.target];
            var $element = $(document.getElementById(elementId));
            var gaugeElement = $element.find('.pdu-gauge')[0];

            if ($.data(gaugeElement, 'gauge')) {
                $.data(gaugeElement, 'gauge').update(value);
            } else {
                var gauge = new LinearGauge({nodeId: gaugeElement.id, precision: 2, color: 'lightsteelblue'});
                gauge.update(value);
                $.data(gaugeElement, 'gauge', gauge);
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
            console.log("Error on data request");
        });
    }

    function updateRack($rack) {
        console.log("updating rack %s", $rack.data('rackid'));
        getData(getMetrics($rack.find('.rack-center')), updateSensors);
        getData(getMetrics($rack.find('.rack-pdu')), updatePDUS);
    }

    function updateRacks() {
        $('.rack').each(function () {
            updateRack($(this));
        });
    }


    //  Run on page load
    $(function () {

        /**
         * Stuff for adding and removing sensors
         */
        var $sensorModal = $('#sensormodal');
        $('button').on('click', function () {
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
                    var thisIsPDU = $(data).find('.pdu-gauge').length;
                    if (thisIsPDU) {
                        getData(getMetric($(data)), updatePDUS);
                    } else {
                        getData(getMetric($(data)), updateSensors);
                    }
                    $modal.foundation('reveal', 'close');
                })
            })
        });


        updateRacks();
        setInterval(updateRacks, 60000);

    });

});
