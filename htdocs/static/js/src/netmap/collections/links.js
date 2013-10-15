define([
    'netmap/models/link',
    'libs/backbone'
], function (linkModel) {
    var linksCollection = Backbone.Collection.extend({
        model: linkModel,
        initialize: function () {

        },
        parse: function (resp) {
            var links = [];
            _.each(resp, function (model) {
               links.push(model);
            });
            return links;
        }


    });

    return linksCollection;
});
