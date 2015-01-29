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
            filter_categories: [
                {name: 'GSW', checked: true},
                {name: 'GW', checked: true},
                {name: 'SW', checked: true},
                {name: 'OTHER', checked: true},
                {name: 'WLAN', checked: true},
                {name: 'SRV', checked: true},
                {name: 'EDGE', checked: true},
                {name: 'ELINK', checked: true},
                {name: 'ENV', checked: true},
                {name: 'POWER', checked: true}
            ]
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
         * Load traffic data from the server. This is a HUGE bottleneck
         * and is therefore done asynchronously after page load.
         */
        loadTraffic: function () {
            var self = this;
            $.getJSON('traffic/layer' + this.get('layer') + '/')
                .done(function (data) {
                    self.trafficSuccess.call(self, data);
                })
                .fail(this.trafficError);
        },

        trafficSuccess: function (data) {

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

        trafficError: function () { console.log('Failed to fetch traffic');

            // TODO: Meaningful report
        }
    });

    return Graph;
});

