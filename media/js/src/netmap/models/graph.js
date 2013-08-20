define([
    'netmap/collections/vlan',
    'netmap/collections/nodes',
    'netmap/collections/links',
    'netmap/collections/edges',
    'libs/backbone'
], function (VlanCollection, NodesCollection, LinksCollection, EdgesCollection) {
    var graphModel = Backbone.Model.extend({
        defaults: {
                  topology: 2
        },
        initialize: function () {
        },
        url: function () {
            var base = 'api/graph/layer{0}'.format(this.get('topology'));
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) === '/' ? '' : '/') + this.get('id');
        },
        // todo: Find a cleaner practice for doing this maybe? Hmf.
        parse: function (response, options) {
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


            response.links.each(function (link) {
                link.set({'edges': new EdgesCollection(link.get('edges'))}, {'silent': true});
                link.get('edges').each(function (edge) {
                    edge.attributes.source.netbox = response.nodes.get(edge.get('source').netbox);
                    edge.attributes.source.interface = (!!edge.attributes.source.interface ? edge.attributes.source.interface : 'N/A');
                    edge.attributes.source.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('source').vlans, function (value, key) { return response.vlans.get(value);})));
                    edge.attributes.target.netbox = response.nodes.get(edge.get('target').netbox);
                    edge.attributes.target.interface = (!!edge.attributes.target.interface ? edge.attributes.target.interface : 'N/A');
                    edge.attributes.target.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('target').vlans, function (value, key) { return response.vlans.get(value);})));
                    edge.attributes.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(edge.get('vlans'), function (value, key) { return response.vlans.get(value);})));
                });
                link.attributes.source = response.nodes.get(link.get('source'));
                link.attributes.target = response.nodes.get(link.get('target'));
                link.attributes.vlans = new VlanCollection(VlanCollection.prototype.parse(_.map(link.get('vlans'), function (value, key) { return response.vlans.get(value); })));
            });

            return response;
        }

    });
    return graphModel;

});