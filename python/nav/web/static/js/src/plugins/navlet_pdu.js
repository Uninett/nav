define(function(require, exports, module) {

    var _sparkline = require("jquery-sparkline");


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

        this.update();
        $navlet.on('refresh', this.update.bind(this));  // navlet controller determines when to update
        $navlet.on('render', function(event, renderType){
            /* We need to unregister eventlistener, as it will not be removed
             when going into edit-mode, and thus we will have one for each time
             you have edited the widget. */
            if (renderType === 'EDIT') {
                $navlet.off('refresh');
            }
        });
    }

    PduController.prototype.update = function() {
        this.feedBack.hide();
        var self = this;

        var request = $.post(this.dataUrl, this.parameters, function(response) {
            _.each(response, function(data) {
                var $el = self.$navlet.find('[data-metric="' + data.target + '"]');

                var point = _.find(data.datapoints.reverse(), function(datapoint) {
                    return datapoint[0] !== null;
                });

                if (!point) {
                    $el.html('<small>No data</small>');
                    return;
                }
                var load = point[0];

                // Recalculate limits for the total column
                var limits = isTotal(data.target) ?
                    self.limits.map(function (t) { return t * 2; }) :
                    self.limits;

                $el.sparkline([null, load].concat(limits), self.config);
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
        var rangeColors = ['#A5D6A7', '#FFEE58', '#EF9A9A'];
        // The splice is necessary because of the way sparklines.js applies the colors.
        rangeColors = rangeColors.splice(0, numLimits);

        return {
            type: 'bullet',
            performanceColor: '#333333',
            rangeColors: rangeColors.reverse(),
            tooltipFormatter: function(data) {
                var prefix = isTotal(data.$el.data('metric')) ? 'Total load' : 'Load';
                return prefix + ' ' + data.values[1] + " (limits: " + data.values.slice(2).reverse() + ")";
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
