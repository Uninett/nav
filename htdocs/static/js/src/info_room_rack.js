require([
    'plugins/linear_gauge',
    'plugins/symbols',
    'libs/jquery.sparkline'
], function (LinearGauge, symbol) {

    /**
     * Opens modal (with remote url) with content for adding sensors when
     * button is clicked
     */
    function addOpenSensorModalListener($sensorModal) {
        $('.rack button').on('click', function () {
            $.data($sensorModal, 'clickedButton', $(this));
            var column = $(this).data('column');

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
    }


    /**
     * Applies listeners when modal for adding sensors is loaded
     * - form submit
     * - cancel click
     * - select2 component
     */
    function addSensorModalListeners($sensorModal) {
        $(document).on('opened', '#sensormodal', function () {
            $sensorModal.find('.sensordropdown').select2();
            $sensorModal.find('.cancelbutton').on('click', function (event) {
                event.preventDefault();
                $sensorModal.foundation('reveal', 'close');
            });

            var $form = $sensorModal.find('form');
            $form.submit(function (event) {
                event.preventDefault();
                var request = $.post($form.attr('action'), $form.serialize());
                request.fail(function () {
                    console.log("Failed to post form");
                });
                request.done(function (data) {
                    var button = $.data($sensorModal, 'clickedButton'),
                        column = button.data('column'),
                        rack = button.closest('.rack');
                    $(rack.find('.sensors').get(column)).append(data);
                    updateSingleSensor($(data));
                    $sensorModal.foundation('reveal', 'close');
                });
            });
        });
    }


    /**
     * Listens to form submits for adding new racks
     * @param selector for the rackmodal
     */
    function addRackModalListener(selector) {
        var $rackModal = $(selector);
        var $form = $rackModal.find('form');
        $form.submit(function (event) {
            event.preventDefault();
            var request = $.post($form.attr('action'), $form.serialize());
            request.fail(function () {
                console.log("Failed to post form");
            });
            request.done(function (html) {
                $('#add-rack-button-container').before(html);
                toggleEditEmptyRack();
                $rackModal.foundation('reveal', 'close');
            });
        });
    }


    /**
     * Updates a single sensor element
     */
    function updateSingleSensor($sensor) {
        var thisIsPDU = $sensor.find('.pdu-gauge').length;
        if (thisIsPDU) {
            getData(getMetric($sensor), updatePDUS);
        } else {
            getData(getMetric($sensor), updateSensors);
        }
    }


    /**
     * Creates mapping between metric and element id for all data-metric elements
     */
    function getMetrics($element) {
        return _.object($element.find('[data-metric]').map(function () {
            return [[this.dataset.metric, this.id]];
        }));
    }

    /**
     * Creates mapping between metric and element id for a single element
     */
    function getMetric($element) {
        var element = $element[0];
        var obj = {};
        obj[element.dataset.metric] = element.id;
        return obj;
    }

    /**
     * Gets the correct single value from the datapoints returned from Graphite
     */
    function getValue(result) {
        var datapoints = result.datapoints;
        var point = _.find(datapoints.reverse(), function (datapoint) {
            return datapoint[0] != null;
        });

        return point[0] ? point[0] : null;
    }

    /**
     * Updates all sensors in the metricMap. They must not be PDU-sensors
     * because these are visualized with a bullet-sparkline
     */
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
        });
    }


    /**
     * Updates all PDU-sensors in the metricMap. They must not be normal sensors
     * because PDU-sensors are visualized with a LinearGauge
     */
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

    /**
     * Fetches data for all metrics in the metricmap and runs updatefunc
     */
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

    /**
     * Updates a single rack
     */
    function updateRack($rack) {
        console.log("updating rack %s", $rack.data('rackid'));
        getData(getMetrics($rack.find('.rack-body .rack-center')), updateSensors);
        getData(getMetrics($rack.find('.rack-body .rack-pdu')), updatePDUS);
    }

    /**
     * Updates all racks
     */
    function updateRacks() {
        $('.rack').each(function () {
            updateRack($(this));
        });
    }


    /**
     * Listener for removing sensors
     */
    function addSensorRemoveListener() {
        $('#racks').on('click', '.remove-sensor', function () {
            var rackSensor = $(this).closest('.rack-sensor');
            var request = $.post(NAV.urls.remove_sensor, {
                racksensorid: rackSensor.data('racksensorid')
            });
            request.done(function () {
                rackSensor.remove();
            });
        });
    }


    /**
     * Listener for removing racks
     */
    function addRackRemoveListener() {
        $('#racks').on('click', '.remove-rack', function () {
            var yes = confirm('Really remove this rack?');
            if (yes) {
                var rack = $(this).closest('.rack');
                var request = $.post(NAV.urls.remove_rack, {
                    rackid: rack.data('rackid')
                });
                request.done(function () {
                    rack.remove();
                });
            }
        });
    }


    function addEditModeListener() {
        // Add listener for toggling editmode
        $('#racks').on('click', '.edit-rack', function() {
            $(this).closest('.rack').toggleClass('editmode');
        });
    }


    // Toggle editmode on for empty racks
    function toggleEditEmptyRack() {
        $('.rack').each(function () {
            var $rack = $(this);
            if (!$rack.find('.rack-sensor').length) {
                $rack.addClass('editmode');
            }
        });
    }


    /**
     * Runs on page load. Setup page
     */
    $(function () {

        // Add listener to edit-button, toggle edit-mode for empty racks
        addEditModeListener();
        toggleEditEmptyRack();

        // Add all listeners
        var $sensorModal = $('#sensormodal');
        addOpenSensorModalListener($sensorModal);
        addSensorModalListeners($sensorModal);

        addRackRemoveListener();
        addSensorRemoveListener();

        $(document).foundation();  // Make sure add rack modal opens
        addRackModalListener('#rackmodal');

        // Start updating racks with data
        updateRacks();
        setInterval(updateRacks, 60000);

    });

});
