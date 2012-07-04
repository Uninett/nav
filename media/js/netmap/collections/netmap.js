define([
    'jQuery',
    'Underscore',
    'Backbone',
    'models/netmap'
], function ($, _, Backbone, netmapModel) {
    var netmapCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/netmap',
        initialize: function () {

        }

    });

    return netmapCollection;
});