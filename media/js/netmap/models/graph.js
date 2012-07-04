define([
    'Underscore',
    'Backbone'
], function (_, Backbone) {
    var graphModel = Backbone.Model.extend({
        defaults: {
        },
        initialize: function () {

        },
        url: function () {
            var base = 'api/graph';
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + this.id;
        }


    });
    return graphModel;

});