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

        // Run collection and listen to events
        this.update();
        $navlet.on('refresh', this.update.bind(this));
        this.$navlet.on('render', function(event, renderType){
            /* We need to unregister refresh listener, as it will not be removed
             when going into edit-mode, and thus we will have one for each time
             you have edited the widget. */
            if (renderType === 'EDIT') {
                self.$navlet.off('refresh');
            }
        });
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
                var value = point ? point[0] : 'N/A';
                self.sensors[data.target].html(value);
            });
            self.$updateTime.html(new Date().toLocaleString());
        });
    };

    module.exports = Poller;


});
