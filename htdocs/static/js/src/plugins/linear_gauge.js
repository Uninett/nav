define(['libs/d3.v2'], function () {

    /* Draw a vertical gauge that animates value changes */

    function LinearGauge(config) {
        this.nodeId = config.nodeId;
        this.url = config.url;
        this.max = config.max || 8;
        this.height = config.height || 150;
        this.width = config.width || 40;
        this.animationSpeed = 1500;
        this.refreshInterval = 60;  // In seconds

        this.container = d3.select('#' + this.nodeId).append('svg')
            .attr('width', this.width).attr('height', this.height);
        this.createGradient();

        var self = this;

        // Specify scaling for y-axis
        this.y = d3.scale.linear().domain([0, this.max]).range([this.height, 0]);

        // Set data to zero, add group element
        var group = this.container.selectAll('g'),
            groupUpdate = group.data([0]),
            groupEnter = groupUpdate.enter().append('g');

        // Draw bar that indicates value
        this.bar = groupEnter.append('rect').attr('y', function (d) {
                return self.y(d);
            }).attr('width', this.width).attr('height', function (d) {
                return self.height - self.y(d);
            }).attr('fill', 'url(#' + self.nodeId + 'gradient)');

        // Draw value on bar
        this.barText = groupEnter.append('text').attr('x', this.width / 2).attr('y', function (d) {
                return self.y(d) + 3;
            }).attr('dy', '0.85em').text(function (d) {
                return d;
            });

        // Draw a line to better indicate value
        this.barLine = groupEnter.append('line').attr('x1', 0).attr('y1', function (d) {
                return self.y(d);
            }).attr('x2', this.width).attr('y2', function (d) {
                return self.y(d);
            });

        setInterval(function () {
            self.loadData();
        }, this.refreshInterval * 1000);
        this.loadData();
    }

    LinearGauge.prototype = {
        createGradient: function () {
            /* Create gradient to indicate severity of value */
            var gradient = this.container
                .append("svg:defs").append("svg:linearGradient")
                .attr("id", this.nodeId + "gradient").attr("x1", "100%").attr("y1", "100%")
                .attr("x2", "100%").attr("y2", "0%").attr('gradientUnits', 'userSpaceOnUse');
            gradient.append("svg:stop").attr("offset", "0%").attr("stop-color", "lightgreen");
            gradient.append("svg:stop").attr("offset", "50%").attr("stop-color", "yellow");
            gradient.append("svg:stop").attr("offset", "100%").attr("stop-color", "red");
        },
	loadData: function() {

        var self = this;
        d3.json(this.url, function (json, error) {
            var datapoints = json[0].datapoints;
            value = datapoints[datapoints.length - 1][0] || datapoints[datapoints.length - 2][0];
            self.update([value]);
        });
/*
         var value = Math.floor(Math.random() * (this.max + 1));
         this.update([value]);
*/
    },
        update: function (data) {
            var self = this;

            // Update and transition bar
            this.bar.data(data)
                .transition()
                .duration(this.animationSpeed)
                .attr('y', function (d) {
                    return self.y(d);
                }).attr('height', function (d) {
                    return self.height - self.y(d);
                });

            // Update and transition value
            this.barText.data(data)
                .transition()
                .duration(this.animationSpeed)
                .attr('y', function (d) {
                    if (d > (self.max * 0.75)) {
                        return self.y(d) + 3;
                    } else {
                        return self.y(d) - 20;
                    }
                }).text(function (d) {
                    return d;
                });

            // Update and transition line
            this.barLine.data(data)
                .transition()
                .duration(this.animationSpeed)
                .attr('y1', function (d) {
                    return self.y(d);
                }).attr('y2', function (d) {
                    return self.y(d);
                });
        }
    };

    return LinearGauge;

});

