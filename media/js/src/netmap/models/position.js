define([
    'libs/backbone'
], function () {
    var PositionModel = Backbone.Model.extend({
        idAttribute: "marking",
        defaults: {
            marking: "none",
            is_selected: false
        },
        initialize: function () {
        },
        validate: function(attributes) {
            if (attributes.marking &&
                attributes.marking !== "room" &&
                attributes.marking !== "location" &&
                attributes.marking !== "none") {
                return "position has to be none, room or location!";
            }
        }

    });
    return PositionModel;

});