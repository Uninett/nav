define([
    'underscore',
    'backbone'
], function (_, Backbone) {
    var netmapModel = Backbone.Model.extend({
        idAttribute: "viewid",
        defaults: {
            timeStamp: new Date(),
            title: "Unsaved view",
            description: null,
            is_public: true,
            // see nav.models.profiles TOPOLOGY_TYPES , 1 == layer 2 topology
            topology: 1,
            categories: ['GSW', 'GW', 'SW', 'EDGE', 'OTHER', 'WLAN', 'SRV'],
            zoom: "0,0;0",
            display_orphans: false
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