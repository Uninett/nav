define(function (require, exports, module) {

    var d3 = require('d3');

    /*
     Gauge implementation in D3. Heavily inspired by JustGage - http://justgage.com/

     TODO: Scale fonts based on radius
     TODO: Proper inner shadow on both arcs.

     */

    function JohnGauge(config) {
        var node = config.node,
            radius = config.radius || 100,
            width = 2 * radius,
            ir = radius * 0.6,
            pi = Math.PI,
            min = config.min || 0,
            max = config.max || 100,
            value = config.value || 0,
            url = config.url || null,
            refreshInterval = config.refreshInterval || 60, // seconds
            invertScale = config.invertScale,
            thresholds = config.thresholds || [];

        this.symbol = config.symbol || '';
        this.unit = config.unit || '';
        this.animationSpeed = 1000;  // Speed of value transitions

        /* Create SVG element */
        var vis = d3.select(node).append('svg')
            .attr("width", width)
            .attr("height", radius)
            .append("svg:g")
            .attr("transform", "translate(" + radius + "," + radius + ")");
        this.vis = vis;

        /* Create linear scale for start and end points */
        this.myScale = d3.scale.linear().domain([min, max]).range([-90 * (pi/180), 90 * (pi/180)]);

        /* Create linear scale for color transitions */
        this.color = this.createColorScale(min, max, thresholds, invertScale);

        this.fontSizeScale = d3.scale.linear().domain([50, 150]).range([14, 30]);
        this.smallfontSizeScale = d3.scale.linear().domain([50, 150]).range([8, 20]);

        /* Define arc */
        this.arc = d3.svg.arc().outerRadius(radius).innerRadius(ir).startAngle(this.myScale(min));

        /* Create background arc with gradient */
        var gradientId = this.createGradient(node);
        vis.append('path')
            .datum({ endAngle: this.myScale(max)})
            .attr('d', this.arc)
            .attr('fill', 'url(#' + gradientId + ')');

        /* Create value arc */
        this.valueArc = vis.append('path')
            .datum({endAngle: this.myScale(min)})
            .attr('fill', this.color(min))
            .attr('opacity', '0.9')
            .attr('d', this.arc);

        /* Draw text elements */
        this.valueText = this.createTexts(radius, ir, min, max);

        /* Draw thresholds */
        this.drawThresholds(thresholds);

        /* If an url is set, fetch data from it */
        if (url !== null) {
            var self = this;
            setInterval(function () {
                self.loadData(url);
            }, refreshInterval * 1000);
            this.loadData(url);
        } else {
            /* Initialize gauge with given value */
            this.refresh(value);
        }
    }

    JohnGauge.prototype = {
        loadData: function (url) {
            var self = this;
            d3.json(url, function (error, json) {
                var datapoints = json[0].datapoints,
                    value = datapoints[datapoints.length - 1][0] ||
                            datapoints[datapoints.length - 2][0];
                self.refresh(value);
            });
        },
        refresh: function (inputValue) {
            var self = this;
            var value = Number(inputValue);

            if (inputValue === null) {
                this.valueText.text('N/A');
                value = 0;
            } else {
                this.valueText.text(+(value.toFixed(1)) + this.symbol);
            }

            /* Transition arc and color to new value */
            this.valueArc.transition().duration(this.animationSpeed).call(arcTween, value)
                .transition().duration(this.animationSpeed).attr('fill', this.color(value));

            function arcTween(transition, newValue) {
                /* Calculates end angles while transitioning */
                transition.attrTween('d', function (d) {
                    var interpolate = d3.interpolate(d.endAngle, self.myScale(newValue));
                    return function (t) {
                        d.endAngle = interpolate(t);
                        return self.arc(d);
                    };
                });
            }

        },
        createTexts: function (radius, ir, min, max) {
            /* Create text that displays value */
            var valueText = this.vis.append('text')
                .text(min + this.symbol)
                .attr('y', -ir/2 + this.fontSizeScale(radius) / 2)
                .attr('font-size', this.fontSizeScale(radius) + 'px')
                .attr('fill', 'black')
                .attr('font-weight', 'bold')
                .attr('text-anchor', 'middle'),

            /* Create text displaying min value */
                minText = this.vis.append('text')
                .text(min)
                .attr('fill', '#b3b3b3')
                .attr('font-size', this.smallfontSizeScale(radius) + 'px')
                .attr('y', '0')
                .attr('x', 5 - ir)
                .attr('text-anchor', 'start'),

            /* Create text displaying max value */
                maxText = this.vis.append('text')
                .text(max)
                .attr('fill', '#b3b3b3')
                .attr('font-size', this.smallfontSizeScale(radius) + 'px')
                .attr('y', '0')
                .attr('x', ir - 5)
                .attr('text-anchor', 'end');

            /* Create text displaying unit */
                maxText = this.vis.append('text')
                .text(this.addEllipsis(this.unit, 10))
                .attr('fill', '#b3b3b3')
                .attr('font-size', this.smallfontSizeScale(radius) + 'px')
                .attr('y', '0')
                .attr('text-anchor', 'middle');

            return valueText;
        },
        addEllipsis: function(text, maxLength) {
            if (text.length > maxLength) {
                return text.substr(0, maxLength - 3) + '...';
            }
            return text;
        },
        getDomain: function(min, max, steps) {
            step = (max - min) / (steps - 1);
            return _.range(steps).map(function(m) {
                return min + (step * m);
            });
        },
        /** Create special range where the mid-range between the > and < is
           considered "green" and the rest is considered out of bounds - "red"
           */
        getConfigTwoThresholds: function(values) {
            return {
                min: this.trimThreshold(_.find(values.thresholds, function(t) {
                    return t.substr(0, 1) === '<';
                })),
                max: this.trimThreshold(_.find(values.thresholds, function(t) {
                    return t.substr(0, 1) === '>';
                })),
                colors: ['#FF4136', '#FFDC00', '#2ECC40', '#FFDC00', '#FF4136']
            }
        },
        getConfigOneThreshold: function(values) {
            var invert = values.thresholds[0].substr(0, 1) === '<';
            var thresholds = values.thresholds;
            return {
                min: invert ? this.trimThreshold(thresholds[0]) : values.min,
                max: invert ? values.max : this.trimThreshold(thresholds[0]),
                colors: invert ? values.colors.reverse() : values.colors
            }
        },
        getConfigZeroThreshold: function(values) {
            return values;
        },
        createColorScale: function (min, max, thresholds, invert) {
            var defaults = {
                min: min,
                max: max,
                colors: ['#2ECC40', '#FFDC00', '#FF4136'],
                thresholds: thresholds
            }

            // Colorscale greatly varies based on thresholds.
            var lookup = {
                2: this.getConfigTwoThresholds.bind(this, defaults),
                1: this.getConfigOneThreshold.bind(this, defaults),
                0: this.getConfigZeroThreshold.bind(this, defaults)
            }

            var config = _.extend(defaults, lookup[thresholds.length]());
            var domain = this.getDomain(config.min, config.max, config.colors.length);

            /* Special case for negative minimum - let it start blue and then
               continue as normal after 0. This really doesn't work well with
               inverse or several thresholds */
            if (config.min < 0) {
                config.colors = ['#0000FF'].concat(defaults.colors);
                domain = [config.min, 0, config.max / 2, config.max];
            }

            if (invert) {
                colors.reverse();
            }

            var scale = d3.scale.linear()
                          .domain(domain)
                          .interpolate(d3.interpolateRgb)
                          .range(config.colors);
            scale.clamp(true);  // Dont extrapolate
            return scale;
        },
        createGradient: function (node) {
            /* Greate gradient for background arc */
            var gradientId = node.id + 'gradient';
            var grads = this.vis.append("defs")
                .append("radialGradient")
                .attr("gradientUnits", "userSpaceOnUse")
                .attr("cx", 0)
                .attr("cy", 0)
                .attr("r", "100%")
                .attr("id", gradientId);
            grads.append("stop").attr("offset", "10%").style("stop-color", "gainsboro");
            grads.append("stop").attr("offset", "50%").style("stop-color", "#edebeb");
            grads.append("stop").attr("offset", "90%").style("stop-color", "gainsboro");

            return gradientId;
        },
        drawThresholds: function (thresholds) {
            var self = this;
            thresholds
                .map(this.trimThreshold)
                .forEach(this.createLineFromValue, this);
        },
        createLineFromValue: function (value) {
            try {
                var points = this.getLineCoords(value);
                this.vis.append("line")
                    .attr('stroke-width', 1).attr('stroke', 'black')
                    .attr("x1", points.x1).attr("y1", points.y1)
                    .attr("x2", points.x2).attr("y2", points.y2);
            } catch (error) {
                console.log("Value outside max, cant draw threshold");
            }
        },
        getLineCoords: function (value) {
            /* Get x and y coordinates for a specific value */
            var path = this.arc({ endAngle: this.myScale(value)}),
                defs = path.split(' '),
                lineCoords = defs[3].split('A')[0].split('L'),
                startPoint = lineCoords[0].split(','),
                endPoint = lineCoords[1].split(',');

            return { x1: startPoint[0], y1: startPoint[1], x2: endPoint[0], y2: endPoint[1]};
        },
        trimThreshold: function(threshold) {
            return +threshold.replace(/\D/, '');
        }
    };


    return JohnGauge;

});
