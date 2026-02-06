define(function(require, exports, module) {

    const d3Sparkline = require("plugins/d3_sparkline");


    /**
     * Based solely on the totally insane assumption that we have three banks
     * and that the first is the sum of the two following.
     */
    function PduController($navlet, dataUrl, metrics) {
        this.$navlet = $navlet;
        this.feedBack = this.$navlet.find('.alert-box.alert');
        this.timestamp = this.$navlet.find('.alert-update-timestamp span');
        this.dataUrl = dataUrl;
        this.limits = getLimits(this.$navlet.find('.pdu-load-status').data('limits')).sort().reverse();
        this.config = getConfig(this.limits.length);
        this.parameters = getParameters(metrics);
        this.isDestroyed = false;

        this.update();
        this.refreshHandler = this.update.bind(this);
        this.cleanupHandler = this.cleanup.bind(this);
        $navlet.on('refresh', this.refreshHandler);
        $navlet.on('htmx:beforeSwap', this.cleanupHandler);
    }

    PduController.prototype.cleanup = function() {
        if (this.isDestroyed) return;
        this.$navlet.off('refresh');
        this.$navlet.off('htmx:beforeSwap');
        this.isDestroyed = true;
    }

    PduController.prototype.update = function() {
        this.feedBack.hide();
        const self = this;

        const request = $.post(this.dataUrl, this.parameters, function(response) {
            _.each(response, function(data) {
                const $el = self.$navlet.find('[data-metric="' + data.target + '"]');

                const point = _.find(data.datapoints.reverse(), function(datapoint) {
                    return datapoint[0] !== null;
                });

                if (!point) {
                    $el.html('<small>No data</small>');
                    return;
                }
                const load = point[0];

                // Recalculate limits for the total column
                const limits = isTotal(data.target) ?
                    self.limits.map(t => t * 2) :
                    self.limits;

                d3Sparkline.bullet($el, [null, load].concat(limits), self.config);
            });
            self.timestamp.text(new Date().toLocaleString());
        });
        request.fail(function() {
            self.feedBack.html('Error fetching data').show();
        });
    };


    /** Constructs config for the sparkline */
    function getConfig(numLimits) {
        //                  green      yellow     red
        let rangeColors = ['#A5D6A7', '#FFEE58', '#EF9A9A'];
        // The splice is necessary because of the way sparklines.js applies the colors.
        rangeColors = rangeColors.splice(0, numLimits);

        return {
            performanceColor: '#333333',
            rangeColors: rangeColors.reverse(),
            tooltipFormatter: function(data) {
                const prefix = isTotal(data.$el.data('metric')) ? 'Total load' : 'Load';
                return `${prefix} ${data.values[1]} (limits: ${data.values.slice(2).reverse()})`;
            }
        };
    }

    /** Returns if the metric is the 'total'-metric, the metric that displays
     * the sum of the others */
    function isTotal(metric) {
        return strEndsWith(metric, 1);
    }


    function strEndsWith(str, suffix) {
        return str.match(suffix+"$") == suffix;
    }

    /**
     * @param {string} limit - comma separated string with numeric thresholds
     * @returns {Array.<integer>} An array of integer limits
     */
    function getLimits(limit) {
        if (typeof limit === 'number') {
            return [limit];  // single limit
        }
        return limit.length === 0 ? [] :
            limit.split(',').map(function(t) {return +t;});
    }

    /**
     * Constructs the parameters for the data request
     */
    function getParameters(metrics) {
        return {
            from: '-5min',
            format: 'json',
            target: metrics
        };
    }

    module.exports = PduController;

});
