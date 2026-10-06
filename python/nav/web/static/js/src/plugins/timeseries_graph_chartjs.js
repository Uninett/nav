/*
 * A time series graph of Graphite render data, drawn with Chart.js.
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
 * Returns {chart, destroy()}.
 */
define(function (require) {

    const Chart = require('chartjs');
    const URI = require('libs/urijs/URI');
    const GraphUtils = require('graph-utils');
    require('chartjs-adapter-moment');  // Lets the time scale use moment
    require('chartjs-plugin-zoom');     // Registers the zoom plugin

    // The legend is drawn inside the canvas, so this is taller than the
    // uPlot graph to give the plot itself about the same height
    const HEIGHT = 230;


    function createDataset(series, index) {
        const {name, meta} = GraphUtils.parseSeriesMeta(series.target);
        const color = meta.color || GraphUtils.palette[index % GraphUtils.palette.length];
        const isArea = meta.renderer === 'area';
        const fillColor = isArea ? GraphUtils.withAlpha(color, 0.3) : color;
        return {
            label: GraphUtils.displayName(name),
            data: series.datapoints.map(([value, timestamp]) => ({x: timestamp * 1000, y: value})),
            borderColor: color,
            backgroundColor: fillColor,
            fill: isArea ? 'origin' : false,
            borderWidth: 1.5,
            pointRadius: 0,
            pointHoverRadius: 3,
            spanGaps: false,
            // The original colours, for highlightDataset
            navColors: {border: color, background: fillColor},
        };
    }


    /** Fades all datasets except the one at index. A null index shows all. */
    function highlightDataset(chart, index) {
        chart.data.datasets.forEach((dataset, i) => {
            const faded = index !== null && i !== index;
            const {border, background} = dataset.navColors;
            dataset.borderColor = faded ? GraphUtils.withAlpha(border, 0.3) : border;
            dataset.backgroundColor = faded ? GraphUtils.withAlpha(background, 0.1) : background;
        });
        chart.update('none');
    }


    /** Gives the canvas a text alternative for screen readers */
    function labelCanvas(canvas, title, unit, datasets) {
        const names = datasets.map(d => d.label).join(', ');
        const label = `${title ? title + ': ' : ''}${names}${unit ? ` (${unit})` : ''}`;
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', `Time series graph of ${label}`);
    }


    function TimeSeriesGraph(container, data, url, minValue) {
        container._navGraph?.destroy();
        container.replaceChildren();

        const params = new URI(url).query(true);
        const title = container.dataset.title || params.title || '';
        const unit = container.dataset.unit || params.vtitle || '';
        const datasets = data.map(createDataset);

        // Chart.js sizes the canvas to its parent, which must have its own size
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.height = `${HEIGHT}px`;
        const canvas = document.createElement('canvas');
        wrapper.appendChild(canvas);
        container.appendChild(wrapper);

        const chart = new Chart(canvas, {
            type: 'line',
            data: {datasets: datasets},
            options: {
                animation: false,
                maintainAspectRatio: false,
                interaction: {mode: 'index', intersect: false},
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            tooltipFormat: 'YYYY-MM-DD HH:mm',
                            displayFormats: {
                                minute: 'HH:mm',
                                hour: 'HH:mm',
                                day: 'D MMM',
                                month: 'MMM YYYY',
                            },
                        },
                        ticks: {maxRotation: 0},
                    },
                    y: {
                        min: minValue === 'auto' ? undefined : 0,
                        grace: '5%',
                        title: {display: Boolean(unit), text: unit},
                        ticks: {callback: GraphUtils.formatKMGT},
                    },
                },
                plugins: {
                    title: {display: Boolean(title), text: title},
                    legend: {
                        position: 'bottom',
                        onHover: (event, item, legend) => highlightDataset(legend.chart, item.datasetIndex),
                        onLeave: (event, item, legend) => highlightDataset(legend.chart, null),
                    },
                    tooltip: {
                        callbacks: {
                            label: item => `${item.dataset.label}: ${GraphUtils.formatValue(item.parsed.y, unit)}`,
                        },
                    },
                    zoom: {
                        zoom: {drag: {enabled: true}, mode: 'x'},
                    },
                },
            },
        });

        const resetZoom = () => chart.resetZoom();
        canvas.addEventListener('dblclick', resetZoom);
        labelCanvas(canvas, title, unit, datasets);

        const graph = {
            chart: chart,
            destroy() {
                canvas.removeEventListener('dblclick', resetZoom);
                chart.destroy();
                delete container._navGraph;
            },
        };
        container._navGraph = graph;
        return graph;
    }

    return TimeSeriesGraph;

});
