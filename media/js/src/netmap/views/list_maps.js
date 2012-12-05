define([
    'netmap/resource',
    'plugins/netmap-extras',
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/graph',
    'netmap/models/default_map',
    'netmap/views/modal/save_new_map',
    'libs-amd/text!netmap/templates/list_maps.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/spin.min',
    'plugins/jquery_spinjs'
], function (ResourceManager, NetmapExtras, CollectionMapProperties, ModelMapProperties, GraphModel, DefaultMapModel, SaveDialogView, netmapTemplate) {

    var ListNetmapView = Backbone.View.extend({
        tagName: "div",
        id: "choose_netview",

        broker: Backbone.EventBroker,
        interests: {
            "netmap:mapProperties": "setMapProperties",
            "netmap:graph": "setGraph",
            "map:topology_change": "deactiveAndShowSpinnerWhileLoading",
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest'
        },
        events: {
            "click #save_view": "showSaveView",
            "click #save_new_view": "showSaveAsView",
            "click #delete_view": "deleteView",
            "click #set_as_user_favorite": "setFavorite",
            "change #dropdown_view_id": "changed_view",
            'click #toggle_view': 'toggleView'
        },

        initialize: function () {
            var self = this;
            this.isContentVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(netmapTemplate);

            this.isLoading = !!this.collection;
            if (this.collection) {
                this.collection.bind("reset", this.render, this);
                this.collection.bind("change", this.render, this);
                this.collection.bind("destroy", this.close, this);
            } else {
                this.collection = new CollectionMapProperties();
                this.collection.fetch({
                    success: function (collection, attributes) {
                        self.collection = collection;
                        // if no netmap views loaded from API OR no active map property (read: netmap view is active)
                        if (self.collection.length <= 1 || !self.options.activeMapProperty) {
                            self.collection.unshift({}); // insert empty Map model
                            self.options.activeMapProperty = self.collection.at(0);
                        }
                        self.render();
                    },
                    error: function () {
                        alert("error loading collection over available views");
                    }
                });
            }

            this.broker.trigger("netmap:request:graph");

            //ResourceManager.getInterest("mapProperties");


            //this.options.mapProperties.map.bind("change", this.updateCollection, this);

        },
        setMapProperties: function (mapProperties) {
            this.collection = mapProperties;
            this.render();
        },
        setGraph: function (graph) {
            this.graph = graph;
            this.render();
        },
        updateCollection: function () {
            if (this.options.mapProperties.map.attributes.viewid !== undefined) {
                var map = this.collection.get(this.options.mapProperties.map.attributes.viewid);
                if (map === undefined) {
                    this.collection.add(this.options.mapProperties.map);
                }
            }
            this.render();
        },
        showCreateNewViewDialog: function () {
            this.showSaveModal(true);
        },
        showUpdateViewDialog: function () {
            this.showSaveModal(false);
        },
        showSaveModal: function (isNewView) {
            var self = this;
            if (self.viewModalSave !== undefined) {
                self.viewModalSave.close();
            }

            self.viewModalSave = new SaveDialogView({
                model: self.options.activeMapProperty,
                graph: self.graph
            });

            self.viewModalSave.render();
        },
        setFavorite: function (e) {
            e.preventDefault();
            var self = this;
            var user_id = $("#netmap_userid").html();
            var updateUserDefaultMap = new DefaultMapModel({ownerid: parseInt(user_id), viewid: self.options.mapProperties.id});
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
        getPropertiesToKeep: function () {
            var self = this;
            return {
                is_public: self.options.mapProperties.map.attributes.is_public,
                topology: self.options.mapProperties.map.attributes.topology,
                categories: self.options.mapProperties.map.attributes.categories,
                zoom: self.options.mapProperties.map.attributes.zoom,
                display_orphans: self.options.mapProperties.map.attributes.display_orphans
            };
        },
        showSaveView: function (e) {
            e.preventDefault();
            //var self = this;
            //var selected_id = $("#dropdown_view_id :selected", this.$el).val();
            this.showUpdateViewDialog();
        },
        showSaveAsView: function () {
            var self = this;
            if (!self.isLoading) {
                var properties = self.getPropertiesToKeep();
                self.options.mapProperties.map.unbind("change");
                self.options.mapProperties.map = new MapModel();
                self.options.mapProperties.map.set(properties);
                self.options.mapProperties.map.bind("change", this.updateCollection, this);
                this.showCreateNewViewDialog();
            }
        },
        deleteView: function (e) {
            e.preventDefault();
            var self = this;
            if (!self.isLoading) {
                var selected_id = self.options.mapProperties.map.id;
                self.options.mapProperties.map.destroy({
                    success: function () {
                        var properties = self.getPropertiesToKeep();
                        self.options.mapProperties.map.unbind("change");
                        self.options.mapProperties.map = new MapModel();
                        self.options.mapProperties.map.set(properties);
                        self.options.mapProperties.map.bind("change", this.updateCollection, this);
                        self.options.mapProperties.id = undefined;
                        Backbone.history.navigate("");
                        self.broker.trigger("map:mapProperties", self.options.mapProperties);
                    },
                    error: function () {
                        alert("Failed to delete view");
                    }
                });
            }

        },
        changed_view: function () {
            var self = this;

            // todo: make an option to check for not loading categories from
            //       a saved map but keep what is already chosen.
            //var keep_categories = self.options.context_selected_map.map.attributes.categories;

            self.selected_id = parseInt(this.$("#dropdown_view_id :selected").val().trim());
            if (isNaN(self.selected_id)) {
                // assume new
                var properties = self.getPropertiesToKeep();
                self.options.mapProperties.map.unbind("change");
                self.options.mapProperties.map = new MapModel();
                self.options.mapProperties.map.set(properties);
                self.options.mapProperties.map.bind("change", this.render, this);
            } else {
                self.options.mapProperties.map = self.collection.get(self.selected_id);
            }
            //self.options.context_selected_map.map.attributes.categories = keep_categories;

            if (!self.options.mapProperties.map.isNew() && self.is_selected_view_really_changed(self.selected_id, self.options.mapProperties.map)) {
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
            //self.broker.trigger('map:loading:context_selected_map');
        },
        loadMapFromContextId: function (map_id) {
            var self = this;
            self.deactiveAndShowSpinnerWhileLoading();

            self.options.mapProperties.map.unbind("change");
            self.options.mapProperties.map = self.collection.get(map_id);
            //self.options.context_selected_map.map.bind("change", this.render, this);
            self.options.mapProperties.graph = new GraphModel({id: map_id});
            self.options.mapProperties.graph.fetch({
                success: function (model) {
                    self.options.mapProperties.graph = model;
                    //self.render();
                    self.isLoading = false;
                    self.broker.trigger('map:mapProperties', self.options.mapProperties);
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
            if (this.collection) {
                context.maps = this.collection.toJSON();
            } else {
                context.maps = null;
            }
            context.mapProperties = (this.mapProperties && this.mapProperties.toJSON()) || null;
            context.isNew = (this.map && this.map.isNew()) || null;

            /*if (this.options.context_user_default_view && this.options.context_user_default_view.attributes.viewid === this.options.mapProperties.map.attributes.viewid) {
                context.isFavorite = this.options.context_user_default_view;
            } else {
                context.isFavorite = false;
            }*/
            console.log("redner maps:");
            console.log(context.maps);

            var out = this.template(context);

            this.$el.html(out);

            if (!this.collection) {
                $(".loading", this.$el).spin();
            }

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





