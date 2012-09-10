define([
    'netmap/models/map',
    'libs/backbone'
], function (netmapModel) {
    var netmapCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/netmap',
        initialize: function () {

        }

    });

    return netmapCollection;
});