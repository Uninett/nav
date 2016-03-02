define([
    'libs/rickshaw.min',
    'libs-amd/text!resources/rickshawgraph/graphtemplate.hbs',
    'nav-url-utils',
    'libs/handlebars'
], function (Rickshaw, Template, Utils) {

    var template = Handlebars.compile(Template);
    var resizeTimeout = 250;  // resize throttled at resizeTimeout ms

    function RickshawGraph(container, data, url) {
        container.innerHTML = template({
            graph_title: container.dataset.title,
            graph_unit: container.dataset.unit,
            graph_y_axis: container.dataset.unit
        });

        var element = container.getElementsByClassName('rickshaw-graph')[0];
        var graph = new Rickshaw.Graph({
            element: element,
            series: prepareData(data),
            renderer: 'line',
            stack: false  // Need to set this so that data is not stacked
        });

        addUtility(container, graph, url);
        graph.render();

        // Throttle resize
        var timer = null;
        window.addEventListener('resize', function () {
            if (!timer) {
                timer = setTimeout(function () {
                    resizeGraph(graph);
                    timer = null;
                }, resizeTimeout);
            }
        });

        return graph;
    }


    /** Add all utility stuff to the graph */
    function addUtility(container, graph, url) {
        var $element = $(graph.element);
        var urlParams = Utils.deSerialize(url);

        graph.series.forEach(function (serie) {
            serie.name = filterFunctionCalls(serie.name);
            // If this is a nav-metric, typically very long, display only the last two "parts"
            if (serie.name.substr(0, 4) === 'nav.') {
                var parts = serie.name.split('.');
                serie.name = [parts[parts.length - 2], parts[parts.length - 1]].join('.');
            }
        });

        new Rickshaw.Graph.Axis.Time({
            graph: graph,
            timeFixture: new Rickshaw.Fixtures.Time.Local()
        });

        new Rickshaw.Graph.Axis.Y({
            graph: graph,
            orientation: 'left',
            element: $element.siblings('.rickshaw-y-axis')[0],
            tickFormat: Rickshaw.Fixtures.Number.formatKMBT
        });

        // Display information about series when hovering over the graph
        new NavHover({
            graph: graph,
            yFormatter: siNumbers,
            urlparams: urlParams
        });

        // Add legend for each data series
        var legend = new Rickshaw.Graph.Legend({
            graph: graph,
            element: $element.siblings('.rickshaw-legend')[0]
        });


        // Highlight data series when user mouses over legend.
        new Rickshaw.Graph.Behavior.Series.Highlight({
            graph: graph,
            legend: legend
        });

        // Toggle visibility of data series
        new Rickshaw.Graph.Behavior.Series.Toggle({
            graph: graph,
            legend: legend
        });

        // Add preview of all data that can be zoomed with sliders.
        var preview = new Rickshaw.Graph.RangeSlider.Preview({
            graph: graph,
            element: $element.siblings('.rickshaw-preview')[0]
        });

        updateMeta(container, urlParams);

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
     * Series names are often wrapped in function calls. Remove the calls.
     * If there is a space in the function call, then we're fucked.
     * Ex:
     * keepLastValue(nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime)
     * => nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime
     */
    function filterFunctionCalls(name) {
        var match = name.match(/\w+\(([^ ]+)\)(.*)/);
        if (match) {
            name = filterFunctionCalls(match[1]) + match[2];
        }
        return name;
    }


    /**
     * Update the title and unit based on url-parameters.
     * @param {HTMLElement} container - The rickshaw container element
     * @param {object} params - object containing all url parameters
     */
    function updateMeta(container, params) {
        var $container = $(container);
        // Try to set title
        if (!$container.data('title') && params.title && params.title.length > 0) {
            $container.find('.rickshaw-title').html(params.title[0]);
        }
        // Try to set units on y-axis
        if (!$container.data('unit') && params.vtitle && params.vtitle.length > 0) {
            $container.find('.rickshaw-y-axis-term').html(params.vtitle[0]);
        }
        return params;
    }


    /**
     * Parse data from Graphite and format it so that Rickshaw understands it.
     */
    function prepareData(data) {
        var palette = new Rickshaw.Color.Palette({scheme: 'munin'});

        return data.map(function (series, index) {
            return {
                key: index,
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


    /** Create a hover detail that displays all series at the same time */
    var NavHover = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
        initialize: function ($super, args) {
            $super(args);
            this.urlparams = args.urlparams;
        },

        createHoverElements: function (args) {
            if (typeof this.hoverElements !== 'undefined') {
                return this.hoverElements;
            }
            var container = document.createElement('div');
            container.className = 'item';

            var date = document.createElement('span');
            date.className = 'date';

            var lines = {};
            var dots = {};

            this.graph.series.forEach(function (serie) {
                lines[serie.key] = document.createElement('div');

                var dot = document.createElement('div');
                dot.style.borderColor = serie.color;
                dot.className = 'dot';
                dots[serie.key] = dot;
            });

            this.hoverElements = {
                container: container,
                date: date,
                lines: lines,
                dots: dots
            };

            return this.hoverElements;
        },

        formatter: function (series, x, actualY, something, formattedY) {
            var unit = 'vtitle' in this.urlparams ? this.urlparams.vtitle[0] : '';
            // If the formatted y-value contains a symbol, we do not want a spacer value
            var spacer = isNaN(+formattedY) ? '' : ' ';
            var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>',
                seriesValue = '<span class="series-value">' + series.name + ": " + formattedY + spacer + unit + '</span>';
            return swatch + seriesValue;
        },

        render: function (args) {
            var hoverElements = this.createHoverElements(args);
            var container = hoverElements.container,
                date = hoverElements.date;

            // Put a date at the top of the container
            container.innerHTML = '';
            date.innerHTML = new Date(args.points[0].value.x * 1000).toLocaleString();
            container.appendChild(date);

            // Add all targets and dots
            args.points.sort(function (a, b) {
                return a.order - b.order;
            }).forEach(function (point, index) {
                var series = point.series;
                var actualY = series.scale ? series.scale.invert(point.value.y) : point.value.y;

                // Each line describes a target
                var line = hoverElements.lines[index];
                line.innerHTML = this.formatter(series, point.value.x, actualY, point.formattedXValue, point.formattedYValue, point);
                container.appendChild(line);

                // Place dots - remember that they are not part of container
                var dot = hoverElements.dots[index];
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

    var siNumbers = function(y, toInteger, spacer) {
        if (y === null || y === 0) {
            return y;
        }

        var precision = typeof toInteger === 'undefined' ? 2: 0;
        var space = typeof spacer === 'undefined' ? ' ': spacer;
        var convert = function(value, converter) {
            return (value / converter).toFixed(precision);
        };

        var value = Number(y);
        if (value >= 1000000000000) { return convert(value, 1000000000000) + space + "T"; }
        else if (value >= 1000000000) { return convert(value, 1000000000) + space + "G"; }
        else if (value >= 1000000) { return convert(value, 1000000) + space + "M"; }
        else if (value >= 1000) { return convert(value, 1000) + space + "k"; }
        else if (value <= 0.000001) { return convert(value, 1/1000000 ) + space + "µ"; }
        else if (value <= 0.01) { return convert(value, 1/1000) + space + "m"; }
        else if (value <= 1) { return value.toFixed(3); }  // This is inconsistent
        else { return value.toFixed(precision); }
    };

    return RickshawGraph;

});
