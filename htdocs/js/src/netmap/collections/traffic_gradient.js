define([
    'netmap/models/traffic_gradient',
    'libs/backbone'
], function (trafficGradientModel) {
    var netmapCollection = Backbone.Collection.extend({
        model: trafficGradientModel,
        url: 'api/traffic_load_gradient',
        initialize: function () {

        }

    });

    return netmapCollection;
});