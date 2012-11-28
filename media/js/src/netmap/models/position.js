define([
    'netmap/models/input_checkradio',
    'libs/backbone'
], function (Model) {
    var PositionModel = Model.extend({
        validate: function(attributes) {
            if (attributes.name &&
                attributes.name !== "room" &&
                attributes.name !== "location" &&
                attributes.name !== "none") {
                return "position has to be none, room or location!";
            }
        }

    });
    return PositionModel;

});