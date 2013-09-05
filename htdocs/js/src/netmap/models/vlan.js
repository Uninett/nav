define([
    'netmap/collections/categories',
    'netmap/collections/position',
    'libs/backbone'
], function (CategoryCollection, PositionCollection) {
    var netmapModel = Backbone.Model.extend({
        idAttribute: "nav_vlan",
        defaults: {
            vlan: null,
            net_ident: null
        },
        initialize: function () {
        }
    });
    return netmapModel;

});
