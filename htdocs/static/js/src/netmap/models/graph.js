define([
    'netmap/collections/vlan',
    'netmap/collections/nodes',
    'netmap/collections/links',
    'netmap/collections/edges',
    'netmap/collections/l3edges',
    'netmap/models/l3edge',
    'netmap/models/vlan',
    'libs/backbone'
], function (VlanCollection, NodesCollection, LinksCollection, EdgesCollection, L3EdgesCollection, L3Edge, VlanModel) {
    var graphModel = Backbone.Model.extend({
        defaults: {
                  traffic: false,
                  topology: 2 // change default value in models/map.js ;-)
        },
        initialize: function () {
        },
        url: function () {
            var options = '';
            if (this.get('traffic')) {
                options = '?traffic=1';
            }
            var base = 'api/graph/layer{0}'.format(this.get('topology'));
            if (this.isNew()) return base+options;
            return base + (base.charAt(base.length - 1) === '/' ? '' : '/') + this.get('id') + options;
        },
        // todo: Find a cleaner practice for doing this maybe? Hmf.
        parse: function (response, options) {
            var self = this;

            response.vlans = new VlanCollection(VlanCollection.prototype.parse(response.vlans));
            response.nodes = new NodesCollection(NodesCollection.prototype.parse(response.nodes));
            response.nodes.each(function (node) {
                if (node.has('vlans')) {
                    var vlans = node.get('vlans');
                    node.set({
                        'vlans': new VlanCollection(VlanCollection.prototype.parse(_.map(vlans, function (value, key) {
                        return response.vlans.get(value);
                    }))) }, { 'silent': true });
                }
            });

            response.links = new LinksCollection(LinksCollection.prototype.parse(response.links));

            function updateEdgeAttributes(edge) {
                    edge.attributes.source.netbox = response.nodes.get(edge.get('source').netbox);
                    edge.attributes.source.interface = (!!edge.attributes.source.interface ? edge.attributes.source.interface : 'N/A');

                    edge.attributes.target.netbox = response.nodes.get(edge.get('target').netbox);
                    edge.attributes.target.interface = (!!edge.attributes.target.interface ? edge.attributes.target.interface : 'N/A');
            }

            response.links.each(function (link) {
                if (self.get('topology') === 3) {
                    /* { edges: {
                     nav_vlan_id: [{gwportprefix_edge}, {gwportprefix_edge_#}],
                     nav_vlan_id_# : [{gwport_edge_#}, {gwport_edge_#}]
                     }
                     */
                    var l3EdgeObjects = _.map(link.get('edges'), function (edgeList, vlanId) {
                        var l3Edge = new L3Edge();
                        var edgesInL3 = new EdgesCollection(EdgesCollection.prototype.parse(edgeList));
                        edgesInL3.each(function (e) {
                            updateEdgeAttributes(e);
                            e.attributes.vlan = response.vlans.get(vlanId);

                        });
                        l3Edge.set({
                            'id':    response.vlans.get(vlanId),
                            'edges': edgesInL3
                        });

                        return l3Edge;
                    });

                    link.set({'edges': new L3EdgesCollection(l3EdgeObjects)}, {'silent': true});

                    link.set({'vlans': new VlanCollection(_.pluck(l3EdgeObjects, 'id'))}, {'silent': true});
                } else {
                    link.set({'edges': new EdgesCollection(link.get('edges'))}, {'silent': true});
                    link.get('edges').each(function (edge) {
                        updateEdgeAttributes(edge);
                        edge.attributes.source.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('source').vlans, function (value, key) {
                            return response.vlans.get(value);
                        })));
                        edge.attributes.target.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('target').vlans, function (value, key) {
                            return response.vlans.get(value);
                        })));
                        edge.attributes.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('vlans'), function (value, key) {
                            return response.vlans.get(value);
                        })));
                    });

                    link.attributes.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(link.get('vlans'), function (value, key) {
                        return response.vlans.get(value);
                    })));
                }
                link.attributes.source = response.nodes.get(link.get('source'));
                link.attributes.target = response.nodes.get(link.get('target'));

            });

            return response;
        }

    });
    return graphModel;

});