define([
    'libs/backbone'
], function () {
    var Layermodel = Backbone.Model.extend({
        defaults: {
            // see nav.models.profiles TOPOLOGY_TYPES , 1 == layer 2 topology
            layer: 2

        },
        initialize: function () {
        }

    });
    return Layermodel;

});