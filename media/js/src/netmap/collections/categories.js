define([
    'netmap/models/category',
    'libs/backbone'
], function (categoryModel) {
    var CategoryCollection = Backbone.Collection.extend({
        model: categoryModel,
        //url: 'api/categories',
        initialize: function () {

        }

    });

    return CategoryCollection;
});