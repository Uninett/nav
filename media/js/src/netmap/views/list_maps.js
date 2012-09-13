define([
    'plugins/netmap-extras',
    'netmap/models/map',
    'netmap/models/graph',
    'netmap/models/default_map',
    'netmap/views/modal/save_new_map',
    'libs-amd/text!netmap/templates/list_maps.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function ( NetmapExtras, MapModel, GraphModel, DefaultMapModel, SaveDialogView, netmapTemplate) {

    var ListNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "choose_netview",

        broker: Backbone.EventBroker,
        interests: {
            "map:topology_change": "deactiveAndShowSpinnerWhileLoading",
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest'
        },
        events: {
                "click #save_view": "show_save_view",
                "click #save_new_view": "new_show_save_view",
                "click #delete_view": "delete_view",
                "click #set_as_user_favorite": "set_favorite",
                "change #dropdown_view_id": "changed_view",
                'click #toggle_view' : 'toggleView'
        },

        initialize: function () {
            this.isContentVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(netmapTemplate);

            this.isLoading = false;
            this.collection.bind("reset", this.render, this);
            this.collection.bind("change", this.render, this);
            this.collection.bind("destroy", this.close, this);
            //debugger;
            this.options.context_selected_map.map.bind("change", this.updateCollection, this);

        },
        updateCollection: function () {
            if (this.options.context_selected_map.map.attributes.viewid !== undefined) {
                var map = this.collection.get(this.options.context_selected_map.map.attributes.viewid);
                if (map === undefined) {
                    this.collection.add(this.options.context_selected_map.map);
                }
            }
            this.render();
        },
        showSaveModal:     function (netmapModel) {
            var self = this;
            if (self.modal_save_view !== undefined) {
                self.modal_save_view.close();
            }
            if (this.options.context_selected_map === undefined) {
                debugger;
            }

            self.modal_save_view = new SaveDialogView({model: self.options.context_selected_map.map, 'graph': self.options.context_selected_map.graph});



            self.modal_save_view.render();
        },
        set_favorite: function (e) {
            e.preventDefault();
            var self = this;
            var user_id = $("#netmap_userid").html();
            var updateUserDefaultMap = new DefaultMapModel({ownerid: parseInt(user_id), viewid: self.options.context_selected_map.id});
            updateUserDefaultMap.save(this.attributes, {
                success: function (model) {
                    self.options.context_user_default_view = model;
                    self.render();
                    alert("Set view as favorite!");
                },
                error: function () {
                    alert("Error while setting favorite view");
                }
            });

        },
        new_show_save_view: function () {
            var self = this;
            if (!self.isLoading) {
                var propertiesToKeep = {
                    is_public: self.options.context_selected_map.map.attributes.is_public,
                    topology:  self.options.context_selected_map.map.attributes.topology,
                    categories: self.options.context_selected_map.map.attributes.categories,
                    zoom: self.options.context_selected_map.map.attributes.zoom,
                    display_orphans: self.options.context_selected_map.map.attributes.display_orphans
                };
                self.options.context_selected_map.map.unbind("change");
                self.options.context_selected_map.map = new MapModel();
                self.options.context_selected_map.map.set(propertiesToKeep);
                self.options.context_selected_map.map.bind("change", this.updateCollection, this);

                this.showSaveModal(self.context_selected_map);
            }
        },
        delete_view: function (e) {
            e.preventDefault();
            var self = this;
            if (!self.isLoading) {
                var selected_id = self.options.context_selected_map.map.id;
                self.options.context_selected_map.map.destroy({
                    success: function () {
                        var propertiesToKeep = {
                            is_public: self.options.context_selected_map.map.attributes.is_public,
                            topology:  self.options.context_selected_map.map.attributes.topology,
                            categories: self.options.context_selected_map.map.attributes.categories,
                            zoom: self.options.context_selected_map.map.attributes.zoom,
                            display_orphans: self.options.context_selected_map.map.attributes.display_orphans
                        };
                        self.options.context_selected_map.map.unbind("change");
                        self.options.context_selected_map.map = new MapModel();
                        self.options.context_selected_map.map.set(propertiesToKeep);
                        self.options.context_selected_map.map.bind("change", this.updateCollection, this);
                        self.options.context_selected_map.id = undefined;
                        Backbone.history.navigate("");
                        self.broker.trigger("map:context_selected_map", self.options.context_selected_map);
                    },
                    error: function () {
                        alert("Failed to delete view");
                    }
                });
            }

        },
        show_save_view: function (e) {
            e.preventDefault();
            var self = this;
            var selected_id = this.$("#dropdown_view_id :selected").val();
            this.showSaveModal(self.context_selected_map);
        },
        changed_view: function () {
            var self = this;

            // todo: make an option to check for not loading categories from
            //       a saved map but keep what is already chosen.
            //var keep_categories = self.options.context_selected_map.map.attributes.categories;

            self.selected_id = parseInt(this.$("#dropdown_view_id :selected").val().trim());
            if (isNaN(self.selected_id)) {
                // assume new
                var propertiesToKeep = {
                    is_public: self.options.context_selected_map.map.attributes.is_public,
                    topology:  self.options.context_selected_map.map.attributes.topology,
                    categories: self.options.context_selected_map.map.attributes.categories,
                    zoom: self.options.context_selected_map.map.attributes.zoom,
                    display_orphans: self.options.context_selected_map.map.attributes.display_orphans
                };
                self.options.context_selected_map.map.unbind("change");
                self.options.context_selected_map.map = new MapModel();
                self.options.context_selected_map.map.set(propertiesToKeep);
                self.options.context_selected_map.map.bind("change", this.render, this);
            } else {
                self.options.context_selected_map.map = self.collection.get(self.selected_id);
            }
            //self.options.context_selected_map.map.attributes.categories = keep_categories;

            if (!self.options.context_selected_map.map.isNew() && self.is_selected_view_really_changed(self.selected_id, self.options.context_selected_map.map)) {
                Backbone.history.navigate("netmap/{0}".format(self.selected_id));
                self.loadMapFromContextId(self.selected_id);
            }
        },
        deactiveAndShowSpinnerWhileLoading: function () {
            var self = this;
            self.isLoading = true;
            this.$el.find("#set_as_user_favorite").attr('disabled', 'disabled');
            this.$el.find("#save_view").attr('disabled', 'disabled');
            this.$el.find("#dropdown_view_id").attr('disabled', 'disabled');
            self.broker.trigger('map:loading:context_selected_map');
        },
        loadMapFromContextId: function (map_id) {
            var self = this;
            self.deactiveAndShowSpinnerWhileLoading();

            self.options.context_selected_map.map.unbind("change");
            self.options.context_selected_map.map = self.collection.get(map_id);
            //self.options.context_selected_map.map.bind("change", this.render, this);
            self.options.context_selected_map.graph = new GraphModel({id: map_id});
            self.options.context_selected_map.graph.fetch({
                success: function (model) {
                    self.options.context_selected_map.graph = model;
                    //self.render();
                    self.isLoading = false;
                    self.broker.trigger('map:context_selected_map', self.options.context_selected_map);
                    //self.options.context_selected_map.trigger('reattach', self.options.context_selected_map);
                }
            });
            /*self.options.context_selected_map.map.fetch({
                success: function (model) {
                    debugger;
                    self.options.context_selected_map.map = model;
                    self.options.context_selected_map.map.bind("change", this.render, this);
                    //self.render();
                }
            })*/
        },
        headerFooterMinimizeRequest: function (options) {
            if (options && options.name === 'header' && (options.isShowing !== this.isContentVisible)) {
                this.toggleView();
            }
        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();

            this.broker.trigger('map:resize:animate', {marginRight: margin});
        },
        alignView: function () {
            var $helper = $(this.$el.parent().parent());
            //var $helper_content = $(".inner_wrap", this.$el);
            var $helper_content = $(".inner_wrap.right_sidebar"); // hack until 'ScrollViewRightPane' is created!

            var margin;

            if (!this.isContentVisible) {
                margin = 30;
                $("a#toggle_view", this.$el).html("&lt;&lt;");

                $helper_content.fadeOut('fast');
                $helper.animate({'width': "{0}px".format(12) }, 400);
            } else {
                margin = 210;

                $("a#toggle_view", this.$el).html("&gt;&gt;");

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin - 40) }, 400);
            }
            return margin;
            //$("#netmap_main_view").animate({'margin-right': "{0}px".format(margin)}, 400);
        },
        render: function () {
            var self = this;
            var context = {};
            context.maps = this.collection.toJSON();

            context.context_selected_map = this.options.context_selected_map.map.toJSON();
            context.isNew = this.options.context_selected_map.map.isNew();
            if (this.options.context_user_default_view && this.options.context_user_default_view.attributes.viewid === this.options.context_selected_map.map.attributes.viewid) {
                context.isFavorite = this.options.context_user_default_view;
            } else {
                context.isFavorite = false;
            }

            var out = this.template(context);

            this.$el.html(out);

            self.alignView();

            return this;
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        },

        // private methods
        is_selected_view_really_changed: function (selected_id, selected_netmap)  {
            return selected_netmap !== undefined && selected_id !== undefined && selected_id != selected_netmap.attributes.id;
        }
    });
    return ListNetmapView;
});





