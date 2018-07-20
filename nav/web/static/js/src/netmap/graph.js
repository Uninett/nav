define([
    'netmap/collections',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collections) {

    /**
     * This is the backbone model representing the topology graph itself,
     * without any filters or options from the netmap-view.
     * It is placed in its own file to avoid a circular dependency.
     */
    var Graph = Backbone.Model.extend({

        defaults: {
            layer: 2,
            viewId: null,
            baseUrl: 'graph/layer',
            nodeCollection: new Collections.NodeCollection(),
            linkCollection: new Collections.LinkCollection(),
            vlanCollection: new Collections.VlanCollection(),
            // Determines what locations we fetch traffic data for, as this is a
            // somewhat expensive operation.
            locations: [],
            filter_categories: [
            // temp deactivating to avoid overhead
                {name: 'GSW', checked: false},
                {name: 'GW', checked: false},
                {name: 'SW', checked: true},
                {name: 'OTHER', checked: true},
                {name: 'WLAN', checked: true},
                {name: 'SRV', checked: true},
                {name: 'EDGE', checked: true},
                {name: 'ELINK', checked: true},
                {name: 'ENV', checked: true},
                {name: 'POWER', checked: true}
            ],
            loadingTraffic: false
        },
        interests: {},

        initialize: function () {
            Backbone.EventBroker.register(this);
        },

        url: function () {

            var url = this.get('baseUrl') + this.get('layer') + '/';
            var viewId = this.get('viewId');

            if (viewId) {
                url += this.get('viewId') + '/';
            }

            return url;
        },

        parse: function (response, options) {

            console.log("Got response". response);

            var nodes = this.get('nodeCollection').populate(response.nodes);
            var links = this.get('linkCollection').populate(response.links);
            var vlans = this.get('vlanCollection').populate(response.vlans);

            // Replace the source/target attribute of each link, which is
            // the node-id with the actual node object
            links.each(function (link) {
                var sourceId = link.get('source');
                var targetId = link.get('target');

                var source = nodes.get(sourceId).attributes;
                if (!source) {
                    source = vlans.get(sourceId).attributes;
                }
                var target = nodes.get(targetId).attributes;
                if (!target) {
                    target = vlans.get(targetId).attributes;
                }

                link.set('source', source);
                link.set('target', target);
            });

            // Since we set the models data explicitly through the collections'
            // populate-methods, we don't return any parsed data here.
            return {};
        },

        /**
         * Load traffic data from the server for nodes matching the
         * filterStrings. If the filterStrings is empty (e.g. a null list), get
         * traffic data for all netboxes found in NAV (this is a HUGE
         * bottleneck). Done asynchronously after page load to reduce perceived
         * slowness of the app.
         */
        loadTraffic: function (filterStrings) {
            var self = this;
            var layer = this.get("layer");

            if (!filterStrings.length) {
                $.getJSON('traffic/layer' + layer + '/')
                    .done(function (data) {
                        self.trafficSuccess.call(self, "all", data);
                    })
                    .fail(this.trafficError)
                    .always(function() {
                        self.set('loadingTraffic', false);
                    });
                return;
            }

            this.set('loadingTraffic', true);
            console.log('Start fetching traffic data');
            _.each(filterStrings, function(location) {
                $.getJSON('traffic/layer' + layer + '/' + location)
                    .done(function (data) {
                        self.trafficSuccess.call(self, location, data);
                    })
                    .fail(this.trafficError)
                    .always(function() {
                        self.set('loadingTraffic', false);
                    });
            });
        },

        trafficSuccess: function (location, data) {
            console.log('Traffic data received for', location, '- processing.');
            var links = this.get('linkCollection');

            // Extend the link-objects with traffic data
            links.each(function (link) {
                var source = parseInt(link.get('source').id);
                var target = parseInt(link.get('target').id);
                var traffic = _.find(data, function (o) {
                    return source === o.source && target === o.target;
                });
                if (traffic === undefined) {
                    // The source/target relationship might be
                    // reversed between links and edges in some cases.
                    traffic = _.find(data, function (o) {
                        return source === o.target && target === o.source;
                    });
                }
                link.set('traffic', traffic);
            });

            Backbone.EventBroker.trigger('netmap:updateGraph');
        },

        trafficError: function (jqXHR, textStatus, errorThrown) {
            console.log('Failed to fetch traffic: ' + textStatus + ' / ' + errorThrown);
        }
    });

    return Graph;
});
