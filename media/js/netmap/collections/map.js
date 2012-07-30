define([
    'jquery',
    'underscore',
    'backbone',
    'models/map'
], function ($, _, Backbone, netmapModel) {
    var netmapCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/netmap',
        initialize: function () {

        }

    });

    return netmapCollection;
});