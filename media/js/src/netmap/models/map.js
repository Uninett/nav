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
            isFavorite: false,
            topology: 2,
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
            displayOrphans: false,
            displayTopologyErrors: false,
            /* properties that does not get saved */
            dataRefreshInterval: -1,
            position: new PositionCollection([
                {name: "none", is_selected: true},
                {name: "room"},
                {name: "location"}
            ])
        },
        initialize: function () {
        },
        url: function () {
            var base = 'api/netmap';
            if (this.isNew()) return base;
            return base + (base.charAt(base.length - 1) === '/' ? '' : '/') + this.id;
        },
        parse: function(resp, xhr) {
            if (resp.categories) {
                resp.categories = new CategoryCollection(resp.categories);
            }
            if (!!resp.display_orphans) {
                resp.displayOrphans = resp.display_orphans;
            }
            if (!!resp.is_public) {
                resp.isPublic = resp.is_public;
            }
            return resp;
        }

    });
    return netmapModel;

});