define([
    'netmap/models/edge',
    'libs/backbone'
], function (linkModel) {
    var linksCollection = Backbone.Collection.extend({
        model: linkModel,
        initialize: function () {

        },
        parse: function (resp) {
            var edge = [];
            _.each(resp, function (model) {
               edge.push(model);
            });
            return edge;
        },
        toJSON: function () {
            var json = this.map(function (model) {
                var modelJson = model.toJSON();
                return modelJson;
            });
            return json;
        }


    });

    return linksCollection;
});
