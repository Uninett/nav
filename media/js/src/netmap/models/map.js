define([
    'netmap/collections/categories',
    'netmap/collections/position',
    'libs/backbone'
], function (CategoryCollection, PositionCollection) {
    var netmapModel = Backbone.Model.extend({
        idAttribute: "viewid",
        defaults: {
            timeStamp: new Date(),
            title: "Unsaved view",
            description: null,
            is_public: true,
            // see nav.models.profiles TOPOLOGY_TYPES , 1 == layer 2 topology
            // todo: change topology value to 2 and ship a SQL migration
            topology: 1,
            categories: new CategoryCollection([
                {name: "GSW", is_selected: true},
                {name: "GW", is_selected: true},
                {name: "SW", is_selected: true},
                {name: "OTHER", is_selected: true},
                {name: "WLAN", is_selected: true},
                {name: "SRV", is_selected: true},
                {name: "EDGE", is_selected: true},
                {name: "ELINK"}
            ]),
            zoom: "0,0;0.5",
            display_orphans: false,
            /* properties that does not get saved */
            position: new PositionCollection([
                {marking: "none", is_selected: true},
                {marking: "room"},
                {marking: "location"}
            ])
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