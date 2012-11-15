define([
    'libs/backbone'
], function () {
    var OrphanModel = Backbone.Model.extend({
        idAttribute: "is_filtering_orphans",
        defaults: {
            is_filtering_orphans: true
        },
        initialize: function () {
        }
    });
    return OrphanModel;

});