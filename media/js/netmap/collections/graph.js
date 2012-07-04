define([
    'jQuery',
    'Underscore',
    'Backbone',
    'models/graph'
], function ($, _, Backbone, netmapModel) {
    var graphCollection = Backbone.Collection.extend({
        model: netmapModel,
        url: 'api/graph',
        initialize: function () {
            // set url depending on netmap
        }

    });

    return graphCollection;
});