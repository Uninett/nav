define([
    'netmap/models',
    'libs/backbone'
], function (Models) {

    /**
     * Collections for Netmap
     */

    var NodeCollection = Backbone.Collection.extend({

        model: Models.Node,

        populate: function (nodes) {

            var models = _.map(nodes, function (node) {
                return new Models.Node (node);
            });

            this.reset(models);
            return this;
        },

        getGraphObjects: function () {
            return this.map(function (node) {
                return node.attributes;
            });
        }
    });

    var LinkCollection = Backbone.Collection.extend({

        model: Models.Link,

        populate: function (links) {

            var models = _.map(links, function (link) {
                return new Models.Link (link);
            });

            this.reset(models);
            return this;
        },

        getGraphObjects: function () {
            return this.map(function (link) {
                return link.attributes;
            });
        }
    });

    var VlanCollection = Backbone.Collection.extend({

        model: Models.Vlan,
        comparator: function (a, b) { return a.vlan - b.vlan; },

        populate: function (vlans) {

            var models = _.map(vlans, function (vlan) {
                return new Models.Vlan (vlan);
            });

            this.reset(models);
            return this;
        },

        getGraphObjects: function () {
            return this.map(function (vlan) {
                return vlan.attributes;
            });
        }
    });

    var NetmapViewCollection = Backbone.Collection.extend({

        model: Models.NetmapView,
        url: 'views/',

        parse: function (data) { console.log('NetmapView collection parse');

            console.log(data);

            return data;
        }
    });

    return {
        NodeCollection: NodeCollection,
        LinkCollection: LinkCollection,
        VlanCollection: VlanCollection,
        NetmapViewCollection: NetmapViewCollection
    };
});
