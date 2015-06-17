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
                    yFormatter: function(y) {
                        if (y === null || y === 0) {
                            return y;
                        }
                        var value = Number(y);
                        if (value < Number('0.01')) {
                            return value.toFixed(5);
                        }
                        return value.toFixed(2);
                    },
                    formatter: function(series, x, actualY, something, formattedY) {
                        var date = '<span class="date">' + new Date(x * 1000).toLocaleString() + '</span>',
		            swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>',
                            seriesValue = '<span class="series-value">' + getSeriesName(series.name) + ": " + formattedY + '</span>';
		        return swatch + seriesValue + '<br>' + date;
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

                preview = new Rickshaw.Graph.RangeSlider.Preview({
                    graph: graph,
                    element: $element.siblings('.rickshaw-preview')[0]
                });
            
            graph.render();
            graph.initialized = true;
        }

    }

    function getSeriesName(name) {
        var nameParts = name.split('.');
        if (nameParts[0] === 'nav') {
            return nameParts[nameParts.length - 1];
        }
        return name;
    }

    return RickshawGraph;

});
