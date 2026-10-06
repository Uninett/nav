/** Helper functions for NAV's time series graphs, independent of the graph library */
define([], () => {

    /**
     * A categorical palette that people with colour blindness can tell apart
     * (Okabe-Ito). Series without a colour of their own get these in order.
     */
    const palette = [
        '#0072B2', '#E69F00', '#009E73', '#D55E00',
        '#CC79A7', '#56B4E9', '#F0E442', '#000000'
    ];

    // Rickshaw-only, removed together with Rickshaw
    /**
     * Create the series objects containing meta info about the series and
     * the datapoints formatted correctly.
     */
    function createSeries(data) {
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


    // Rickshaw-only, removed together with Rickshaw
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
     * Remove all function calls from a string. We do it recursively starting
     * at the innermost one
     */
    function removeFunctionCalls(string) {
        const functionRegex = /\w+\([^()]*\)/;
        if (!functionRegex.test(string)) {
            return string;
        }
        return removeFunctionCalls(string.replace(functionRegex, ''));
    }


    /**
     * Series names are often wrapped in function calls. Remove the calls.
     * Ex:
     * keepLastValue(nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime)
     * => nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime
     */
    function filterFunctionCalls(name) {
        // Metric names consist of letters, digits, "-" and "_" (nav.metrics.names)
        const seriesMatch = name.match(/nav\.[-.\w]+/);
        if (!seriesMatch) {
            return name;
        }
        // Remove all functions and return the rest
        return seriesMatch[0] + removeFunctionCalls(name);
    }


    /** NAVs way of presenting si-numbers */
    function siNumbers(y, toInteger, spacer = ' ') {
        if (y === null || y === 0) {
            return y;
        }

        const precision = toInteger === undefined ? 2 : 0;
        const convert = (value, converter) => (value / converter).toFixed(precision);

        const value = Number(y);
        const absvalue = Math.abs(value);
        if (absvalue >= 1e12) { return convert(value, 1e12) + spacer + "T"; }
        else if (absvalue >= 1e9) { return convert(value, 1e9) + spacer + "G"; }
        else if (absvalue >= 1e6) { return convert(value, 1e6) + spacer + "M"; }
        else if (absvalue >= 1e3) { return convert(value, 1e3) + spacer + "k"; }
        else if (absvalue <= 1e-10) { return convert(value, 1e-12) + spacer + "p"; }
        else if (absvalue <= 1e-7) { return convert(value, 1e-9) + spacer + "n"; }
        else if (absvalue <= 1e-4) { return convert(value, 1e-6) + spacer + "µ"; }
        else if (absvalue <= 0.01) { return convert(value, 1e-3) + spacer + "m"; }
        else { return value.toFixed(precision); }
    }

    // Replaces Rickshaw's builtin formatKMBT for tick formatting (as the B makes no sense)
    function formatKMGT(y) {
        const absY = Math.abs(y);
        if (absY >= 1e12) { return y / 1e12 + "T"; }
        else if (absY >= 1e9) { return y / 1e9 + "G"; }
        else if (absY >= 1e6) { return y / 1e6 + "M"; }
        else if (absY >= 1e3) { return y / 1e3 + "K"; }
        else if (absY < 1 && y > 0) { return y.toFixed(2); }
        else if (absY === 0) { return ''; }
        else { return y; }
    }

    // Rickshaw-only, removed together with Rickshaw
    function resizeGraph(graph) {
        var boundingRect = graph.element.getBoundingClientRect();
        graph.configure({
            width: boundingRect.width,
            height: boundingRect.height
        });
        graph.render();
    }


    /**
     * The backend can put metadata in front of a series name in the Graphite
     * alias, as key=value pairs separated by ";;". Splits
     * "renderer=area;;color=#f00;;name" into
     * {name: "name", meta: {renderer: "area", color: "#f00"}}.
     */
    function parseSeriesMeta(target) {
        const parts = target.split(';;');
        const name = parts.pop();
        const meta = {};
        for (const part of parts) {
            const [key, ...value] = part.split('=');
            meta[key] = value.join('=');
        }
        return {name, meta};
    }


    /**
     * The name to show for a series: function calls are removed, and NAV
     * metric paths, which are often very long, are cut to their last two parts.
     */
    function displayName(target) {
        const name = filterFunctionCalls(target);
        if (name.startsWith('nav.')) {
            return name.split('.').slice(-2).join('.');
        }
        return name;
    }


    /**
     * Converts Graphite's render data, [{target, datapoints: [[value, ts]]}],
     * to columns: [timestamps, values of series 1, values of series 2, ...].
     * The timestamps are the sorted union of all the series' timestamps. A
     * series without a value at a timestamp gets null there.
     */
    function toColumnar(graphiteData) {
        const series = graphiteData.map(s => new Map(
            s.datapoints.map(([value, timestamp]) => [timestamp, value])
        ));
        const timestamps = new Set();
        for (const values of series) {
            for (const timestamp of values.keys()) {
                timestamps.add(timestamp);
            }
        }
        const xs = [...timestamps].sort((a, b) => a - b);
        return [xs, ...series.map(values => xs.map(x => values.get(x) ?? null))];
    }


    /**
     * Returns a hex colour (#rgb or #rrggbb) as rgba() with the given alpha.
     * Other colours are returned unchanged.
     */
    function withAlpha(color, alpha) {
        let hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(color)?.[1];
        if (!hex) {
            return color;
        }
        if (hex.length === 3) {
            hex = [...hex].map(digit => digit + digit).join('');
        }
        const [red, green, blue] = [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16));
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
    }


    return {
        palette,
        parseSeriesMeta,
        displayName,
        toColumnar,
        withAlpha,
        filterFunctionCalls,
        removeFunctionCalls,
        siNumbers,
        formatKMGT,
        createSeries,
        convertToRickshaw,
        resizeGraph
    };

});
