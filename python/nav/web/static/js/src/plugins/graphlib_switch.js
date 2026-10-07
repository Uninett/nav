/*
 * Spike only: lets the "graphlib" URL parameter of the page choose which
 * library draws the Graphite graphs, so Rickshaw, uPlot and Chart.js can be
 * compared on real pages. Remove this module after the spike.
 *
 * - no graphlib parameter: Rickshaw, as before
 * - ?graphlib=uplot or ?graphlib=chartjs: that library only
 * - ?graphlib=all: all three side by side
 *
 * The sensor graphs draw Rickshaw with their own code, so they use
 * drawCompactGraphs instead of drawGraph.
 */
define(function (require) {

    const URI = require('libs/urijs/URI');
    const RickshawGraph = require('plugins/rickshaw_graph');

    const LIBRARIES = {
        rickshaw: {name: 'Rickshaw', className: 'rickshaw-container', Graph: RickshawGraph},
        uplot: {name: 'uPlot', className: 'nav-graph-container', Graph: require('plugins/timeseries_graph_uplot')},
        chartjs: {name: 'Chart.js', className: 'nav-graph-container', Graph: require('plugins/timeseries_graph_chartjs')},
    };


    function chosenLibraries() {
        const choice = new URI(window.location.href).query(true).graphlib;
        if (choice === 'all') {
            return Object.keys(LIBRARIES);
        }
        return choice in LIBRARIES ? [choice] : [];
    }


    /**
     * Replaces the content of the container with one labelled box per
     * library, side by side, or stacked if direction is 'column'. Returns
     * the boxes by library key.
     */
    function createBoxes(container, libraries, direction = 'row') {
        const boxes = {};
        const columns = libraries.map(key => {
            const column = document.createElement('div');
            column.style.flex = '1';
            column.style.minWidth = '0';

            const heading = document.createElement('h6');
            heading.textContent = LIBRARIES[key].name;

            const box = document.createElement('div');
            box.className = LIBRARIES[key].className;
            for (const attribute of ['title', 'unit']) {
                if (container.dataset[attribute]) {
                    box.dataset[attribute] = container.dataset[attribute];
                }
            }
            boxes[key] = box;

            column.append(heading, box);
            return column;
        });

        // The container is no longer a graph itself, only a row of graphs
        container.className = '';
        container.style.display = 'flex';
        container.style.flexDirection = direction;
        container.style.gap = '1em';
        container.replaceChildren(...columns);
        return boxes;
    }


    /**
     * Draws the graph with the chosen libraries. Takes the same arguments
     * as RickshawGraph and returns the Rickshaw graph, or the first graph.
     */
    function drawGraph(container, data, url, minValue) {
        const libraries = chosenLibraries();
        if (libraries.length === 0) {
            return new RickshawGraph(container, data, url, minValue);
        }
        if (!container._graphlibBoxes) {
            container._graphlibBoxes = createBoxes(container, libraries);
        }
        const graphs = libraries.map(key =>
            new LIBRARIES[key].Graph(container._graphlibBoxes[key], data, url, minValue));
        return graphs[0];
    }

    /**
     * Draws a compact graph with each chosen library except Rickshaw,
     * stacked in the container. Returns true if the caller should draw its
     * own Rickshaw graph too.
     */
    function drawCompactGraphs(container, data, url, minValue) {
        const libraries = chosenLibraries();
        const others = libraries.filter(key => key !== 'rickshaw');
        if (others.length > 0) {
            if (!container._graphlibBoxes) {
                container._graphlibBoxes = createBoxes(container, others, 'column');
            }
            others.forEach(key => new LIBRARIES[key].Graph(
                container._graphlibBoxes[key], data, url, minValue, {compact: true}));
        }
        return libraries.length === 0 || libraries.includes('rickshaw');
    }

    return {drawGraph, drawCompactGraphs};

});
