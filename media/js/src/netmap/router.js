define([
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/graph',
    'netmap/models/default_map',
    'netmap/views/map_info',
    'netmap/views/draw_map',
    'netmap/views/list_maps',
    'netmap/views/navigation',
    'netmap/views/searchbox',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/spin.min',
    'libs/d3.v2'
    /*'views/users/list'*/
], function (MapCollection, MapModel, GraphModel, DefaultMapModel, MapInfoView, DrawNetmapView, ListNetmapView, NavigationView, SearchboxView) {

    var view_choose_map;

    var AppRouter = Backbone.Router.extend({
        initialize: function () {
        },
        routes: {
            'view/:map_id': 'showView',
            '': 'findDefaultView'
        },
        // Routes below here
        showView: function(mapId) {
            //console.log("showNetmap({0})".format(map_id));
            var mapIdAsInteger = parseInt(mapId, 10);
            this.loadUi(mapIdAsInteger);
        },
        findDefaultView: function (view_id) {
            if (!view_id) {
                var user_id = $("#netmap_userid").html();
                this.checkDefaultMapForUser(parseInt(user_id, 10));
            }
        },
        checkDefaultMapForUser: function (userId) {
            var self = this;
            new DefaultMapModel({ownerid: userId}).fetch({
                success: function (model) {
                    Backbone.View.navigate("view/{0}".format(model.get('viewid')), true);
                },
                error: function () {
                    self.checkDefaultMapSetByAdministrator();
                }
            });
        },
        checkDefaultMapSetByAdministrator: function () {
            var self = this;
            // todo add a map the administrator can set to be default view
            // for every page request not containing a map id

            new DefaultMapModel().fetch({
                    success: function (model, attributes) {
                        Backbone.View.navigate("view/{0}".format(model.get('viewid')), true);
                    },
                    error: function () {
                        // global not found, load UI and it will load default graph
                        self.loadUi();
                    }
            });

        },
        loadUi: function (viewId) {
            var self = this;
            view_choose_map = new ListNetmapView();

            // draw navigation view!
            if (this.view_navigation !== undefined) {
                this.view_navigation.close();
            }
            this.view_navigation = new NavigationView();
            $('#netmap_left_sidebar #map_filters').html(this.view_navigation.render().el);

            this.view_searchbox = new SearchboxView();
            $('#netmap_left_sidebar #searchbox').html(this.view_searchbox.render().el);

            if (self.view_map_info !== undefined) {
                self.view_map_info.close();
                $('#netmap_infopanel').append("<div id='mapinfo'></div>");
            }
            self.view_map_info = new MapInfoView({el: $('#mapinfo')});
            // graph is now set in context_selected-map, we can render map!
            $('#netmap_infopanel #list_views').html(view_choose_map.render().el);

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