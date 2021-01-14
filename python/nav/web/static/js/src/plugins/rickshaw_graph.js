define([
    'libs/rickshaw.min',
    'libs-amd/text!resources/rickshawgraph/graphtemplate.hbs',
    'libs/urijs/URI',
    'rickshaw-utils',
    'libs/handlebars'
], function (Rickshaw, Template, URI, RickshawUtils, Handlebars) {

    var template = Handlebars.compile(Template);
    var resizeTimeout = 250;  // resize throttled at resizeTimeout ms

    function RickshawGraph(container, data, url, minValue) {
        container.innerHTML = template({
            graph_title: container.dataset.title,
            graph_unit: container.dataset.unit,
            graph_y_axis: container.dataset.unit
        });

        var element = container.getElementsByClassName('rickshaw-graph')[0];
        var graph = new Rickshaw.Graph({
            element: element,
            series: RickshawUtils.createSeries(data),
            renderer: 'line',
            min: typeof minValue === 'undefined' ? 0 : minValue,
            stack: false  // Need to set this so that data is not stacked
        });

        addUtility(container, graph, url);
        graph.render();

        // Throttle resize
        var timer = null;
        $(window).on('resize', function () {
            if (!timer) {
                timer = setTimeout(function () {
                    RickshawUtils.resizeGraph(graph);
                    timer = null;
                }, resizeTimeout);
            }
        });

        return graph;
    }


    function buildObject(parts) {
        var obj = {};
        for(var i = 0; i < parts.length; i++) {
            var keyValue = parts[i].split('=');
            obj[keyValue[0]] = keyValue[1];
        }
        return obj;
    }

    function getSeriesMeta(name) {
        return name.split(';;');
    }

    /** Add all utility stuff to the graph */
    function addUtility(container, graph, url) {
        var $element = $(graph.element);
        var urlParams = URI.parseQuery(url);

        graph.setRenderer('multi');
        graph.series.forEach(function (serie) {
            var metaParts = getSeriesMeta(serie.name),
                name = metaParts.pop(),
                meta = buildObject(metaParts);
            serie.key = name;
            serie.name = RickshawUtils.filterFunctionCalls(name);
            serie.renderer = meta.renderer ? meta.renderer : 'line';

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
            tickFormat: RickshawUtils.formatKMGT
        });

        // Display information about series when hovering over the graph
        new NavHover({
            graph: graph,
            yFormatter: RickshawUtils.siNumbers,
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


    /**
     * Update the title and unit based on url-parameters.
     * @param {HTMLElement} container - The rickshaw container element
     * @param {object} params - object containing all url parameters
     */
    function updateMeta(container, params) {
        var $container = $(container);
        // Try to set title
        if (!$container.data('title') && params.title) {
            $container.find('.rickshaw-title').html(params.title);
        }
        // Try to set units on y-axis
        if (!$container.data('unit') && params.vtitle) {
            $container.find('.rickshaw-y-axis-term').html(params.vtitle);
        }
        return params;
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
            var unit = 'vtitle' in this.urlparams ? this.urlparams.vtitle : '';
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
            }).forEach(function (point) {
                var series = point.series;
                var actualY = series.scale ? series.scale.invert(point.value.y) : point.value.y;

                // Each line describes a target
                var line = hoverElements.lines[series.key];
                line.innerHTML = this.formatter(series, point.value.x, actualY, point.formattedXValue, point.formattedYValue, point);
                container.appendChild(line);

                // Place dots - remember that they are not part of container
                var dot = hoverElements.dots[series.key];
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

    return RickshawGraph;

});
