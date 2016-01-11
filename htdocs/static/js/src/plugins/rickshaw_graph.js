define([
    'libs/rickshaw.min',
    'libs-amd/text!resources/rickshawgraph/graphtemplate.hbs',
    'nav-url-utils',
    'libs/handlebars'
], function(Rickshaw, Template, Utils) {

    var template = Handlebars.compile(Template);
    var resizeTimeout = 250;  // Throttle resize to trigger at most every resizeTimeout ms

    function RickshawGraph(container, url) {
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
            renderer: 'line',
            stack: false  // Need to set this so that data is not stacked
        });

        var timer = null;
        window.addEventListener('resize', function() {
            if (!timer) {
                timer = setTimeout(function() {
                    resizeGraph(g.graph);
                    timer = null;
                }, resizeTimeout);
            }
        });

        return g;
    }


    function resizeGraph(graph) {
        var boundingRect = graph.element.getBoundingClientRect();
        graph.configure({
            width: boundingRect.width,
            height: boundingRect.height
        });
        graph.render();
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


    var NavHover = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
        createHoverElements: function(args) {
            if (typeof this.hoverElements !== 'undefined') {
                return this.hoverElements;
            }
            var container = document.createElement('div');
            container.className = 'item';

            var date = document.createElement('span');
            date.className = 'date';

            var lines = {};
            var dots = {};

            this.graph.series.forEach(function(serie) {
                var line = document.createElement('div');
                lines[serie.name] = line;

                var dot = document.createElement('div');
                dot.style.borderColor = serie.color;
                dot.className = 'dot';
                dots[serie.name] = dot;
            });

            this.hoverElements = {
                container: container,
                date: date,
                lines: lines,
                dots: dots
            };

            return this.hoverElements;
        },

        formatter: function(series, x, actualY, something, formattedY) {
            var unit = this.unit || '';
            var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>',
                seriesValue = '<span class="series-value">' + series.name + ": " + formattedY + unit + '</span>';
	    return swatch + seriesValue;
        },

        render: function(args) {
            var hoverElements = this.createHoverElements(args);
            var container = hoverElements.container,
                date = hoverElements.date;

            // Put a date at the top of the container
            container.innerHTML = '';
            date.innerHTML = new Date(args.points[0].value.x * 1000).toLocaleString();
            container.appendChild(date);

            // Add all targets and dots
            args.points.sort(function(a, b) {
                return a.order - b.order;
            }).forEach(function(point) {
                var series = point.series;
	        var actualY = series.scale ? series.scale.invert(point.value.y) : point.value.y;

                // Each line describes a target
                var line = hoverElements.lines[point.name];
                line.innerHTML = this.formatter(series, point.value.x, actualY, point.formattedXValue, point.formattedYValue, point);
                container.appendChild(line);

                // Place dots - remember that they are not part of container
                var dot = hoverElements.dots[point.name];
                dot.style.top = this.graph.y(point.value.y0 + point.value.y) + 'px';
                dot.classList.add('active');
                this.element.appendChild(dot);
            }, this);

            // Decide on which side of line to put hover element
	    container.classList.remove('left', 'right');
	    container.classList.add('active', 'right');

            // Put element next to mouse
            container.style.top = args.mouseY + 'px';

            this.element.appendChild(container);
            this.show();

            // If it is positioned badly, change side
            if (this._calcLayoutError([container]) > 0) {
                container.classList.remove('right');
                container.classList.add('left');
            }

        }
    });

    var siNumbers = function(y, toInteger) {
        if (y === null || y === 0) {
            return y;
        }

        var precision = typeof toInteger === 'undefined' ? 2: 0;
        var convert = function(value, converter) {
            return (value / converter).toFixed(precision);
        };

        var value = Number(y);
        if (value >= 1000000000000) { return convert(value, 1000000000000) + " T"; }
	else if (value >= 1000000000) { return convert(value, 1000000000) + " G"; }
	else if (value >= 1000000) { return convert(value, 1000000) + " M"; }
	else if (value >= 1000) { return convert(value, 1000) + " K"; }
        else if (value <= 0.000001) { return convert(value, 1/1000000 ) +  " µ"; }
        else if (value <= 0.01) { return convert(value, 1/1000) +  " m"; }
        else if (value <= 0) { return value.toFixed(3); }  // This is inconsistent
        else { return value.toFixed(precision); }
    };


    /**
     * Add all functionality when ajax call returns
     */
    function onComplete(request) {
        var $element = $(request.args.element),
            graph = request.graph;

        var meta = updateMeta($element, request);

        if (!graph.initialized) {

            graph.series.forEach(function(serie) {
                serie.name = getSeriesName(serie.name);
            });

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

                hoverDetail = new NavHover({
	            graph: graph,
                    yFormatter: siNumbers
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


    /**
     * Update the title and term based on url-parameters.
     */
    function updateMeta($element, request) {
        var container = $element.closest('.rickshaw-container');
        var params = Utils.deSerialize(request.dataURL);
        if (!container.data('title')) {
            // Desperately try to set title
            var titleElement = container.find('.rickshaw-title');
            if (params.title) {
                titleElement.html(params.title);
            } else {
                var seriesNames = request.graph.series
                        .map(function(x){return getSeriesNotation(x.name);}).join(', ');
                titleElement.html(seriesNames);
            }
        }
        if (!container.data('unit')) {
            container.find('.rickshaw-y-axis-term').html(params.vtitle);
        }
        return params;
    }


    function getSeriesNotation(name) {
        return getSeriesName(name).split('.').pop();
    }


    function getSeriesName(name) {
        var result = name.match(/nav\.[^),]+/);
        return result ? result[0] : name;
    }

    return RickshawGraph;

});
