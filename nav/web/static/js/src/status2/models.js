define([
    'libs/backbone',
], function (Backbone) {

    var EventModel = Backbone.Model.extend({
        urlRoot: NAV.urls.status2_clear_alert
    });

    return {
        EventModel: EventModel
    };

});
