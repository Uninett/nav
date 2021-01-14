/** Helper functions for Rickshaw */
define([], function () {

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
     * Series names are often wrapped in function calls. Remove the calls.
     * Ex:
     * keepLastValue(nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime)
     * => nav.devices.buick_lab_uninett_no.ipdevpoll.1minstats.runtime
     */
    function filterFunctionCalls(name) {
        var serieMatch = name.match(/nav\.[.\w]+/);
        if (serieMatch) {
            var serie = serieMatch[0];
            // Remove all functions and return the rest
            return serie + removeFunctionCalls(name);
        } else {
            return name;
        }

    }


    /**
     * Remove all function calls from a string. We do it recursively starting
     * at the innermost one
     */
    function removeFunctionCalls(string) {
        var functionRegex = /(\w+\([^()]+\))/;
        var functionMatch = string.match(functionRegex);
        if (functionMatch) {
            string = string.replace(functionRegex, '');
            string = removeFunctionCalls(string);
        }
        return string;
    }


    /** NAVs way of presenting si-numbers */
    function siNumbers(y, toInteger, spacer) {
        if (y === null || y === 0) {
            return y;
        }

        var precision = typeof toInteger === 'undefined' ? 2: 0;
        var space = typeof spacer === 'undefined' ? ' ': spacer;
        var convert = function(value, converter) {
            return (value / converter).toFixed(precision);
        };

        var value = Number(y);
        var absvalue = Math.abs(value);
        if (absvalue >= 1000000000000) { return convert(value, 1000000000000) + space + "T"; }
        else if (absvalue >= 1000000000) { return convert(value, 1000000000) + space + "G"; }
        else if (absvalue >= 1000000) { return convert(value, 1000000) + space + "M"; }
        else if (absvalue >= 1000) { return convert(value, 1000) + space + "k"; }
        else if (absvalue <= 0.0000000001) { return convert(value, 1/1000000000000 ) + space + "p"; }
        else if (absvalue <= 0.0000001) { return convert(value, 1/1000000000 ) + space + "n"; }
        else if (absvalue <= 0.0001) { return convert(value, 1/1000000 ) + space + "µ"; }
        else if (absvalue <= 0.01) { return convert(value, 1/1000) + space + "m"; }
        else { return value.toFixed(precision); }
    }

    // Replaces Rickshaw's builtin formatKMBT for tick formatting (as the B makes no sense)
    function formatKMGT(y) {
        var abs_y = Math.abs(y);
        if (abs_y >= 1000000000000) { return y / 1000000000000 + "T" }
        else if (abs_y >= 1000000000) { return y / 1000000000 + "G" }
        else if (abs_y >= 1000000) { return y / 1000000 + "M" }
        else if (abs_y >= 1000) { return y / 1000 + "K" }
        else if (abs_y < 1 && y > 0) { return y.toFixed(2) }
        else if (abs_y === 0) { return '' }
        else { return y }
    };

    function resizeGraph(graph) {
        var boundingRect = graph.element.getBoundingClientRect();
        graph.configure({
            width: boundingRect.width,
            height: boundingRect.height
        });
        graph.render();
    }


    return {
        createSeries: createSeries,
        convertToRickshaw: convertToRickshaw,
        filterFunctionCalls: filterFunctionCalls,
        removeFunctionCalls: removeFunctionCalls,
        resizeGraph: resizeGraph,
        siNumbers: siNumbers,
        formatKMGT: formatKMGT
    };

});
