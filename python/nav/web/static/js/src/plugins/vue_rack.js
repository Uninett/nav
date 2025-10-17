define(function (require) {
    var Vue = require('vue');
    var sparkline = require('jquery-sparkline');
    var LinearGauge = require('plugins/linear_gauge');
    var rackTemplate = require('libs-amd/text!resources/vue/environment_rack.html');
    var rackItemTemplate = require('libs-amd/text!resources/vue/environment_rack_item.html');
    var rackPduTemplate = require('libs-amd/text!resources/vue/environment_rack_pdu_item.html');


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


    /** Gets the first relevant value from the datapoints */
    function getValue(datapoints) {
        var point = _.find(datapoints.reverse(), function (datapoint) {
            return datapoint[0] != null;
        });

        return point ? point[0] : null;
    }


    var RackPduItem = {
        template: rackPduTemplate,
        props: ['item'],

        methods: {
            createGauge: function () {
                var self = this;
                return new LinearGauge({
                    element: $(self.$el).find('.pdu-gauge')[0],
                    precision: 2,
                    color: 'lightsteelblue',
                    height: 100,
                    max: self.item.display_range[1]
                });
            }
        },
        watch: {
            'item.value': function () {
                if (!this.gauge) {
                    this.gauge = this.createGauge();
                }
                this.gauge.update(this.item.value);
            }
        }

    };

    var RackItem = {
        template: rackItemTemplate,
        props: ['item'],
        methods: {
            drawSparkline: function () {
                var max = this.item.display_range[1];
                $(this.$el).find('.sparkline').sparkline([null, this.item.value, max], {
                    type: 'bullet',
                    performanceColor: 'lightsteelblue',
                    rangeColors: ['#fff'],
                    width: '100%',
                    tooltipFormatter: function () {
                        return "";
                    }
                });
            }
        },
        watch: {
            'item.value': function () {
                if (this.item.unit_of_measurement != 'boolean') {
                    this.item.value = round(this.item.value);
                    this.drawSparkline();
                }
            }
        }
    };

    var Rack = {
        template: rackTemplate,
        components: {
            'left-item': RackPduItem,
            'center-item': RackItem,
            'right-item': RackPduItem
        },
        props: ['rack'],
        methods: {
            /** Loads Graphite data for all items in the rack updates by setting value */
            loadGraphiteData: function () {
                var rackitems = _.union(
                    this.rack.configuration.left,
                    this.rack.configuration.center,
                    this.rack.configuration.right);
                var url = '/graphite/render';
                var request = $.getJSON(url,
                    {
                        target: rackitems.map(function (obj) {
                            return obj.metric;
                        }),
                        format: 'json',
                        from: '-5min',
                        until: 'now'
                    });
                request.done(function (data) {
                    var mapping = {};
                    data.forEach(function (result) {
                        mapping[result.target] = result.datapoints;
                    });
                    rackitems.forEach(function (obj) {
                        if (mapping[obj.metric]) {
                            Vue.set(obj, 'value', getValue(mapping[obj.metric]));
                        }
                    });
                });

            }
        },
        watch: {
            rack: function () {
                var oneMinute = 60 * 1000;
                this.loadGraphiteData();
                setInterval(this.loadGraphiteData, oneMinute);
                // console.log(this);
            }
        }
    };

    return Rack;

    /* Example usage
    var vm = new Vue({
        el: '#test',
        data: {
            racks: [],
            rack: null,
            id: 306
        },
        components: {
            'my-rack': Rack
        },
        methods: {
            loadRacks: function () {
                var self = this;
                $.getJSON('/api/1/rack/', function (data) {
                    self.racks = data.results;
                });
            },
            loadRack: function () {
                var self = this;
                $.getJSON('/api/1/rack/' + this.id, function (data) {
                    console.log(data);
                    self.rack = data;
                });
            }
        },
        mounted: function () {
            // this.loadRacks();
            this.loadRack();
        }
    });
     */

});
