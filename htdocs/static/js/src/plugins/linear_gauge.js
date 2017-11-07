define(function (require, exports, module) {

    var d3 = require('d3');

    /* Need a random id for the gradient */
    function guid() {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
                .toString(16)
                .substring(1);
        }
        return 'g' + s4() + s4() + '-' + s4() + '-' + s4() + '-' +
            s4() + '-' + s4() + s4() + s4();
    }

    /* Draw a vertical gauge that animates value changes */

    function LinearGauge(config) {
        this.element = config.element || document.querySelector('#' + config.nodeId);
        this.url = config.url || null;
        this.max = config.max || 8;
        this.height = config.height || 150;
        this.width = config.width || 40;
        this.animationSpeed = 1500;
        this.refreshInterval = 60;  // In seconds
        this.precision = config.precision || null;  // Number of decimals for value
        this.threshold = config.threshold || null;
        this.color = config.color;  // Set a single color instead of using the gradient
        this.gradientId = guid();
        this.fill = config.color ? this.color : 'url(#' + this.gradientId + ')';

        this.container = d3.select(this.element).append('svg')
            .attr('width', this.width).attr('height', this.height)
            .style('background-color', '#eee')
            .style('border', '1px solid #aaaaaa');
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
            }).attr('fill', this.fill);

        // Draw value on bar
        this.barText = groupEnter.append('text')
            .attr('fill', '#555')
            .attr('text-anchor', 'middle')
            .attr('x', this.width / 2).attr('y', function (d) {
                return self.y(d) + 3;
            }).attr('dy', '0.85em').text(function (d) {
                return d;
            });

        // Draw a line to better indicate value
        this.barLine = groupEnter.append('line')
            .attr('stroke', '#555')
            .attr('x1', 0).attr('y1', function (d) {
                return self.y(d);
            }).attr('x2', this.width).attr('y2', function (d) {
                return self.y(d);
            });

        if (this.url !== null) {
            setInterval(function () {
                self.loadData();
            }, this.refreshInterval * 1000);
            this.loadData();
        } else {
            self.update(0);
        }
    }

    LinearGauge.prototype = {
        createGradient: function () {
            /* Create gradient to indicate severity of value */
            var gradient = this.container
                .append("svg:defs").append("svg:linearGradient")
                .attr("id", this.gradientId).attr("x1", "100%").attr("y1", "100%")
                .attr("x2", "100%").attr("y2", "0%").attr('gradientUnits', 'userSpaceOnUse');
            gradient.append("svg:stop").attr("offset", "0%").attr("stop-color", "lightgreen");
            gradient.append("svg:stop").attr("offset", "50%").attr("stop-color", "yellow");
            gradient.append("svg:stop").attr("offset", "100%").attr("stop-color", "red");
        },
        loadData: function() {

            var self = this;
            d3.json(this.url, function (json, error) {
                var datapoints = json[0].datapoints,
                    value = datapoints[datapoints.length - 1][0] || datapoints[datapoints.length - 2][0];

                if (self.precision !== null) {
                    value = new Number(value).toFixed(self.precision);
                }
                self.update(value);
            });
    /*
             var value = Math.floor(Math.random() * (this.max + 1));
             this.update([value]);
    */
        },
        update: function (data) {
            var self = this;

            if (this.precision != null && data > 0) {
                data = data.toFixed(this.precision);
            }

            // Set a data attribute to indicate current value
            this.container.attr('data-currentvalue', data);

            // Update and transition bar
            this.bar.data([data])
                .transition()
                .duration(this.animationSpeed)
                .attr('y', function (d) {
                    return self.y(d);
                }).attr('height', function (d) {
                    return self.height - self.y(d);
                });

            /* Make bar red if threshold is passed */
            if (this.threshold && data > this.threshold) {
                this.bar.attr('fill', 'red');
                this.thresholdPassed = true;
            } else if (this.thresholdPassed && data < this.threshold) {
                this.bar.attr('fill', self.fill);
            }

            // Update and transition value
            var fontSize = '16px';
            if (data > 10) { fontSize = '14px'; }
            if (data > 100) { fontSize = '12px'; }

            this.barText.data([data])
                .transition()
                .duration(this.animationSpeed)
                .attr('style', 'font-size: ' + fontSize)
                .attr('y', function (d) {
                    if (d > self.max) {
                        return self.y(self.max) + 3;
                    } else if (d > (self.max * 0.5)) {
                        return self.y(d) + 3;
                    } else {
                        return self.y(d) - 20;
                    }
                }).text(function (d) {
                    return d;
                });

            // Update and transition line
            this.barLine.data([data])
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
