define([
    'libs/backbone'
], function () {

    var GraphModel = Backbone.Model.extend({

        idAttribute: 'viewid',

        defaults: {
            last_modified: new Date(),
            title: 'Unsaved view',
            description: '',
            is_public: true,
            is_favorite: false,
            topology: 2,
            categories: [
                {name: 'GSW', is_selected: true},
                {name: 'GW', is_selected: true},
                {name: 'SW', is_selected: true},
                {name: 'OTHER', is_selected: true},
                {name: 'WLAN', is_selected: true},
                {name: 'SRV', is_selected: true},
                {name: 'EDGE', is_selected: true},
                {name: 'ELINK'}
            ],
            zoom: '0,0;0.5',
            display_orphans: false,
            display_topology_errors: false,

            /* Non-persistent attributes */
            refresh_interval: -1
        },

        initialize: function () {}
    });

    return GraphModel;
});
