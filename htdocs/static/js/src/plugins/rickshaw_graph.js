define([
    'libs/rickshaw.min',
    'libs-amd/text!resources/rickshawgraph/graphtemplate.hbs',
    'libs/handlebars'
], function(Rickshaw, Template) {
    
    var template = Handlebars.compile(Template);

    function RickshawGraph(container, url) {
        console.log('Creating new graph');
        container.innerHTML = template({
            graph_title: container.dataset.title,
            graph_unit: container.dataset.unit,
            graph_y_axis: container.dataset.unit
        });

        var g = new Rickshaw.Graph.Ajax({
            dataURL: url,
            element: container.getElementsByClassName('rickshaw-graph')[0],
            onData: function(data) {
                return prepareData(data, container.dataset);
            },
            onComplete: onComplete,
            renderer: 'line'
        });

        return g;
    }


    /**
     * Parse data from Graphite and format it so that Rickshaw understands it.
     */
    function prepareData(data, dataset) {
        var palette = new Rickshaw.Color.Palette({ scheme: 'colorwheel' });

        return data.map(function(series) {
            return { 
                name: series.target, 
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
            graph = request.graph;

        if (!graph.initialized) {
            var x_axis = new Rickshaw.Graph.Axis.Time({ 
                graph: graph,
                timeFixture: new Rickshaw.Fixtures.Time.Local()
            }),
                
                y_axis = new Rickshaw.Graph.Axis.Y({ 
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
                }),

                slider = new Rickshaw.Graph.RangeSlider({
                    graph: graph,
                    element: $element.siblings('.rickshaw-slider')[0]
                });
            
            graph.render();
            graph.initialized = true;
        }

    }

    return RickshawGraph;

});
