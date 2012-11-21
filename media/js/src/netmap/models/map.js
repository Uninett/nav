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
            topology: 1,
            categories: new CategoryCollection([
                {name: "GSW"},
                {name: "GW"},
                {name: "SW"},
                {name: "OTHER"},
                {name: "WLAN"},
                {name: "SRV"},
                {name: "EDGE"},
                {name: "ELINK", 'is_selected': false}
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