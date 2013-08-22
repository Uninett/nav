define([
    'libs/backbone',
    'libs/underscore'
], function () {
    var CheckRadioModel = Backbone.Model.extend({
        idAttribute: "name",
        defaults: {
            name: null,
            is_selected: false
        },
        initialize: function (attributes) {
            // Sets the idAttribute to "value" if there a value present
            // in the model. Normally defaults to "name"
            if ("value" in attributes) {
                this.idAttribute = "value";
                this.id = this.get("value");
            }
        }
    });

    return CheckRadioModel;

});