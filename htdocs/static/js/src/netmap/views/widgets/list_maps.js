define([
    'netmap/views/widget_mixin',
    'plugins/netmap-extras',
    'netmap/resource',
    'netmap/collections/map',
    'netmap/models/map',
    'netmap/models/graph',
    'netmap/models/default_map',
    'netmap/views/modal/save_new_map',
    'libs-amd/text!netmap/templates/widgets/list_maps.html',
    'libs/svg-crowbar',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/spin.min',
    'plugins/jquery_spinjs'
], function (WidgetMixin, NetmapExtras, Resources, CollectionMapProperties, ModelMapProperties, GraphModel, DefaultMapModel, SaveDialogView, netmapTemplate, SVGCrowbar) {

    var ListNetmapView = Backbone.View.extend(_.extend({}, WidgetMixin, {
        tagName: "div",
        id: "choose_netview",

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:mapProperties": "setMapProperties",
            "netmap:graph": "setGraph",
            "netmap:setMapProperties:done": "render",

            "netmap:save:removeUnsavedView": "removeUnsavedViewFromCollection",
            "netmap:save:newMapProperties": "addMapPropertiesToCollection",
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest'
        },
        events: {
            "click .header .title": "toggleWidget",
            "click #save_view": "showSaveView",
            "click #save_new_view": "showSaveAsView",
            "click #delete_view": "deleteView",
            "click #set_as_user_favorite": "setFavorite",
            "click #export_svg": "exportAsSVG",
            "change #dropdown_view_id": "eventChangeActiveMapProperties"
        },
        initialize: function () {
            var self = this;
            this.isContentVisible = true;
            this.isWidgetVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(netmapTemplate);

            if (this.collection) {
                this.collection.bind("reset", this.render, this);
                this.collection.bind("change", this.eventChangeActiveMapProperties, this);
                this.collection.bind("destroy", this.close, this);
            } else {
                if (!this.options.activeMapProperties) {
                    this.options.activeMapProperties = Resources.getActiveMapModel();
                    this.options.activeMapProperties.set({"is_selected": true});
                }

                this.options.activeMapProperties.bind("change", this.render, this);

                this.collection = Resources.getMapCollection();
                if (!this.collection) {
                    this.collection = new CollectionMapProperties();
                    this.collection.fetch({
                        success: function (collection, attributes) {
                            self.collection = collection;
                            // if no netmap views loaded from API OR no active map property (read: netmap view is active)
                            if (self.collection.length <= 1 || !self.options.activeMapProperties) {
                                self.collection.unshift({}); // insert empty Map model
                                self.options.activeMapProperties = self.collection.at(0);
                                self.options.activeMapProperties.bind("change", this.render, this);
                            }
                            self.collection.bind("change", self.render, self);
                            self.render();
                        },
                        error:   function () {
                            alert("error loading collection over available views");
                        }
                    });
                }
            }

            this.broker.trigger("netmap:request:graph");
        },
        setMapProperties: function (mapProperties) {
            if (this.collection) {
                this.collection.unbind("change");
            }
            this.collection = mapProperties;
            this.collection.bind("change", this.render, this);
            this.render();
        },
        setGraph: function (graph) {
            this.graph = graph;
            this.render();
        },
        isLoading: function () {
            return !this.options.activeMapProperties ||
                !this.graph ||
                !this.collection;
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

            var context = {
                model: self.options.activeMapProperties,
                graph: self.graph,
                transactionAbortId: self.options.activeMapProperties.get('viewid'),
                isNew: isNewView
            };

            self.viewModalSave = new SaveDialogView(context);
            self.viewModalSave.render();
        },
        addMapPropertiesToCollection: function (model) {
            this.collection.add(model);
            this.options.activeMapProperties = model;
            this.render();
        },
        removeUnsavedViewFromCollection: function (model) {
            this.collection.remove(model);
        },
        setFavorite: function (e) {
            e.preventDefault();
            var self = this;
            var user_id = $("#netmap_userid").html();

            var favoriteBeforeChanging = self.collection.getFavorite();
            var updateUserDefaultMap = new DefaultMapModel({ownerid: parseInt(user_id, 10), viewid: self.options.activeMapProperties.get('viewid')});
            updateUserDefaultMap.save(this.attributes, {
                success: function (model) {
                    self.collection.setFavorite(model.get('viewid'));
                    self.render();

                },
                error: function () {
                    self.collection.setFavorite(favoriteBeforeChanging);
                    self.render();
                    alert("Error while setting favorite view");
                }
            });

        },
        exportAsSVG: function (e) {
            e.preventDefault();

            SVGCrowbar();
        },
        showSaveView: function (e) {
            e.preventDefault();

            if (!this.isLoading()) {
                this.showUpdateViewDialog();
            }
        },
        showSaveAsView: function () {
            if (!this.isLoading()) {
                this.showCreateNewViewDialog();
            }
        },
        deleteView: function (e) {
            e.preventDefault();
            var self = this;
            if (!self.isLoading()) {
                self.options.activeMapProperties.destroy({
                    success: function () {
                        var newClonedMapProperties = self.options.activeMapProperties.clone();
                        self.options.activeMapProperties.unbind("change");
                        newClonedMapProperties.unset('viewid', {silent: true});
                        newClonedMapProperties.unset('isFavorite', {silent: true});
                        newClonedMapProperties.set({'title': "Unsaved view"}, {silent: true});
                        self.options.activeMapProperties = newClonedMapProperties;


                        self.collection.resetIsSelected();
                        self.collection.add(newClonedMapProperties);

                        self.options.activeMapProperties.bind("change", self.render, self);
                        Backbone.history.navigate("view/random");
                        self.render();
                    },
                    error: function () {
                        alert("Failed to delete view");
                    }
                });
            }

        },
        eventChangeActiveMapProperties: function (e) {
            var self = this;
            var selected_id = parseInt(this.$("#dropdown_view_id :selected").val().trim(), 10);

            var model = this.collection.get(selected_id);
            if (model) {
                this.options.activeMapProperties.unbind("change");

                // remove 'Unsaved view' from dropdown if swapping to another saved view
                if (this.options.activeMapProperties.isNew() && this.options.activeMapProperties.get('title') === 'Unsaved view') {
                    this.collection.remove(this.options.activeMapProperties);
                }

                this.options.activeMapProperties = model;
                this.options.activeMapProperties.bind("change", this.render, this);

                this.collection.resetIsSelected();
                this.options.activeMapProperties.set({"is_selected": true});

                if (this.graph.get('viewid') !== selected_id) {
                    this.graph = null; // changing view, need new graph
                }
                this.broker.trigger("netmap:changeActiveMapProperty", this.options.activeMapProperties);

                Backbone.View.navigate("view/" + selected_id);
                this.broker.trigger("netmap:selectVlan", null);
                this.render();
                // setGraph should be triggered by event next by draw_map
            }
        },
        render: function () {
            var context = {};
            if (this.collection) {
                context.maps = this.collection.toJSON();
            } else {
                context.maps = null;
            }

            context.isLoading = this.isLoading();
            context.isFavorite = this.options.activeMapProperties.get('isFavorite', false);
            context.description = this.options.activeMapProperties.get('description', null);
            context.isViewEnabled = this.isViewEnabled;
            context.isFavoriteEnabled = (!this.options.activeMapProperties.isNew() && this.isViewEnabled);
            context.isWidgetVisible = this.isWidgetVisible;
            context.isWidgetCollapsible = !!this.options.isWidgetCollapsible;
            context.isBrowserSupportingSVGExport = $.browser.webkit;
            context.imagePath = NAV.imagePath;
            var out = this.template(context);

            this.$el.html(out);

            if (!this.collection) {
                $(".loading", this.$el).spin();
            }

            return this;
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));
    return ListNetmapView;
});





