define([
    'netmap/models/input_checkradio',
    'libs/backbone'
], function (Model) {
    var CategoryCollection = Backbone.Collection.extend({
        model: Model,
        //url: 'api/categories',
        initialize: function () {

        }

    });

    return CategoryCollection;
});