define([
    'chartjs',
    'chartjs-adapter-moment',
    'chartjs-plugin-zoom'
], function (Chart) {
    describe("Chart.js loading", function () {
        let canvas;
        let chart;

        beforeEach(function () {
            canvas = document.createElement('canvas');
            document.body.appendChild(canvas);
        });

        afterEach(function () {
            chart?.destroy();
            chart = undefined;
            canvas.remove();
        });

        it("should register the zoom plugin", function () {
            assert.isDefined(Chart.registry.getPlugin('zoom'));
        });

        it("should format dates with the moment adapter", function () {
            const adapter = new Chart._adapters._date();
            assert.equal(adapter.format(Date.UTC(2026, 0, 2), 'YYYY'), '2026');
        });

        it("should draw a time series chart with drag zoom", function () {
            chart = new Chart(canvas, {
                type: 'line',
                data: {datasets: [{data: [{x: 0, y: 1}, {x: 60000, y: 2}]}]},
                options: {
                    animation: false,
                    scales: {x: {type: 'time'}},
                    plugins: {zoom: {zoom: {drag: {enabled: true}, mode: 'x'}}}
                }
            });
            assert.isFunction(chart.resetZoom);
        });
    });
});
