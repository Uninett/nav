define([
    'netmap/models/l3edge',
    'libs/backbone'
], function (l3EdgeModel) {
    var l3EdgeCollection = Backbone.Collection.extend({
        model: l3EdgeModel,
        initialize: function (options) {
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
                modelJson.edges = modelJson.edges.toJSON();
                modelJson.id = modelJson.id.toJSON();
                return modelJson;
            });
            return json;
        }

    });

    return l3EdgeCollection;
});
