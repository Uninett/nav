define([
    'libs/backbone'
], function () {
    var CategoryModel = Backbone.Model.extend({
        idAttribute: "name",
        defaults: {
            name: null,
            is_selected: true
        },
        initialize: function () {
        }
    });
    return CategoryModel;

});