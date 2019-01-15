define([
    'libs/backbone',
    'status/models'
], function (Backbone, Models) {

    /**
     * Collections for Status
     */
    var EventCollection = Backbone.Collection.extend({
        model: Models.EventModel,

        sortAttribute: 'start_time',
        sortDirection: -1,

        initialize: function () {
            console.log('A new eventcollection was made');
        },

        sortEvents: function (attribute, direction) {
            this.sortAttribute = attribute;
            this.sortDirection = direction;
            this.sort();
        },

        comparator: function (a, b) {
            var value1, value2, sortAttributes = this.sortAttribute.split('.');
            if (sortAttributes.length > 1) {
                /** Support one level nesting */
                value1 = a.get(sortAttributes[0])[sortAttributes[1]].toLowerCase();
                value2 = b.get(sortAttributes[0])[sortAttributes[1]].toLowerCase();
            } else {
                /** No nesting */
                value1 = a.get(this.sortAttribute).toLowerCase();
                value2 = b.get(this.sortAttribute).toLowerCase();
            }

            if (value1 === value2) { return 0; }
            if (this.sortDirection === 1) {
                return value1 > value2 ? 1 : -1;
            } else {
                return value1 < value2 ? 1 : -1;
            }

        },
        parse: function (response) {
            return response.results;
        }
    });

    var ChangeCollection = Backbone.Collection.extend({
        model: Models.EventModel
    });

    return {
        EventCollection: EventCollection,
        ChangeCollection: ChangeCollection
    };

});
