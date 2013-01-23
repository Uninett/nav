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
            '': 'showFavoriteViewOrLoadGeneric'
        },
        // Routes below here
        showRandomView: function () {
            this.showView(null);
        },
        showView: function(mapId) {
            var mapIdAsInteger = parseInt(mapId, 10);
            Resources.setViewId(mapIdAsInteger);
            this.loadUi(mapIdAsInteger);
        },
        showFavoriteViewOrLoadGeneric: function() {
            var favorite = Resources.getMapPropertiesCollection().getFavorite();
            if (favorite) {
                this.navigate("view/"+favorite.get('viewid'), true);
            } else {
                this.navigate("view/random", true);
            }

        },

        loadUi: function (viewId) {
            var self = this;
            this.viewInfo = Backbone.View.prototype.attachSubView(this.viewInfo, InfoView, '#netmap_infopanel');
            this.viewNavigation = Backbone.View.prototype.attachSubView(this.viewNavigation, NavigationView, '#netmap_left_sidebar');

            self.view_map = new DrawNetmapView({
                viewid: viewId,
                view_map_info: self.view_map_info,
                cssWidth: $('#netmap_main_view').width()
            });
            $('#netmap_main_view #wrapper_chart').html(self.view_map.render().el);
        }

    });

    var initialize = function () {
        var self = this;
        //spinner_map = new Spinner();
        this.app_router = new AppRouter;

        // Extend the View class to include a navigation method goTo
        Backbone.View.navigate = self.app_router.navigate;
        Backbone.history.start();
    };


    return {
        initialize: initialize
    };
});