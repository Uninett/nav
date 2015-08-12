define([
    'libs/rickshaw.min',
    'libs-amd/text!resources/rickshawgraph/graphtemplate.hbs',
    'libs/handlebars'
], function(Rickshaw, Template) {
    
    var template = Handlebars.compile(Template);

    function RickshawGraph(container) {
        console.log('Creating new graph');
        this.innerHTML = template({
            graph_title: this.dataset.title,
            graph_unit: this.dataset.unit,
            graph_y_axis: this.dataset.unit || this.dataset.yaxis
        });

        var g = new Rickshaw.Graph.Ajax({
            dataURL: this.dataset.url,
            element: this.getElementsByClassName('rickshaw-graph')[0],
            onData: function(data) {
                return prepareData(data, container.dataset);
            },
            onComplete: onComplete,
            renderer: 'line'
        });
    }

    /**
     * Parse data from Graphite and format it so that Rickshaw understands it.
     */
    function prepareData(data, dataset) {
        var palette = new Rickshaw.Color.Palette();

        return data.map(function(series) {
            return { 
                name: dataset.unit || series.target, 
                color: palette.color(), 
                data: series.datapoints.map(convertToRickshaw)
            };
        });
    }

    /**
     * Rickshaw demands  {x: timestamp, y: value}
     * Graphite delivers [value, timestamp]
     */
    function convertToRickshaw(dataPoint) {
        return {
            x: dataPoint[1],
            y: dataPoint[0]
        };
    }


    /**
     * Add all functionality when ajax call returns
     */
    function onComplete(request) {
        var $element = $(request.args.element),

            graph = request.graph,

            x_axis = new Rickshaw.Graph.Axis.Time(
                { 
                    graph: graph,
                    timeFixture: new Rickshaw.Fixtures.Time.Local()
                }
            ),

            y_axis = new Rickshaw.Graph.Axis.Y(
                { 
                    graph: graph, 
                    orientation: 'left', 
                    element: $element.siblings('.rickshaw-y-axis')[0],
                    tickFormat: Rickshaw.Fixtures.Number.formatKMBT
                }),

            hoverDetail = new Rickshaw.Graph.HoverDetail({
	        graph: graph,
                xFormatter: function(x) {
                    return new Date(x * 1000).toLocaleString();
                }
            }),

            legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: $element.siblings('.rickshaw-legend')[0]
            }),

            // Toggle visibility of data series
            shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });

        graph.render();
    }

    return RickshawGraph;

});
