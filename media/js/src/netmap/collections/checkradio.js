define([
    'netmap/models/input_checkradio',
    'libs/backbone'
], function (Model) {
    var GeneralCheckRadioCollection = Backbone.Collection.extend({
        model: Model,
        initialize: function () {
        }
    });

    return GeneralCheckRadioCollection;
});