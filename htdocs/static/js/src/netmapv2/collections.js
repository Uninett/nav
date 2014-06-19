define([
    'netmap/models',
    'libs/backbone'
], function (Models) {

    var NodeCollection = Backbone.Collection.extend({

        model: Models.Node,

        populate: function (nodes) {

            var models = [];
            _.each(nodes, function (node) {

                models.push(new Models.Node (node));
            });

            this.add(models);
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

            var models = [];
            _.each(links, function (link) {

                models.push(new Models.Link (link));
            });

            this.add(models);
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

        populate: function (vlans) {

            var models = [];
            _.each(vlans, function (vlan) {

                models.push(new Models.Vlan (vlan));
            });

            this.add(models);
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
