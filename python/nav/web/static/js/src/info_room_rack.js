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
     * Rounds something that may be a number to max n decimals.
     * If you want a specific number of decimals use toFixed.
     */
    function round(number, n) {
        n = n === undefined ? 2 : n;
        if (number === null) {
            return number;
        }

        try {
            return parseFloat(Number(number).toFixed(n));
        } catch (e) {
            return number;
        }
    }

    /**
     * Matches all search terms when searching in Select2
     */
    function select2MultipleMatcher(term, text) {
        var has = true;
        var words = term.toUpperCase().split(" ");
        for (var i =0; i < words.length; i++){
            var word = words[i];
            has = has && (text.toUpperCase().indexOf(word) >= 0);
        }
        return has;
    }


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
            $sensorModal.find('#add-rackitem-tabs').tabs().show();
            var sumSelectClone = $sensorModal.find('.sumsensors').closest('label').clone();
            $sensorModal.find('.sensordropdown').select2({
                matcher: select2MultipleMatcher
            });
            $sensorModal.find('.sensordropdown').select2('open');

            $sensorModal.find('.sumform').on('change', '.sumsensors', function (event) {
                var label = $(event.target).closest('label');
                var clone = sumSelectClone.clone();
                clone.find('select').select2({
                    matcher: select2MultipleMatcher
                });
                label.after(clone);
            });
            $sensorModal.find('.cancelbutton').on('click', function (event) {
                event.preventDefault();
                $sensorModal.foundation('reveal', 'close');
            });

            var $form = $sensorModal.find('form');
            $form.submit(function (event) {
                event.preventDefault();
                var request = $.post($(this).attr('action'), $(this).serialize());
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
            getData(getMetric($sensor), updatePDU);
        } else {
            getData(getMetric($sensor), updateSensor);
        }
    }


    /**
     * Creates mapping between metric and element id for all data-metric elements
     */
    function getMetrics($element) {
        return _.object($element.find('[data-metric]').map(function () {
            return [[this.id, this.dataset.metric]];
        }));
    }

    /**
     * Creates mapping between element id and metric for a single element
     */
    function getMetric($element) {
        var element = $element[0];
        var obj = {};
        obj[element.id] = element.dataset.metric;
        return obj;
    }

    /**
     * Gets the correct single value from the datapoints returned from Graphite
     */
    function getValue(datapoints) {
        var point = _.find(datapoints.reverse(), function (datapoint) {
            return datapoint[0] != null;
        });

        return point ? point[0] : null;
    }

    /**
     * Map result list to {target: datapoints}
     * @param {array} results - A list of {'target': 'metric', 'datapoints', [[value, timestamp]]}
     */
    function createResultMap(results) {
        var resultMap = {};
        _.each(results, function(result) {
            resultMap[result.target] = result.datapoints;
        });
        return resultMap;
    }


    /**
     * Get min and max value for the item to display
     */
    function getMinMax(rackitem) {
        try {
            return rackitem.data('displayRange');
        } catch (e) {
            console.log('No minmax set for', rackitem);
            return [0, 50];
        }
    }


    /**
     * Updates all sensors in the metricMap.
     */
    function updateSensors(results, metricMap, updateFunc) {
        var resultMap = createResultMap(results);

        _.each(metricMap, function (target, elementId) {
            var datapoints = resultMap[target];
            var value = round(datapoints ? getValue(datapoints) : null);
            var $element = $(document.getElementById(elementId));
            updateFunc($element, value, getMinMax($element));
        });
    }


    /** Update a sensor in the middle column (not PDU) */
    function updateSensor($element, value, minMax) {
        var unit = $element.data('unit') ? $element.data('unit').toLowerCase() : "";
        var unitIsKnown = _.has(unitMapping, unit);
        var textvalue = value === null ? 'NaN' : value + symbol(unit);
        var min = minMax[0], max = minMax[1];
        $element.find('.textvalue').html(textvalue);

        if (unitIsKnown) {
            // Create sparkline if unit is known only
            $element.find('.sparkline').sparkline([null, value, max], {
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

    }


    /** Update a PDU sensor */
    function updatePDU($element, value, minMax) {
        var gaugeElement = $element.find('.pdu-gauge')[0];

        if ($.data(gaugeElement, 'gauge')) {
            $.data(gaugeElement, 'gauge').update(value);
        } else {
            var gauge = new LinearGauge({
                nodeId: gaugeElement.id,
                precision: 2,
                height: 100,
                max: minMax[1]
            });
            gauge.update(value);
            $.data(gaugeElement, 'gauge', gauge);
        }

    }


    /**
     * Fetches data for all metrics in the metricmap and runs updatefunc
     */
    function getData(metricMap, updateFunc) {
        var targets = _.values(metricMap);
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
            updateSensors(data, metricMap, updateFunc);
        });

        request.fail(function () {
            console.log("Error on data request");
        });


    }

    /**
     * Updates a single rack
     */
    function updateRack($rack) {
        getData(getMetrics($rack.find('.rack-body .rack-center')), updateSensor);
        getData(getMetrics($rack.find('.rack-body .rack-pdu')), updatePDU);
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
            var rack = $(this).closest('.rack');
            var request = $.post(NAV.urls.remove_sensor , {
                id: rackSensor.data('id'),
                column: rackSensor.data('column'),
                rackid: rack.data('rackid')
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
                    var serialized = $(this).sortable('serialize', {
                        attribute: 'data-sortid'
                    });
                    var rack = $(this).closest('.rack');
                    var column = $(this).data('column');
                    serialized += '&column=' + column;
                    serialized += '&rackid=' + rack.data('rackid');
                    var request = $.post(NAV.urls.save_sensor_order, serialized);
                }
            });
        });
    }


    function addRackSort() {
        $('#racks-container').sortable({
            tolerance: 'pointer',
            handle: '.icon-container .fa-arrows',
            forcePlaceholderSize: true,
            placeholder: 'highlight',
            update: function (event, ui) {
                var serialized = $(this).sortable('serialize');
                var request = $.post(NAV.urls.save_rack_order, serialized);
            }
        });
    }


    function addColorChooser() {
        $('#racks-container').on('change', 'form.color-chooser', function(event) {
            var classes = _.map(this.querySelectorAll("input[type=radio]"), function(element) {
                return element.value;
            }).join(' ');

            var $radio = $(event.target),
                html_class = $radio.val(),
                rackid = $radio.closest('.rack').data('rackid');

            $.post(NAV.urls.save_rack_color, {
                rackid: rackid,
                class: html_class
            }).done(function() {
                $radio.closest('.rack').find('.rack-body').removeClass(classes).addClass(html_class);
            }).fail(function() {
                console.error('Failed updating html class');
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

        addRackSort();
        addSensorSort();

        addColorChooser();

        // Start updating racks with data
        updateRacks();
        setInterval(updateRacks, 60000);

    });

});
