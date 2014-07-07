define([
    'netmap/collections',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collections) {

    var Graph = Backbone.Model.extend({

        defaults: {
            traffic: false,
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

            if (viewId !== null) {
                url += this.get('viewId') + '/';
            }

            if (this.get('traffic')) {
                url += '?traffic=1';
            }

            return url;
        },

        parse: function (response, options) { console.log('graph model parse');

            var nodes = this.get('nodeCollection').populate(response.nodes);
            var links = this.get('linkCollection').populate(response.links);
            var vlans = this.get('vlanCollection').populate(response.vlans);

            // Set the actual node object of each link
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

            // Get traffic
            var self = this;
            $.getJSON('traffic/layer' + this.get('layer') + '/')
                .done(function (data) {
                    self.trafficSuccess.call(self, data);
                })
                .fail(this.trafficError);

            return {}; // We set the attributes excplicitly
        },

        trafficSuccess: function (data) { console.log('traffic success!');

            var links = this.get('linkCollection');
            links.each(function (link) {
                var source = parseInt(link.get('source').id);
                var target = parseInt(link.get('target').id);
                var traffic = _.find(data, function (o) {
                    return source === o.source && target === o.target;
                });
                link.set('traffic', traffic);
            });

            Backbone.EventBroker.trigger('netmap:updateGraph');
        },

        trafficError: function () { console.log('traffic fail!');

        }
    });

    return Graph;
});

