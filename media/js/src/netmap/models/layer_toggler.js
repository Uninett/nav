define([
    'libs/backbone'
], function () {
    var Layermodel = Backbone.Model.extend({
        defaults: {
            // see nav.models.profiles TOPOLOGY_TYPES , 1 == layer 2 topology
            layer: 2,
            layer2_active: true
        },
        initialize: function () {
        }

    });
    return Layermodel;

});