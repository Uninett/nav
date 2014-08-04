define([
    'netmap/collections',
    'netmap/models',
    'netmap/graph',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collections, Models) {

    var ControlView = Backbone.View.extend({

        el: '#navigation-view',
        interests: {},
        events: {
            'submit #graph-search-form': 'searchGraph',
            'submit #netmap-view-create-form': 'createView',
            'change #graph-layer-select': 'changeTopologyLayer',
            'change #graph-view-select': 'changeNetmapView',
            'click .filter-category': 'updateCategoryFilter',
            'click #filter-orphan-nodes': 'updateOrphanNodesFilter',
            'click #netmap-view-save': 'saveCurrentView',
            'click #netmap-view-delete': 'deleteCurrentView',
            'click #netmap-view-default': 'setCurrentViewDefault',
            'click #netmap-view-panel-toggle': 'toggleNetmapViewPanel',
            'click #netmap-view-reset-zoom': 'fireResetZoom',
            'click #netmap-view-reset-transparency': 'fireResetTransparency',
            'click #advanced-options-panel-toggle': 'toggleAdvancedOptionsPanel',
            'click #refresh-interval input[type=radio]': 'setRefreshInterval',
            'click #refresh-interval input[type=checkbox]': 'setRefreshTrafficOnly'
        },

        initialize: function () {

            // Initialize the available views from the
            // window-object.
            this.netmapViews = new Collections.NetmapViewCollection();
            this.netmapViews.reset(window.netmapData.views);
            this.currentView = this.netmapViews.get(window.netmapData.defaultView);
            this.refreshInterval = null;

            this.initializeDOM();

            Backbone.EventBroker.register(this);
        },

        /**
         * Initializes and/or caches any necessary DOM elements.
         */
        initializeDOM: function () { // TODO: Consistent naming

            this.netmapViewPanel = this.$('#netmap-view-panel');
            this.advancedOptionsPanel = this.$('#advanced-options-panel');
            this.alertContainer = this.$('#netmap-alert-container', this.netmapViewPanel);

            this.$('#graph-view-select option[value="' + this.currentView.id + '"]').prop(
                'selected',
                true
            );

            this.setCategoriesForCurrentView();
            this.setTopologySelectForCurrentView();
        },

        toggleNetmapViewPanel: function (e) {

            this.$(e.currentTarget.children).toggleClass('fa-caret-down fa-caret-up');
            this.netmapViewPanel.toggle();
        },

        toggleAdvancedOptionsPanel: function (e) {

            this.$(e.currentTarget.children).toggleClass('fa-caret-down fa-caret-up');
            this.advancedOptionsPanel.toggle();
        },

        fireResetZoom: function () {
            Backbone.EventBroker.trigger('netmap:resetZoom');
        },

        fireResetTransparency: function () {
            Backbone.EventBroker.trigger('netmap:resetTransparency');
        },

        /**
         * Triggers when the topology layer is changed. Updates the
         * view and fires an event to the graph model
         * @param e
         */
        changeTopologyLayer: function (e) {

            var layer = e.currentTarget.value;
            this.currentView.set('topology', layer);
            Backbone.EventBroker.trigger('netmap:topologyLayerChanged', layer);
        },


        /**
         * Triggers when the current netmap view is changed
         * @param e
         */
        changeNetmapView: function (e) {

            var viewId = e.currentTarget.value;
            this.currentView = this.netmapViews.get(viewId);
            this.setCategoriesForCurrentView();
            this.setTopologySelectForCurrentView();

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);
        },

        /**
         * Triggers when a new category is selected. Updates the
         * current view and notifies the graph.
         * @param e
         */
        updateCategoryFilter: function (e) {

            var categoryId = e.currentTarget.value;
            var checked = e.currentTarget.checked;
            var categories = this.currentView.get('categories');

            if (checked) {
                categories.push(categoryId);
            } else {
                categories.splice(categories.indexOf(categoryId), 1);
            }

            Backbone.EventBroker.trigger('netmap:filterCategoriesChanged', categoryId, checked);
        },


        updateOrphanNodesFilter: function (e) {

            this.currentView.set('display_orphans', e.currentTarget.checked);

            Backbone.EventBroker.trigger('netmap:updateGraph');
        },


        saveCurrentView: function () {

            // Update `display_elinks` and remove 'ELINKS' from categories if present
            var categories = this.currentView.get('categories');
            this.currentView.set('display_elinks', _.indexOf(categories, 'ELINK') >= 0);
            this.currentView.set('categories', _.without(categories, 'ELINK'));
            this.currentView.set('last_modified', new Date());
            var isNew = this.currentView.isNew();

            var self = this;
            this.currentView.save(this.currentView.attributes,
                {
                    success: function (model) {
                        self.saveSuccessful.call(self, model, isNew);
                    },
                    error: function (model, resp) {
                        self.saveError.call(self, resp.responseText);
                    }
                }
            );
        },

        deleteCurrentView: function () {

            if (!this.currentView.isNew()) {

                var self = this;
                this.currentView.destroy({
                    success: function () {
                        self.deleteSuccessful.call(self, false);
                    },
                    error: function (model, resp) {
                        self.deleteError.call(self, resp.responseText);
                    },
                    wait: true
                });
            } else {
                this.deleteSuccessful(true);
            }
        },

        /**
         * Saves the current view as default for the current user
         */
        setCurrentViewDefault: function () {

            var self = this;

            $.ajax({
                type: 'PUT',
                url: 'views/default/' + window.netmapData.userID + '/',
                data: {view: this.currentView.id, owner: window.netmapData.userID}
            })
            .done(function () {
                var alert = self.alertContainer.html(
                    '<span class="alert-box success">View set as default</span>'
                );
                setTimeout(function () {
                    $('span', alert).fadeOut(function () {
                        this.remove();
                    });
                }, 3000);
            })
            .fail(function () {
                var alert = self.alertContainer.html(
                    '<span class="alert-box alert">Save unsuccessful!' +
                    '<a href="#" class="close">&times;</a></span>'
                );
                $('span a', alert).click(function () {
                    $('span', alert).fadeOut(function () {
                        this.remove();
                    }) ;
                });
            });
        },

        createView: function (e) {
            e.preventDefault();

            var title = $('input:text', e.currentTarget).val();
            var desc = $('textarea', e.currentTarget).val();
            var publ = $('input:checkbox', e.currentTarget).is(':checked');
            e.currentTarget.reset();

            var newView = new Models.NetmapView();
            newView.set({
                title: title,
                description: desc,
                is_public: publ
            });
            this.netmapViews.add(newView);
            this.currentView = newView;

            var viewSelect = this.$('#graph-view-select');
            viewSelect.append(new Option(title, newView.cid, true, true));

            this.setCategoriesForCurrentView();
            this.setTopologySelectForCurrentView();

            this.alertContainer.html('<span class="alert-box">Current view is unsaved</span>');

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);
        },

        /**
         * Triggers a graph search for the given query
         * @param e
         */
        searchGraph: function (e) {
            e.preventDefault();
            var query = $('#graph-search-input', e.currentTarget).val();
            Backbone.EventBroker.trigger('netmap:searchGraph', query);
        },

        /* Save callbacks */

        saveSuccessful: function (model, isNew) {

            Backbone.EventBroker.trigger('netmap:saveNodePositions');

            if (isNew) {
                /* If the model was new we need to set its value as
                 * the id given by the database.
                 */
                this.$('#graph-view-select option[value="' + model.cid + '"]')
                    .attr('id', model.id)
                    .attr('value', model.id);
            }

            var alert = this.alertContainer.html('<span class="alert-box success">View saved successfully</span>');
            setTimeout(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                });
            }, 3000);
        },

        deleteSuccessful: function (isNew) {

            var value;
            if (isNew) {
                value = this.currentView.cid;
            } else {
                value = this.currentView.id;
            }

            this.$('#graph-view-select option[value="' + value + '"]').remove();
            var selected = this.$('#graph-view-select option:selected').val();
            this.currentView = this.netmapViews.get(selected);
            this.setCategoriesForCurrentView();
            this.setTopologySelectForCurrentView();

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);

            var alert = this.alertContainer.html('<span class="alert-box success">Successfully deleted view</span>');
            setTimeout(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                });
            }, 3000);
        },

        saveError: function (resp) { console.log(resp);

            var alert = this.alertContainer.html(
                '<span class="alert-box alert">Save unsuccessful!' +
                    '<a href="#" class="close">&times;</a></span>'
            );
            $('span a', alert).click(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                }) ;
            });
        },

        deleteError: function (resp) { console.log(resp);

            var alert = this.alertContainer.html(
                '<span class="alert-box alert">Delete unsuccessful!' +
                    '<a href="#" class="close">&times;</a></span>'
            );
            $('span a', alert).click(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                }) ;
            });
        },

        setCategoriesForCurrentView: function () {

            var newCategories = this.currentView.get('categories');
            _.each(this.$('.filter-category'), function (elem) {
                elem.checked = _.contains(newCategories, elem.value);
            });
            this.$('#filter-orphan-nodes').prop(
                'checked',
                this.currentView.get('display_orphans')
            );
        },

        setTopologySelectForCurrentView: function () {

            var layer = this.currentView.get('topology');

            this.$('#graph-layer-select option[value="' + layer + '"]').prop(
                'selected',
                layer
            );
        },

        setRefreshInterval: function (e) {

            var self = this;
            var val = parseInt(e.currentTarget.value);

            if (val === -1) {
                console.log('refresh off');
                if (this.refreshInterval !== null) {
                    clearInterval(this.refreshInterval);
                }
                $('#refresh-counter', this.advancedOptionsPanel).html('');
            } else {
                clearInterval(this.refreshInterval);
                var counter = val * 60;
                this.refreshInterval = setInterval(function () {
                    counter--;
                    if (counter === 0) {
                        Backbone.EventBroker.trigger('netmap:refreshGraph');
                        counter = val * 60;
                    }
                    $('#refresh-counter', self.advancedOptionsPanel).html(
                        '<small>Refreshing in ' + counter + ' sec</small>'
                    );
                }, 1000);
            }
        },

        setRefreshTrafficOnly: function (e) {
            this.currentView.refreshTrafficOnly = e.currentTarget.checked;
        }
    });

    return ControlView;
});
