define(["libs-amd/text!resources/room/sensor.html", "libs-amd/text!resources/room/detail.html", "moment", "libs/handlebars", "libs/jquery", "libs/justgage.min", "libs/rickshaw.min"], function (template, detail_template, moment) {
    function SensorController($node) {
        this.$node = $node;
        this.url = this.$node.attr('data-url') + '&format=json';
        this.type = this.$node.attr('data-unit');
        this.sensorid = this.$node.attr('data-sensorid');
        this.sensorname = this.$node.attr('data-sensorname');

        this.maxValue = 50;  // Max value for graphs and gauges

        var $html = this.render();
        this.graphNode = $html.find('.rs-graphnode');
        this.graphYnode = $html.find('.rs-ynode');

        this.detailTemplate = Handlebars.compile(detail_template);

        this.update();
        var self = this;
        setInterval(function () {
            self.update();
        }, 60000);
    }

    SensorController.prototype = {
        render: function () {
            var compiledTemplate = Handlebars.compile(template),
                $html = $(compiledTemplate({
                    legend: this.sensorname,
                    sensorid: this.sensorid
                }));
            $html.appendTo(this.$node);
            return $html;
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
                title: ' ',
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
                width: 230,
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
                element: this.graphYnode.get(0),
                ticks: 4
            });
            // Enables details on hover.
            var self = this;
            var hoverDetail = new Rickshaw.Graph.HoverDetail({
                graph: graph,
                formatter: function (series, x, y) {
                    var date = moment(new Date(x * 1000)).format('DD-MM-YYYY HH:mm');
                    return self.detailTemplate({
                        color: series.color,
                        name: series.name,
                        date: date,
                        number: parseInt(y, 10)
                    });
                }
            });

            return graph;
        }
    };

    return SensorController;

});
