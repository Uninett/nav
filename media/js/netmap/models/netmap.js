define([
    'Underscore',
    'Backbone'
], function (_, Backbone) {
    var netmapModel = Backbone.Model.extend({
        idAttribute: "viewid",
        defaults: {
            timeStamp: new Date()
        },
        initialize: function () {

        },
        url: function () {
            var base = 'api/netmap';
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + this.id;
        }


    });
    return netmapModel;

});