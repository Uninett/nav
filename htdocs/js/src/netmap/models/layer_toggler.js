define([
    'libs/backbone'
], function () {
    var Layermodel = Backbone.Model.extend({
        defaults: {
            layer: 2,
            layer2_active: true
        },
        initialize: function () {
        }

    });
    return Layermodel;

});