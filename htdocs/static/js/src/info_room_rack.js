require([
    'plugins/linear_gauge',
    'plugins/symbols',
    'libs/jquery.sparkline'
], function (LinearGauge, symbol) {

    /**
     * TODO:
     * - How to set min and max values for the different sensors
     * - Naming - is it really racks?
     */


    var unitMapping = {
        'celsius': 'celsius'
    };



    /**
     * Opens modal (with remote url) with content for adding sensors when
     * button is clicked
     */
    function addOpenSensorModalListener($sensorModal) {
        $('#racks').on('click', '.rack-column button', function () {
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
            var unit = $element.data('unit').toLowerCase();
            var unitIsKnown = _.has(unitMapping, unit);
            $element.find('.textvalue').html(value + symbol(unit));

            if (unitIsKnown) {
                // Create sparkline if unit is known only
                $element.find('.sparkline').sparkline([null, value, 50], {
                    type: 'bullet',
                    performanceColor: 'lightsteelblue',
                    rangeColors: ['#fff'],
                    width: '100%',
                    tooltipFormatter: function (data) {
                        // return data.values[1].toFixed(2);
                        return "";
                    }
                });
            }
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
        var targets = _.keys(metricMap);
        if (!targets.length) { return; }
        var url = '/graphite/render';
        var request = $.getJSON(url,
            {
                target: targets,
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
        $('#racks').on('click', '.remove-rack', function (event) {
            // event.preventDefault();
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


    /**
     * Add listeners for displaying and hiding edit mode
     */
    function addEditModeListener() {
        var $racks = $('#racks');

        function switchMode(func) {
            var $this = $(this);
            var $rack = $this.closest('.rack');
            $rack[func]('editmode');
        }

        $racks.on('click', '.edit-rack', function() {
            switchMode.call(this, 'addClass');
        });

        $racks.on('click', '.close-edit-rack', function() {
            switchMode.call(this, 'removeClass');
        });
    }


    // Toggle editmode on for empty racks
    function toggleEditEmptyRack() {
        $('.rack').each(function () {
            var $rack = $(this);
            if (!$rack.find('.rack-sensor').length) {
                $rack.find('.edit-rack').click();
            }
        });
    }


    function addRenameRackListener() {
        $('#racks').on('submit', '.rename-rack-form', function(event) {
            event.preventDefault();
            var $form = $(this);
            var request = $.post($form.attr('action'), $form.serialize());
            request.fail(function () {
                console.log("Failed to rename rack");
            });
            request.done(function (name) {
                // Give a little flash to indicate success
                var $submit = $form.find('[type="submit"]');
                $submit.addClass('success');
                setTimeout(function () {
                    $submit.removeClass('success');
                }, 1000);
                $form.siblings('.rack-heading').find('.rackname').text(name);
            });
        });
    }


    function addSensorSort() {
        $('.rack').find('.rack-column .sensors').each(function() {
            $(this).sortable({
                tolerance: 'pointer',
                handle: '.fa-arrows',
                forcePlaceholderSize: true,
                placeholder: 'highlight',
                update: function(event, ui) {
                    var serialized = $(this).sortable('serialize');
                    var request = $.post(NAV.urls.save_sensor_order, serialized);
                }
            });
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

        addRenameRackListener();

        addSensorSort();

        // Start updating racks with data
        updateRacks();
        setInterval(updateRacks, 60000);

    });

});
