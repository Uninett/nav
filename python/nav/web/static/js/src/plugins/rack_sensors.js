/**
 * Fetches sensor values from Graphite and updates the sensors in a rack.
 *
 * Used by the Racks tab in Room Info and by the Environment Rack widget. All
 * element lookups are done within the given rack element, so the same rack
 * can be shown more than once on a page.
 */
define([
    'plugins/linear_gauge',
    'plugins/symbols',
    'plugins/d3_sparkline'
], function (LinearGauge, symbol, d3Sparkline) {

    /* Units that get a bullet bar unless barForAllUnits is set */
    var barUnits = ['celsius'];


    /**
     * Default options, matching the Racks tab in Room Info
     *
     * - barForAllUnits: draw a bullet bar for every numeric unit
     * - unitSymbols: append a unit symbol to the value text
     * - missingValueText: text to show when there is no value
     * - gaugeColor: single colour for PDU gauges instead of the gradient
     */
    var defaults = {
        barForAllUnits: false,
        unitSymbols: true,
        missingValueText: 'NaN',
        gaugeColor: undefined
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
     * Gets the last value that is not null from the datapoints returned from
     * Graphite
     */
    function getValue(datapoints) {
        var point = datapoints.slice().reverse().find(function (datapoint) {
            return datapoint[0] !== null;
        });

        return point ? point[0] : null;
    }


    /**
     * Map result list to {target: datapoints}
     * @param {array} results - A list of {'target': 'metric', 'datapoints', [[value, timestamp]]}
     */
    function createResultMap(results) {
        var resultMap = {};
        results.forEach(function (result) {
            resultMap[result.target] = result.datapoints;
        });
        return resultMap;
    }


    /**
     * Get min and max value for the item to display
     */
    function getMinMax($rackitem) {
        try {
            return $rackitem.data('displayRange');
        } catch (e) {
            console.log('No minmax set for', $rackitem);
            return [0, 50];
        }
    }


    /**
     * Creates a list of [element, metric] pairs for all data-metric elements
     */
    function getMetrics($element) {
        return $element.find('[data-metric]').map(function () {
            return [[this, this.dataset.metric]];
        }).get();
    }


    /** Update a sensor in the middle column (not PDU) */
    function updateSensor($element, value, minMax, options) {
        var unit = $element.data('unit') ? $element.data('unit').toLowerCase() : "";
        if (unit === 'boolean') {
            var on_state = $element.data('on-state');
            if (value === on_state ) {
                $element.find(".off").addClass('hidden');
                $element.find(".on").removeClass('hidden');
            } else {
                $element.find(".on").addClass('hidden');
                $element.find(".off").removeClass('hidden');
            }
            return;
        }

        var textvalue;
        if (value === null) {
            textvalue = options.missingValueText;
        } else {
            textvalue = options.unitSymbols ? value + symbol(unit) : value;
        }
        $element.find('.textvalue').html(textvalue);

        if (options.barForAllUnits || barUnits.indexOf(unit) !== -1) {
            d3Sparkline.bullet($element.find('.sparkline'), [null, value, minMax[1]], {
                performanceColor: 'lightsteelblue',
                rangeColors: ['#fff']
            });
        }
    }


    /** Update a PDU sensor */
    function updatePDU($element, value, minMax, options) {
        var gaugeElement = $element.find('.pdu-gauge')[0];

        if ($.data(gaugeElement, 'gauge')) {
            $.data(gaugeElement, 'gauge').update(value);
        } else {
            var gauge = new LinearGauge({
                element: gaugeElement,
                precision: 2,
                height: 100,
                max: minMax[1],
                color: options.gaugeColor
            });
            gauge.update(value);
            $.data(gaugeElement, 'gauge', gauge);
        }
    }


    /**
     * Updates the sensor element in each [element, metric] pair
     */
    function updateSensors(results, items, updateFunc, options) {
        var resultMap = createResultMap(results);

        items.forEach(function (item) {
            var $element = $(item[0]);
            var datapoints = resultMap[item[1]];
            var value = round(datapoints ? getValue(datapoints) : null);
            updateFunc($element, value, getMinMax($element), options);
        });
    }


    /**
     * Fetches data for all [element, metric] pairs and runs updateFunc
     */
    function getData(items, updateFunc, options) {
        var targets = items.map(function (item) {
            return item[1];
        });
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
            updateSensors(data, items, updateFunc, options);
        });

        request.fail(function () {
            console.log("Error on data request");
        });
    }


    /**
     * Updates all sensors in a rack
     * @param rackElement - The .rack element, as a DOM element or jQuery object
     * @param {object} [options] - See defaults
     */
    function updateRack(rackElement, options) {
        var $rack = $(rackElement);
        options = Object.assign({}, defaults, options);
        getData(getMetrics($rack.find('.rack-body .rack-center')), updateSensor, options);
        getData(getMetrics($rack.find('.rack-body .rack-pdu')), updatePDU, options);
    }


    /**
     * Updates a single sensor
     * @param sensorElement - The .rack-sensor element, as a DOM element or jQuery object
     * @param {object} [options] - See defaults
     */
    function updateSingleSensor(sensorElement, options) {
        var $sensor = $(sensorElement);
        var element = $sensor[0];
        var items = [[element, element.dataset.metric]];
        var updateFunc = $sensor.find('.pdu-gauge').length ? updatePDU : updateSensor;
        getData(items, updateFunc, Object.assign({}, defaults, options));
    }


    return {
        updateRack: updateRack,
        updateSingleSensor: updateSingleSensor
    };

});
