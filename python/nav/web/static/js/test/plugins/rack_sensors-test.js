define(['plugins/rack_sensors'], function (RackSensors) {

    /* The options the Environment Rack widget passes */
    var WIDGET_OPTIONS = {
        barForAllUnits: true,
        unitSymbols: false,
        missingValueText: '',
        gaugeColor: 'lightsteelblue'
    };

    function centerSensorHtml(id, metric, unit, displayRange) {
        return '<div id="item_1_' + id + '" class="rack-sensor"' +
            ' data-metric="' + metric + '" data-unit="' + unit + '"' +
            ' data-display-range="' + displayRange + '">' +
            '  <div class="sparkline"></div>' +
            '  <small class="textvalue"></small>' +
            '</div>';
    }

    /* Mirrors the structure info/room/fragment_rack.html renders */
    var RACK_HTML =
        '<div class="rack" data-rackid="1">' +
        '  <div class="rack-body">' +
        '    <div class="rack-left rack-pdu rack-column">' +
        '      <div id="item_1_1" class="rack-sensor" data-metric="pdu"' +
        '           data-display-range="[0, 16]">' +
        '        <a><div id="sensor-1-1" class="pdu-gauge"></div></a>' +
        '      </div>' +
        '    </div>' +
        '    <div class="rack-center rack-column">' +
        centerSensorHtml(2, 'temperature', 'celsius', '[0, 50]') +
        centerSensorHtml(3, 'power', 'dBm', '[0, 100]') +
        centerSensorHtml(4, 'nodata', 'celsius', '[0, 50]') +
        centerSensorHtml(5, 'temperature', 'celsius', '[0, 50]') +
        '      <div id="item_1_6" class="rack-sensor" data-metric="alarm"' +
        '           data-unit="boolean" data-on-state="1">' +
        '        <div class="on alert-box hidden">On</div>' +
        '        <div class="off alert-box hidden">Off</div>' +
        '      </div>' +
        '    </div>' +
        '    <div class="rack-right rack-pdu rack-column"></div>' +
        '  </div>' +
        '</div>';

    var EMPTY_RACK_HTML =
        '<div class="rack" data-rackid="2">' +
        '  <div class="rack-body">' +
        '    <div class="rack-left rack-pdu rack-column"></div>' +
        '    <div class="rack-center rack-column"></div>' +
        '    <div class="rack-right rack-pdu rack-column"></div>' +
        '  </div>' +
        '</div>';

    describe('Rack sensors', function () {

        var originalGetJSON;
        var requests;
        var graphiteData;

        /*
         * Replaces $.getJSON with a fake Graphite render API. Each series
         * ends with a null datapoint, like the current minute usually does,
         * and the metric "nodata" has no series at all.
         */
        beforeEach(function () {
            graphiteData = {
                pdu: [[4.2, 1], [5.5, 2], [null, 3]],
                temperature: [[20.5, 1], [21.123, 2], [null, 3]],
                power: [[40, 1], [42.5, 2], [null, 3]],
                alarm: [[0, 1], [1, 2], [null, 3]]
            };
            requests = [];
            originalGetJSON = $.getJSON;
            $.getJSON = function (url, params) {
                requests.push(params.target);
                var results = params.target.filter(function (target) {
                    return graphiteData.hasOwnProperty(target);
                }).map(function (target) {
                    return {target: target, datapoints: graphiteData[target].slice()};
                });
                return $.Deferred().resolve(results).promise();
            };
        });

        afterEach(function () {
            $.getJSON = originalGetJSON;
            $('body').empty();
        });

        function addRack(html) {
            return $(html || RACK_HTML).appendTo('body');
        }

        function textValue($rack, id) {
            return $rack.find('#item_1_' + id + ' .textvalue').text();
        }

        function hasBar($rack, id) {
            return $rack.find('#item_1_' + id + ' .sparkline svg').length === 1;
        }

        function gauge($rack) {
            return $rack.find('.pdu-gauge svg');
        }

        describe('when updating a rack with the default options', function () {

            it('should show the latest value with a unit symbol', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.strictEqual(textValue($rack, 2), '21.12°');
            });

            it('should draw a bar only for celsius sensors', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.isTrue(hasBar($rack, 2));
                assert.isFalse(hasBar($rack, 3));
            });

            it('should show NaN when there is no data', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.strictEqual(textValue($rack, 4), 'NaN');
            });

            it('should draw the PDU gauge with the gradient', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.strictEqual(gauge($rack).attr('data-currentvalue'), '5.50');
                assert.match(gauge($rack).find('rect').attr('fill'), /^url\(#/);
            });

            it('should fetch the center and PDU sensors in separate requests', function () {
                RackSensors.updateRack(addRack());
                assert.deepEqual(requests, [
                    ['temperature', 'power', 'nodata', 'temperature', 'alarm'],
                    ['pdu']
                ]);
            });
        });

        describe('when updating a rack with the widget options', function () {

            it('should show the latest value without a unit symbol', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack, WIDGET_OPTIONS);
                assert.strictEqual(textValue($rack, 2), '21.12');
            });

            it('should draw a bar for all numeric sensors', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack, WIDGET_OPTIONS);
                assert.isTrue(hasBar($rack, 2));
                assert.isTrue(hasBar($rack, 3));
            });

            it('should show an empty text when there is no data', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack, WIDGET_OPTIONS);
                assert.strictEqual(textValue($rack, 4), '');
            });

            it('should draw the PDU gauge in a single colour', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack, WIDGET_OPTIONS);
                assert.strictEqual(gauge($rack).find('rect').attr('fill'), 'lightsteelblue');
            });
        });

        describe('when a boolean sensor is updated', function () {

            it('should show the on box if the value matches the on state', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.isFalse($rack.find('#item_1_6 .on').hasClass('hidden'));
                assert.isTrue($rack.find('#item_1_6 .off').hasClass('hidden'));
            });

            it('should show the off box if the value differs from the on state', function () {
                graphiteData.alarm = [[1, 1], [0, 2], [null, 3]];
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.isTrue($rack.find('#item_1_6 .on').hasClass('hidden'));
                assert.isFalse($rack.find('#item_1_6 .off').hasClass('hidden'));
            });
        });

        describe('when the same metric is shown twice in a rack', function () {
            it('should show the latest value for both sensors', function () {
                var $rack = addRack();
                RackSensors.updateRack($rack);
                assert.strictEqual(textValue($rack, 2), '21.12°');
                assert.strictEqual(textValue($rack, 5), '21.12°');
            });
        });

        describe('when the same rack is shown twice on a page', function () {
            it('should update both copies', function () {
                var $first = addRack();
                var $second = addRack();
                RackSensors.updateRack($first, WIDGET_OPTIONS);
                RackSensors.updateRack($second, WIDGET_OPTIONS);
                [$first, $second].forEach(function ($rack) {
                    assert.strictEqual(textValue($rack, 2), '21.12');
                    assert.strictEqual(gauge($rack).attr('data-currentvalue'), '5.50');
                });
            });
        });

        describe('when a rack has no sensors', function () {
            it('should not request any data', function () {
                RackSensors.updateRack(addRack(EMPTY_RACK_HTML));
                assert.deepEqual(requests, []);
            });
        });

        describe('when updating a single sensor', function () {

            it('should request only the metric of that sensor', function () {
                var $rack = addRack();
                RackSensors.updateSingleSensor($rack.find('#item_1_3'));
                assert.deepEqual(requests, [['power']]);
            });

            it('should update a center sensor with the given options', function () {
                var $rack = addRack();
                RackSensors.updateSingleSensor($rack.find('#item_1_3'), WIDGET_OPTIONS);
                assert.strictEqual(textValue($rack, 3), '42.5');
                assert.isTrue(hasBar($rack, 3));
            });

            it('should update a PDU sensor', function () {
                var $rack = addRack();
                RackSensors.updateSingleSensor($rack.find('#item_1_1'));
                assert.strictEqual(gauge($rack).attr('data-currentvalue'), '5.50');
            });
        });
    });
});
