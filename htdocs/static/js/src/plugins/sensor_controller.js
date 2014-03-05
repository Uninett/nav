define(["moment", "libs/jquery", "libs/justgage.min", "libs/rickshaw.min"], function (moment) {
    function SensorController($node) {
        this.$node = $node;
        this.url = this.$node.attr('data-url') + '&format=json';
        this.type = this.$node.attr('data-unit');
        this.sensorid = this.$node.attr('data-sensorid');
        this.sensorname = this.$node.attr('data-sensorname');

        this.maxValue = 50;  // Max value for graphs and gauges

        this.createContainers();
        this.update();
        var self = this;
        setInterval(function () {
            self.update();
        }, 60000);
    }

    SensorController.prototype = {
        createContainers: function () {
            var currentContainer = $('<div>').addClass('current')
                    .attr('id', 'current' + this.sensorid)
                    .appendTo(this.$node),
                graphContainer = $('<div>').addClass('rs-graph')
                    .appendTo(this.$node),
                graphYAxis = $('<div>').addClass('rs-ynode')
                    .appendTo(graphContainer),
                graphNode = $('<div>').addClass('rs-graphnode')
                    .attr('id', 'graph' + this.sensorid)
                    .appendTo(graphContainer);

            if (this.type === 'celsius') {
                currentContainer.addClass('gauge');
            } else {
                currentContainer.addClass('number');
            }

            this.currentContainer = currentContainer;
            this.graphContainer = graphContainer;
            this.graphNode = graphNode;
            this.graphYnode = graphYAxis;
        },
        update: function () {
            this.loadData();
        },
        loadData: function () {
            var self = this;
            $.getJSON(this.url, function (data) {
                if (data && data.length) {
                    var datapoints = data[0].datapoints.map(function (point) {
                        return {
                            x: point[1],
                            y: point[0]
                        };
                    });
                    var last = datapoints[datapoints.length - 1].y || datapoints[datapoints.length - 2].y;
                    self.updateCurrent(last);
                    self.updateGraph(datapoints);
                }
            });
        },
        updateCurrent: function (value) {
            if (!this.current) {
                this.current = this.createCurrent(value);
            }
            this.current.refresh(value);
        },
        createCurrent: function (value) {
            return new JustGage({
                id: 'current' + this.sensorid,
                min: 0,
                value: value,
                max: this.maxValue,
                title: this.sensorname,
                label: 'Celcius'
            });
        },
        updateGraph: function (values) {
            if (!this.graph) {
                console.log('Creating graph');
                this.graph = this.createGraph();
            }
            this.graph.series[0].data = values;
            this.graph.render();
        },
        createGraph: function () {
            var graph = new Rickshaw.Graph({
                element: this.graphNode.get(0),
                width: 250,
                height: 150,
                renderer: 'line',
                max: this.maxValue,
                series: [{
                    color: 'steelblue',
                    data: [{x: 0, y: 0}], // Data is overridden on update
                    name: this.sensorname
                }]
            });
            // Time formatter for the x-axis
            var unit_formatter = {
                name: '6 hours',
                seconds: 3600 * 6,
                formatter: function (d) {
                    return moment(d).format('HH:mm');
                }
            };
            var x_axis = new Rickshaw.Graph.Axis.Time({
                graph: graph,
                timeUnit: unit_formatter
            });
            var y_axis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                orientation: 'left',
                element: this.graphYnode.get(0)
            });
            // Enables details on hover.
            var hoverDetail = new Rickshaw.Graph.HoverDetail({
                graph: graph,
                formatter: function (series, x, y) {
                    var date = '<span class="date">' + new Date(x * 1000).toString() + '</span>';
                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
                    var content = swatch + series.name + ": " + parseInt(y) + '<br>' + date;
                    return content;
                }
            });

            return graph;
        }
    };

    return SensorController;

});
