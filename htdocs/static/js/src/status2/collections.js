define([
    'libs/backbone',
    'status/models'
], function (Backbone, Models) {

    /**
     * Collections for Status
     */
    var EventCollection = Backbone.Collection.extend({
        model: Models.EventModel,
        initialize: function () {
            console.log('A new eventcollection was made');
        },
        parse: function (response) {
            return response.results;
        }
    });

    return {
        EventCollection: EventCollection
    };

});
