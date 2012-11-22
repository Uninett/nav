define([
    'libs/backbone'
], function () {
    var CheckRadioModel = Backbone.Model.extend({
        idAttribute: "name",
        defaults: {
            name: null,
            is_selected: false
        },
        initialize: function () {
        }
    });
    return CheckRadioModel;

});