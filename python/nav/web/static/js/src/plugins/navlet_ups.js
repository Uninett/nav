define(function(require, exports, module) {

    /**
     * @param {jQuery} $navlet - The navlet element (the one with data-id)
     */
    function Poller($navlet) {
        var self = this;
        this.$navlet = $navlet;
        this.$updateTime = $navlet.find('.update-time');

        // Build sensors dict where metric path is key and node is value
        this.sensors = {};
        $navlet.find('[data-metric]').each(function() {
            var $node = $(this);
            self.sensors[$node.attr('data-metric')] = $node;
        });

        this.metricList = _.keys(this.sensors);
        this.isDestroyed = false;

        // Run collection and listen to events
        this.update();
        this.refreshHandler = this.update.bind(this);
        this.cleanupHandler = this.cleanup.bind(this);
        $navlet.on('refresh', this.refreshHandler);
        $navlet.on('htmx:beforeSwap', this.cleanupHandler);
    }

    Poller.prototype.cleanup = function() {
        if (this.isDestroyed) return;
        this.$navlet.off('refresh');
        this.$navlet.off('htmx:beforeSwap');
        this.isDestroyed = true;
    }

    Poller.prototype.update = function() {
        var self = this;
        var request = $.post(NAV.graphiteRenderUrl,
                             {target: this.metricList, from: '-5min', format: 'json'});
        request.done(function(response){
            // For each metric, update the related node
            response.forEach(function(data) {
                var datapoints = data.datapoints.reverse();
                // Find the first point that has data and use that.
                var point = _.find(datapoints, function(point){
                    return point[0] !== null;
                });
                var $node = self.sensors[data.target];
                var value = point ? point[0] : 'N/A';

                // Convert value if applicable
                var converted = convertValue($node, value);
                if (_.isArray(converted)) {
                    value = converted[0] || 'N/A';
                    $node.parent().find('.unit-of-measurement').text(converted[1]);
                }

                // If value is less than 200 and it is a voltage (indicated in template), mark it
                if (value < 200) {
                    $node.closest('.ups-voltage-indicator').addClass('marklow');
                }

                $node.html(value);
            });
            self.$updateTime.html(new Date().toLocaleString());
        });
    };

    /** Convert value based on unit of measurement. Converted values returns as
     * an array where the first value is the converted value and the second is
     * the new unit */
    function convertValue($node, value) {
        var uom = $node.data('uom');
        var convert = {
            Seconds: function() {
                // Seconds is converted to minutes
                return [(+value / 60).toFixed(0), 'Minutes'];
            }
        };
        try {
            return convert[uom]();
        } catch (e) {
            return value;
        }
    }

    module.exports = Poller;


});
