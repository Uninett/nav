define([
    'libs/backbone',
    'status/views',
], function (Backbone, Views) {

    var EventModel = Backbone.Model.extend({
        initialize: function () {
            console.log('An eventmodel was made');
            console.log(this.attributes);
            console.log(this.id);
        }
    });

    return {
        EventModel: EventModel
    };

});
