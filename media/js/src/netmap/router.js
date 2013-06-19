define([
    'netmap/resource',
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/graph',
    'netmap/models/default_map',
    'netmap/views/draw_map',
    'netmap/views/navigation',
    'netmap/views/info',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/spin.min',
    'libs/d3.v2'
    /*'views/users/list'*/
], function (Resources, MapCollection, MapModel, GraphModel, DefaultMapModel, DrawNetmapView, NavigationView, InfoView) {

    var AppRouter = Backbone.Router.extend({
        initialize: function () {
            this.viewNavigation = null;
            this.viewInfo = null;
        },
        routes: {
            'view/random': 'showRandomView',
            'view/:map_id': 'showView',
            'view/:map_id/vlan/:vlan_id': 'showViewWithVlanSelected',
            'vlan/:vlan_id': 'showRandomViewWithVlanSelected',
            '': 'showFavoriteViewOrLoadGeneric'
        },
        _setMapId: function (mapId) {
            var mapIdAsInteger = parseInt(mapId, 10);
            Resources.setViewId(mapIdAsInteger);
            return mapIdAsInteger;
        },
        // Routes below here
        showRandomView: function () {
            this.showView(null);
        },
        showRandomViewWithVlanSelected: function (vlanId) {
            this.showViewWithVlanSelected(null, vlanId);
        },
        showView: function(mapId) {
            this.loadUi(this._setMapId(mapId), null);
        },
        showViewWithVlanSelected: function(mapId, vlanId) {
            var vlanIdAsInteger= parseInt(vlanId, 10);
            this.loadUi(this._setMapId(mapId), vlanIdAsInteger);
        },
        showFavoriteViewOrLoadGeneric: function() {
            var favorite = Resources.getMapCollection().getFavorite();
            if (favorite) {
                this.navigate("view/"+favorite.get('viewid'), true);
            } else {
                this.navigate("view/random", true);
            }

        },

        loadUi: function (viewId, vlanId) {
            var self = this;
            this.viewInfo = Backbone.View.prototype.attachSubView(this.viewInfo, InfoView, '#netmap_infopanel');
            this.viewNavigation = Backbone.View.prototype.attachSubView(this.viewNavigation, NavigationView, '#netmap_left_sidebar');

            self.view_map = new DrawNetmapView({
                viewid: viewId,
                nav_vlanid: {'navVlanId': vlanId },
                view_map_info: self.view_map_info,
                cssWidth: $('#netmap_main_view').width()
            });
            $('#wrapper_chart').html(self.view_map.render().el);
        }

    });

    var initialize = function () {
        var self = this;
        //spinner_map = new Spinner();
        this.app_router = new AppRouter();

        // Extend the View class to include a navigation method goTo
        Backbone.View.navigate = self.app_router.navigate;
        Backbone.history.stripTrailingSlash = function (stringValue) {
            return stringValue.replace(/\/$/, "");
        };
        Backbone.history.start();
    };


    return {
        initialize: initialize
    };
});