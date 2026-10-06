/*
 * A time series graph of Graphite render data, drawn with uPlot.
 *
 *   new TimeSeriesGraph(container, data, url, minValue)
 *
 * - container: the element to draw in. A graph that is already there is
 *   destroyed first, so the same container can be drawn into again.
 * - data: Graphite render JSON, [{target, datapoints: [[value, ts], ...]}].
 * - url: the URL the data came from. Its "title" and "vtitle" (unit)
 *   parameters are used unless the container has data-title or data-unit.
 * - minValue: undefined to start the Y axis at 0, or 'auto' to fit the data.
 *
 * Returns {uplot, destroy()}.
 */
/* global ResizeObserver */
define(function (require) {

    // Capitalised, because jshint wants constructors to start with a capital letter
    const UPlot = require('uplot');
    const URI = require('libs/urijs/URI');
    const GraphUtils = require('graph-utils');

    const HEIGHT = 200;

    /*
     * Time axis labels with a 24-hour clock. Each row is: tick step in
     * seconds, label format, then the second line to add where the year,
     * month, day, hour, minute or second changes, and the mode. See "axes"
     * in uPlot's documentation.
     */
    const TIME_AXIS_VALUES = [
        [3600 * 24 * 365, '{YYYY}', null, null, null, null, null, null, 1],
        [3600 * 24 * 28, '{MMM}', '\n{YYYY}', null, null, null, null, null, 1],
        [3600 * 24, '{D} {MMM}', '\n{YYYY}', null, null, null, null, null, 1],
        [3600, '{HH}:{mm}', '\n{D} {MMM} {YYYY}', null, '\n{D} {MMM}', null, null, null, 1],
        [60, '{HH}:{mm}', '\n{D} {MMM} {YYYY}', null, '\n{D} {MMM}', null, null, null, 1],
        [1, '{HH}:{mm}:{ss}', '\n{D} {MMM} {YYYY}', null, '\n{D} {MMM}', null, null, null, 1],
    ];

    function createSeries(target, index, unit) {
        const {name, meta} = GraphUtils.parseSeriesMeta(target);
        const color = meta.color || GraphUtils.palette[index % GraphUtils.palette.length];
        return {
            label: GraphUtils.displayName(name),
            stroke: color,
            fill: meta.renderer === 'area' ? GraphUtils.withAlpha(color, 0.3) : undefined,
            width: 1.5,
            value: (self, value) => GraphUtils.formatValue(value, unit),
        };
    }


    /** The Y range when the axis starts at 0, with some room above the top value */
    function rangeFromZero(self, min, max) {
        return [0, max > 0 ? max * 1.05 : 1];
    }


    /** Gives the canvas a text alternative for screen readers */
    function labelCanvas(plot, title, unit, series) {
        const names = series.map(s => s.label).join(', ');
        const label = `${title ? title + ': ' : ''}${names}${unit ? ` (${unit})` : ''}`;
        const canvas = plot.root.querySelector('canvas');
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', `Time series graph of ${label}`);
    }


    /** The width inside the element's padding */
    function contentWidth(element) {
        const style = getComputedStyle(element);
        const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
        return Math.max(0, element.clientWidth - padding);
    }


    /**
     * Resizes the plot when the container's width changes, at most once per
     * animation frame. This also draws the plot at the right size when a
     * hidden container, such as a closed tab, is shown.
     */
    function followWidth(container, plot) {
        let frame = null;
        const observer = new ResizeObserver(() => {
            if (frame !== null) {
                return;
            }
            frame = requestAnimationFrame(() => {
                frame = null;
                const width = contentWidth(container);
                if (width !== plot.width) {
                    plot.setSize({width: width, height: HEIGHT});
                }
            });
        });
        observer.observe(container);
        return {
            disconnect() {
                cancelAnimationFrame(frame);
                observer.disconnect();
            },
        };
    }

    function TimeSeriesGraph(container, data, url, minValue) {
        container._navGraph?.destroy();
        container.replaceChildren();

        const params = new URI(url).query(true);
        const title = container.dataset.title || params.title || '';
        const unit = container.dataset.unit || params.vtitle || '';
        const series = data.map((graphiteSeries, index) =>
            createSeries(graphiteSeries.target, index, unit));

        const plot = new UPlot({
            width: contentWidth(container),
            height: HEIGHT,
            title: title,
            series: [{value: '{YYYY}-{MM}-{DD} {HH}:{mm}'}, ...series],
            scales: {
                x: {time: true},
                y: minValue === 'auto' ? {} : {range: rangeFromZero},
            },
            axes: [
                {values: TIME_AXIS_VALUES},
                {
                    label: unit,
                    size: 60,
                    values: (self, splits) => splits.map(GraphUtils.formatKMGT),
                },
            ],
            legend: {live: true},
            focus: {alpha: 0.3},
            cursor: {
                focus: {prox: 16},
                drag: {x: true, y: false},
            },
        }, GraphUtils.toColumnar(data), container);

        labelCanvas(plot, title, unit, series);
        const resizer = followWidth(container, plot);

        const graph = {
            uplot: plot,
            destroy() {
                resizer.disconnect();
                plot.destroy();
                delete container._navGraph;
            },
        };
        container._navGraph = graph;
        return graph;
    }

    return TimeSeriesGraph;

});
