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
    'libs/backbone-eventbroker',
    'libs/spin.min',
    'libs/d3.v2'
    /*'views/users/list'*/
], function (MapCollection, MapModel, GraphModel, DefaultMapModel, MapInfoView, DrawNetmapView, ListNetmapView, NavigationView, SearchboxView) {

    var collection_maps;
    var context_selected_map = {};
    var context_user_default_view;
    var spinner_map;
    var map_id;

    var view_choose_map;

    var AppRouter = Backbone.Router.extend({
        broker: Backbone.EventBroker,
        initialize: function () {
            this.broker.register(this);
        },
        routes: {
            'view/:map_id': 'showNetmap',
            '': 'loadPage'
        },
        interests: {
            'map:loading:context_selected_map': 'loadingMap',
            'map:context_selected_map': 'update_selected_map'
        },
        update_selected_map: function (new_context) {
            this.loadingMap();
            if (new_context.map.id !== undefined && new_context.map.id) {
                this.showNetmap(new_context.map.id);
            } else if (new_context.map !== undefined && new_context.map) {
                this.loadUi();
            }
        },
        map_topology_change: function (topology_id) {
            this.loadingMap();
            this.loadUi(true); // force load!
        },
        loadingMap: function () {
            console.log("aha?");
            /*$('#netmap_main_view #chart').hide();
            $('#netmap_main_view #loading_chart').show();
            var target = document.getElementById('loading_chart');
            spinner_map.spin(target);*/
        },

        // Routes below here

        showNetmap: function(map_id) {
            this.loadingMap();
            //console.log("showNetmap({0})".format(map_id));
            map_id = parseInt(map_id, 10);
            context_selected_map.id = parseInt(map_id, 10);
            this.loadPage();
        },
        loadPage: function () {
            var self = this;
            this.loadingMap();

            // check user's default view if he has any.


            if (context_user_default_view === undefined) {
                var user_id = $("#netmap_userid").html();
                new DefaultMapModel({ownerid: parseInt(user_id, 10)}).fetch({
                    success: function (model) {
                        context_user_default_view = model;
                    },
                    error: function () {
                        context_user_default_view = null;
                    }
                });
            }

            // is "colelction_maps" set?

            if (collection_maps === undefined) {
                collection_maps = new MapCollection();
                collection_maps.fetch({
                    success: function () {
                        self.checkContextMapId();
                    }
                });
            } else {
                self.checkContextMapId();
            }


        },
        checkContextMapId: function () {
            var self = this;

            if (context_selected_map.id !== undefined) {
                self.loadMap(collection_maps.get(context_selected_map.id));
            } else {
                self.checkDefaultMapSetByAdministrator();
            }

        },
        checkDefaultMapSetByAdministrator: function () {
            var self = this;
            // todo add a map the administrator can set to be default view
            // for every page request not containing a map id

            if (context_user_default_view) {
                Backbone.View.navigate("view/{0}".format(context_user_default_view.get('viewid')), true);
            } else {
                new DefaultMapModel().fetch({
                    success: function (model, attributes) {
                        Backbone.View.navigate("view/{0}".format(model.get('viewid')), true);
                    },
                    error: function () {
                        // global not found, just do a graph
                        context_selected_map.map = new MapModel({topology: 1});
                        self.loadUi();
                    }
                });
            }
        },
        loadMap: function (model) {
            var self = this;
            context_selected_map.map = model;
            // render error if model is empty !
            self.loadUi();
        },
        loadUi: function (forceLoad) {
            var self = this;
            view_choose_map = new ListNetmapView();
            //}
            self.loadGraph(forceLoad);
            self.loadNavigation();
        },
        loadNavigation: function () {
            // draw navigation view!
            var oldViewNavigationOptions = {model: context_selected_map.map};
            if (this.view_navigation !== undefined) {
                oldViewNavigationOptions.isLoading = this.view_navigation.isLoading;
                this.view_navigation.close();
            }
            this.view_navigation = new NavigationView(oldViewNavigationOptions);
            $('#netmap_left_sidebar #map_filters').html(this.view_navigation.render().el);

            this.view_searchbox = new SearchboxView();
            $('#netmap_left_sidebar #searchbox').html(this.view_searchbox.render().el);
        },
        loadGraph: function (forceLoad) {
            var self = this;

            if (self.view_map !== undefined) {
                self.view_map.close();
            }

            self.drawPage();
        },
        drawPage: function () {
            var self = this;

            if (self.view_map_info !== undefined) {
                self.view_map_info.close();
                $('#netmap_infopanel').append("<div id='mapinfo'></div>");
            }
            self.view_map_info = new MapInfoView({el: $('#mapinfo')});
            // graph is now set in context_selected-map, we can render map!
            $('#netmap_infopanel #list_views').html(view_choose_map.render().el);

            self.view_map = new DrawNetmapView({viewid: map_id, mapProperties: context_selected_map.map, view_map_info: self.view_map_info, cssWidth: $('#netmap_main_view').width(), loadDefault: parseInt($("#netmap_userid").html(),10)});
            $('#netmap_main_view #wrapper_chart').html(self.view_map.render().el);
            //spinner_map.stop();
            //$('#netmap_main_view #loading_chart').hide();
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