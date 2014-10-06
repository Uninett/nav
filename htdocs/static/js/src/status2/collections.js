define([
    'libs/backbone',
    'status/models'
], function (Backbone, Models) {

    /**
     * Collections for Status
     */
    var EventCollection = Backbone.Collection.extend({
        model: Models.EventModel,
        comparator: function (obj) {
            return [obj.get('event_type'), obj.get('subject')];
        },
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
