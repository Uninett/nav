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
        }
    });

    var ViewCollection;

    return {
        NodeCollection: NodeCollection,
        LinkCollection: LinkCollection,
        VlanCollection: VlanCollection,
        ViewCollection: ViewCollection
    };
});
