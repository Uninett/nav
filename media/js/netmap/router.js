
define([
    'jQuery',
    'Underscore',
    'Backbone',
    'collections/netmap',
    'models/netmap',
    'models/graph',
    'views/draw_netmap',
    'views/list_netmap',
    'views/modal/save_new_view'
    /*'views/users/list'*/
], function ($, _, Backbone, NetmapCollection, NetmapModel, GraphModel, DrawNetmapView, ListNetmapView, SaveNetmapView) {

    var netmaps;
    var selected_netmap;


    var AppRouter = Backbone.Router.extend({
        routes: {
            '': 'showDefaultNetmap',
            // Define some URL routes
            'netmaps': 'listNetmaps',
            //'netmap/new': 'show_save_netmap_view',
            'netmap/:netmap_id': 'showNetmap',
            'dummy': 'dummy'
            /*'/users': 'showUsers',

             // Default
             '*actions': 'defaultAction'*/
        },
        listNetmaps: function () {
            var self = this;

            if (netmaps === undefined) {
                netmaps = new NetmapCollection();

                netmaps.fetch({
                    success: function () {

                        self.postListView = new ListNetmapView({collection: netmaps, options: {'selected_netmap': self.selected_netmap} });
                        $('#netmap_infopanel').html(self.postListView.render().el);
                    }
                });
            }
            if (self.postListView) {
                $('#netmap_infopanel').html(self.postListView.render().el);
            }

            //drawNetmap(this.selected_netmap);

        },
        showDefaultNetmap: function () {
            // todo: add logic for fetching default netmap
            this.showNetmap();
        },
        showNetmap: function(netmap_id) {
            var self = this;

            if (netmaps) {
                self.selected_netmap = netmaps.get(netmap_id);
                if (self.list_netmap_view) {
                    self.list_netmap_view.close();
                }
                self.drawNetmap(self.selected_netmap);
            } else {

                this.selected_netmap = new NetmapModel({id: netmap_id});

                self.selected_netmap.fetch({
                    success: function () {
                        self.drawNetmap(self.selected_netmap);
                    }
                });
            }

            this.listNetmaps();

        },
        drawNetmap: function () {
            "use strict";
            var self = this;

            var graph;
            if (selected_netmap !== undefined) {
                graph = new GraphModel({id: selected_netmap.id});
            } else {
                graph = new GraphModel();
            }
            graph.fetch({
                success: function() {
                    self.list_netmap_view = new DrawNetmapView({model: graph });
                    $('#netmap_main_view').html(self.list_netmap_view.render().el);
                }
            });
        },
        dummy: function () {
            //netmaps.getByCid("c2").set({title: 'foobar'});
            netmaps.get(1).set({title: 'fooobar'});
        },
        show_save_netmap_view: function () {
            "use strict";
            var self = this;
            self.save_netmap_view = new SaveNetmapView({model: selected_netmap});
        }

    });

    var initialize = function () {
        var app_router = new AppRouter;

        //var postListView = new postListView();
        //var showPostView = new showPostView();


        Backbone.history.start();
    };
    return {
        initialize: initialize
    };
});