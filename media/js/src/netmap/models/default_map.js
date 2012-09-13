define([
    'libs/backbone'
], function () {
    var defaultMapModel = Backbone.Model.extend({
        defaults: {
                  ownerid: 0
        },
        initialize: function () {
        },
        url: function () {
            var base = 'api/netmap/defaultview';
            if (this.attributes.ownerid !== 0) {
                base += '/user';
            }
            return base;
            //return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + this.id;
        }


    });
    return defaultMapModel;

});