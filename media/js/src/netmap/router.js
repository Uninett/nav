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
    'libs/spin.min'
    /*'views/users/list'*/
], function (MapCollection, MapModel, GraphModel, DefaultMapModel, MapInfoView, DrawNetmapView, ListNetmapView, NavigationView, SearchboxView) {

    var collection_maps;
    var context_selected_map = {};
    var spinner_map;

    var view_choose_map;

    var AppRouter = Backbone.Router.extend({
        broker: Backbone.EventBroker,
        initialize: function () {
            this.broker.register(this);
        },
        routes: {
            'netmap/:map_id': 'showNetmap',
            '': 'loadPage'
        },
        interests: {
            'map:loading:context_selected_map': 'loadingMap',
            'map:context_selected_map': 'update_selected_map',
            'map:topology_change': 'map_topology_change'
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
            this.loadUi();
        },
        loadingMap: function () {
            $('#netmap_main_view #loading_chart').show();
            var target = document.getElementById('loading_chart');
            spinner_map.spin(target);
        },

        // Routes below here

        showNetmap: function(map_id) {
            this.loadingMap();
            //console.log("showNetmap({0})".format(map_id));
            context_selected_map.id = parseInt(map_id);
            this.loadPage();
        },
        loadPage: function () {
            var self = this;
            this.loadingMap();

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

            var user_id = $("#netmap_userid").html();
            var defaultMap = new DefaultMapModel({ownerid: parseInt(user_id)});
            defaultMap.fetch({
                success: function (model, attributes) {
                    Backbone.View.goTo("netmap/{0}".format(attributes.viewid));
                },
                error: function () {
                    // User's default map not found, try global
                    self.defaultMap = new DefaultMapModel();
                    self.defaultMap.fetch({
                        success: function (model, attributes) {
                            Backbone.View.goTo("netmap/{0}".format(attributes.viewid));
                        },
                        error: function () {
                            // global not found, just do a graph
                            context_selected_map.map = new MapModel({topology: 1});
                            self.loadUi();
                        }
                    });
                }
            });
        },
        loadMap: function (model) {
            var self = this;
            context_selected_map.map = model;
            // render error if model is empty !
            self.loadUi();
        },
        loadUi: function () {
            var self = this;

            /*if (view_choose_map !== undefined) {
                view_choose_map.close(); //
            } else {*/
            view_choose_map = new ListNetmapView({collection: collection_maps, context_selected_map: context_selected_map});
            //}
            self.loadGraph();
            self.loadNavigation();
        },
        loadNavigation: function () {
            // draw navigation view!

            this.view_navigation = new NavigationView({model: context_selected_map.map});
            $('#netmap_left_sidebar #map_filters').html(this.view_navigation.render().el);

            this.view_searchbox = new SearchboxView();
            $('#netmap_left_sidebar #searchbox').html(this.view_searchbox.render().el);
        },
        loadGraph: function () {
            var self = this;

            if (self.view_map !== undefined) {
                self.view_map.close();
            }


            if (context_selected_map.graph !== undefined && context_selected_map.graph) {
               self.drawPage();
            } else {
                if (context_selected_map.id !== undefined) {
                    context_selected_map.graph = new GraphModel({id: context_selected_map.id, topology: context_selected_map.map.attributes.topology});
                } else {
                    context_selected_map.graph = new GraphModel({topology: context_selected_map.map.attributes.topology});
                }
                context_selected_map.graph.fetch({
                    success: function () {
                        self.drawPage();
                    }
                });
            }
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


            self.view_map = new DrawNetmapView({context_selected_map: context_selected_map, view_map_info: self.view_map_info, cssWidth: $('#netmap_main_view').width()});
            $('#netmap_main_view').prepend(self.view_map.render().el);
            spinner_map.stop();
            $('#netmap_main_view #loading_chart').hide();
        }

    });

    var initialize = function () {
        var self = this;
        spinner_map = new Spinner();
        this.app_router = new AppRouter;

        // Extend the View class to include a navigation method goTo
        Backbone.View.goTo = function (loc) {
            self.app_router.navigate(loc, true);
        };


        /*_.extend(context_selected_map, Backbone.Events);
        context_selected_map.on('reattach', function (new_selected_map) {
            context_selected_map = new_selected_map;
            app_router.loadUi();
        });*/
        //var postListView = new postListView();
        //var showPostView = new showPostView();


        Backbone.history.start();
    };
    return {
        initialize: initialize
    };
});