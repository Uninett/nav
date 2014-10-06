define([
    'libs/backbone',
    'status/models'
], function (Backbone, Models) {

    /**
     * Collections for Status
     */

    var EventCollection = Backbone.Collection.extend({
        model: Models.EventModel,
        url: 'blapp',
        initialize: function () {
            console.log('A new eventcollection was made');
        }
    });

    return {
        EventCollection: EventCollection
    };

});
