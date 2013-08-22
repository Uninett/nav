define([
    'netmap/models/node',
    'libs/backbone'
], function (nodeModel) {
    var nodesCollection = Backbone.Collection.extend({
        model: nodeModel,
        initialize: function () {

        },
        parse: function (resp) {
            var nodes = [];
            _.each(resp, function (model) {
               nodes.push(nodeModel.prototype.parse(model));
            });
            return nodes;
        }


    });

    return nodesCollection;
});
