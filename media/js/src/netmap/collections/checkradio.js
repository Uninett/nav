define([
    'netmap/models/input_checkradio',
    'libs/backbone'
], function (Model) {
    var GeneralCheckRadioCollection = Backbone.Collection.extend({
        model: Model,
        initialize: function () {
        },
        clearIsSelectedStatus: function () {
            this.each(function (element) {
                element.set({is_selected: false}, {silent: true});
            });
        }
    });

    return GeneralCheckRadioCollection;
});