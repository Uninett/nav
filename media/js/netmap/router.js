
define([
    'jquery',
    'underscore',
    'backbone',
    'collections/map',
    'models/map',
    'models/graph',
    'views/netbox_info',
    'views/draw_map',
    'views/list_maps',
    'views/navigation'
    /*'views/users/list'*/
], function ($, _, Backbone, MapCollection, MapModel, GraphModel, NetboxInfoView, DrawNetmapView, ListNetmapView, NavigationView) {

    var collection_maps;
    var context_selected_map = {};

    var view_choose_map;



    var AppRouter = Backbone.Router.extend({

        routes: {
            'netmap/:map_id': 'showNetmap',
            '': 'loadPage'
        },

        showNetmap: function(map_id) {

            context_selected_map.id = parseInt(map_id);
            this.loadPage();
        },
        loadPage: function () {
            var self = this;
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

            context_selected_map.map = new MapModel();
            self.loadUi();
        },
        loadMap: function (model) {
            var self = this;
            context_selected_map.map = model;
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

            view_navigation = new NavigationView({model: context_selected_map.map});
            $('#netmap_left_sidebar').html(view_navigation.render().el);
        },
        loadGraph: function () {
            var self = this;
            console.log("====" + "map_id");
            console.log(context_selected_map.id);
            console.log("====/" + "map_id");
            if (context_selected_map.id !== undefined) {
                context_selected_map.graph = new GraphModel({id: context_selected_map.id });
            } else {
                context_selected_map.graph = new GraphModel();
            }
            context_selected_map.graph.fetch({
                success: function () {
                    self.drawPage();
                }
            });
        },
        drawPage: function () {
            var self = this;


            self.view_netbox_info = new NetboxInfoView({el: $('#nodeinfo')});

            // graph is now set in context_selected-map, we can render map!
            $('#netmap_infopanel #list_views').html(view_choose_map.render().el);

            if (self.view_map !== undefined) {
                self.view_map.close();
            }

            self.view_map = new DrawNetmapView({context_selected_map: context_selected_map, view_netbox_info: self.view_netbox_info, cssWidth: $('#netmap_main_view').width()});
            $('#netmap_main_view').html(self.view_map.render().el);

        }

    });

    var initialize = function () {
        var app_router = new AppRouter;

        _.extend(context_selected_map, Backbone.Events);
        context_selected_map.on('reattach', function (new_selected_map) {
            context_selected_map = new_selected_map;
            app_router.loadUi();
        });
        //var postListView = new postListView();
        //var showPostView = new showPostView();


        Backbone.history.start();
    };
    return {
        initialize: initialize
    };
});