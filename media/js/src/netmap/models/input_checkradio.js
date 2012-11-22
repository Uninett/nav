define([
    'libs/backbone'
], function () {
    var CheckRadioModel = Backbone.Model.extend({
        idAttribute: "name",
        defaults: {
            name: null,
            is_selected: true
        },
        initialize: function () {
        }
    });
    return CheckRadioModel;

});