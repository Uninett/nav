define([
    'netmap/collections',
    'netmap/models',
    'netmap/graph',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/jquery-ui-1.8.21.custom.min'
], function (Collections, Models) {

    /**
     * This view is responsible for responding to DOM events
     * and dispatching the necessary event on to th GraphView.
     */
    var ControlView = Backbone.View.extend({

        el: '#navigation-view',
        interests: {},
        events: {
            'submit #graph-search-form': 'searchGraph',
            'reset #graph-search-form': 'resetSearch',
            'submit #netmap-view-create-form': 'createView',
            'submit #filter-room-location-form': 'filterByRoomOrLocation',
            'change #graph-layer-select': 'changeTopologyLayer',
            'change #graph-view-select': 'changeNetmapView',
            'click .filter-category': 'updateCategoryFilter',
            'click .filter-string-remove': 'removeRoomOrLocationFilter',
            'click #filter-orphan-nodes': 'updateOrphanNodesFilter',
            'click #netmap-view-save': 'saveCurrentView',
            'click #netmap-view-delete': 'deleteCurrentView',
            'click #netmap-view-default': 'setCurrentViewDefault',
            'click #netmap-view-panel-toggle': 'toggleNetmapViewPanel',
            'click #netmap-view-zoom-to-extent': 'fireZoomToExtent',
            'click #netmap-view-reset-zoom': 'fireResetZoom',
            'click #netmap-view-reset-transparency': 'fireResetTransparency',
            'click #advanced-options-panel-toggle': 'toggleAdvancedOptionsPanel',
            'click #refresh-interval input[type=radio]': 'setRefreshInterval',
            'click #refresh-interval input[type=checkbox]': 'setRefreshTrafficOnly',
            'click #netmap-view-unfix-nodes': 'fireUnfixNodes',
            'click #netmap-view-toggle-force': 'fireToggleForce'
        },

        initialize: function () {

            // Initialize the available views from the
            // window-object.
            this.netmapViews = new Collections.NetmapViewCollection();
            this.netmapViews.reset(window.netmapData.views);

            // Set current view to the users default view. If no default view is
            // set, set the current view to be the first in the list of available
            // views. If none are available use the default object
            this.currentView = this.netmapViews.get(window.netmapData.defaultView) ||
                this.netmapViews.at(0) || new Models.NetmapView();

            // Backup attributes
            this.backupAttributes = _.omit(this.currentView.attributes, 'categories');
            this.backupAttributes.categories = this.currentView.get('categories').slice();

            this.refreshInterval = null;
            this.updateFavoriteViewEnabled = true;
            this.saveDeleteViewEnabled = true;

            this.initializeDOM();

            Backbone.EventBroker.register(this);
        },

        /** Initializes and/or caches any necessary DOM elements. */
        initializeDOM: function () {

            this.netmapViewPanel = this.$('#netmap-view-panel');
            this.advancedOptionsPanel = this.$('#advanced-options-panel');
            this.alertContainer = this.$('#netmap-alert-container', this.netmapViewPanel);

            this.$('#filter-room-location-form input[type=text]', this.netmapViewPanel).autocomplete({
                source: window.netmapData.roomsAndLocations,
                autoFocus: true
            });

            this.$('#graph-view-select option[value="' + this.currentView.id + '"]').prop(
                'selected',
                true
            );

            this.setFormForCurrentView();
            this.setCategoriesForCurrentView();
            this.setLocationRoomFilterForCurrentView();
            this.setTopologySelectForCurrentView();
            this.setViewButtonsForCurrentView();
            this.resetRefreshControls();
        },

        toggleNetmapViewPanel: function (e) {
            this.$(e.currentTarget.children).toggleClass('fa-caret-down fa-caret-up');
            this.netmapViewPanel.toggle();
        },

        toggleAdvancedOptionsPanel: function (e) {
            this.$(e.currentTarget.children).toggleClass('fa-caret-down fa-caret-up');
            this.advancedOptionsPanel.toggle();
        },

        fireZoomToExtent: function () {
            Backbone.EventBroker.trigger('netmap:zoomToExtent');
        },

        fireResetZoom: function () {
            Backbone.EventBroker.trigger('netmap:resetZoom');
        },

        fireResetTransparency: function () {
            Backbone.EventBroker.trigger('netmap:resetTransparency');
        },

        fireUnfixNodes: function () {
            Backbone.EventBroker.trigger('netmap:unfixNodes');
        },

        fireToggleForce: function (e) {

            var targetElem = this.$(e.currentTarget);
            var statusOn = targetElem.data('status') === 'on';
            if (statusOn) {
                targetElem.data('status', 'off');
                targetElem.html('Start force<img src="/static/images/lys/red.png">');
            } else { // off
                targetElem.data('status', 'on');
                targetElem.html('Pause force<img src="/static/images/lys/green.png">');
            }
            Backbone.EventBroker.trigger('netmap:toggleForce', statusOn);
        },

        /**
         * Triggers when the topology layer is changed. Updates the
         * view and fires an event to the graph model
         */
        changeTopologyLayer: function (e) {

            var layer = e.currentTarget.value;
            this.currentView.set('topology', layer);
            Backbone.EventBroker.trigger('netmap:topologyLayerChanged', layer);
        },

        /**
         * Change the controls to reflect view change and notify the GraphView
         */
        changeNetmapView: function (e) {

            // Reset attributes from backup
            this.currentView.set(this.backupAttributes);

            var viewId = e.currentTarget.value;
            this.currentView = this.netmapViews.get(viewId);
            if (!this.currentView) {
                // This clause is not needed for Backbone>=0.9.9, but should
                // cause no harm after upgrade.
                this.currentView = this.netmapViews.getByCid(viewId);
            }
            this.backupAttributes = _.omit(this.currentView.attributes, 'categories');
            this.backupAttributes.categories = this.currentView.get('categories').slice();

            var unsaved = this.currentView.isNew() ?
                '<span class="alert-box">Current view is unsaved</span>' : '';
            this.alertContainer.html(unsaved);
            this.setFormForCurrentView();
            this.setCategoriesForCurrentView();
            this.setLocationRoomFilterForCurrentView();
            this.setTopologySelectForCurrentView();
            this.setViewButtonsForCurrentView();
            this.resetRefreshControls();

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);
        },

        /**
         * Triggers on category select/unselect. Updates the current netmapView
         * and notifies the GraphView.
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

            if (!this.saveDeleteViewEnabled) {
                // This control is disabled
                return;
            }

            // Update `display_elinks` and remove 'ELINKS' from categories if present
            var categories = this.currentView.get('categories');
            this.currentView.set('display_elinks', _.indexOf(categories, 'ELINK') >= 0);
            this.currentView.set('categories', _.without(categories, 'ELINK'));
            this.currentView.set('last_modified', new Date());
            this.currentView.set('location_room_filter', this.currentView.filterStrings.join('|'));
            this.currentView.baseZoom = this.currentView.get('zoom');
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

            if (!this.saveDeleteViewEnabled) {
                // This control is disabled
                return;
            }

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

        /** Saves the current view as default for the current user */
        setCurrentViewDefault: function () {

            if (!this.updateFavoriteViewEnabled) {
                // This control is disabled
                return;
            }

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

            var newView = new Models.NetmapView(_.omit(
                this.currentView.attributes, 'viewid'));
            newView.set({
                title: title,
                description: desc,
                is_public: publ,
                owner: window.netmapData.userLogin
            });
            this.netmapViews.add(newView);

            this.currentView.set(this.backupAttributes);
            this.currentView = newView;
            this.backupAttributes = _.omit(this.currentView.attributes, 'categories');
            this.backupAttributes.categories = this.currentView.get('categories').slice();

            var viewSelect = this.$('#graph-view-select');
            viewSelect.append(new Option(title + ' (' + window.netmapData.userLogin + ')',
                this.currentView.cid, true, true));

            this.setFormForCurrentView();
            this.setCategoriesForCurrentView();
            this.setLocationRoomFilterForCurrentView();
            this.setTopologySelectForCurrentView();
            this.setViewButtonsForCurrentView();
            this.resetRefreshControls();

            this.alertContainer.html('<span class="alert-box">Current view is unsaved</span>');

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);
        },

        /**  Triggers a graph search for the given query */
        searchGraph: function (e) {
            e.preventDefault();
            var query = $('#graph-search-input', e.currentTarget).val();
            if (query) {
                Backbone.EventBroker.trigger('netmap:searchGraph', query);
            } else {
                this.resetSearch(e);
            }
        },

        /** Triggers resets for zoom and transparency */
        resetSearch: function (e) {
            Backbone.EventBroker.trigger('netmap:resetTransparency');
            Backbone.EventBroker.trigger('netmap:resetZoom');
        },

        /** Fires when a new location-/room-filter is added */
        filterByRoomOrLocation: function (e) {
            e.preventDefault();
            var query = $('input[type="text"]', e.currentTarget).val();
            e.currentTarget.reset();
            $('#filter-labels', this.netmapViewPanel).append(
                '<span class="label secondary" data-string="' + query + '">' + query +
                    '<a href="#" class="filter-string-remove">&times;</a></span>'
            );
            Backbone.EventBroker.trigger('netmap:filterByRoomOrLocation', query);
        },


        removeRoomOrLocationFilter: function (e) {
            e.preventDefault();
            var elem = $(e.currentTarget).parent();
            var filterString = elem.data('string');
            elem.remove();
            Backbone.EventBroker.trigger('netmap:removeFilter', filterString);
        },

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

            this.backupAttributes = this.currentView.attributes;
            this.setUpdateFavoriteViewEnables(true);

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
            this.currentView = this.netmapViews.get(selected) || new Models.NetmapView();
            this.setFormForCurrentView();
            this.setCategoriesForCurrentView();
            this.setLocationRoomFilterForCurrentView();
            this.setTopologySelectForCurrentView();
            this.setViewButtonsForCurrentView();
            this.resetRefreshControls();

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

        setFormForCurrentView: function () {
            var form = $('#netmap-view-create-form', this.netmapViewPanel);
            $('input:text', form).val(this.currentView.get('title'));
            $('textarea', form).val(this.currentView.get('description'));
            $('input:checkbox', form).prop('checked', this.currentView.get('is_public'));
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

        setLocationRoomFilterForCurrentView: function () {

            var elem = $('#filter-labels', this.netmapViewPanel).empty();
            var filters = this.currentView.get('location_room_filter');

            if (filters) {
                filters = filters.split('|');
                _.each(filters, function (filter) {
                    elem.append(
                        '<span class="label secondary" data-string="' + filter +
                        '">' + filter +
                        '<a href="#" class="filter-string-remove">&times;</a></span>'
                    );
                });
                this.currentView.filterStrings = filters;
            } else {
                this.currentView.filterStrings = [];
            }
        },

        setTopologySelectForCurrentView: function () {

            var layer = this.currentView.get('topology');

            this.$('#graph-layer-select option[value="' + layer + '"]').prop(
                'selected',
                layer
            );
        },

        /**
         * Enables/disables the appropriate buttons for the current view
         */
        setViewButtonsForCurrentView: function () {

            // No view exists
            if (!this.netmapViews.length) {
                this.setUpdateFavoriteViewEnables(false);
                this.setSaveDeleteViewEnabled(false);

            // User does not own selected view
            } else if (!window.netmapData.admin &&
                    this.currentView.get('owner') !== window.netmapData.userLogin) {
                this.setUpdateFavoriteViewEnables(true);
                this.setSaveDeleteViewEnabled(false);

            // View is unsaved
            } else if (this.currentView.isNew()) {
                this.setUpdateFavoriteViewEnables(false);
                this.setSaveDeleteViewEnabled(true);

            // User owns the selected view
            } else {
                this.setUpdateFavoriteViewEnables(true);
                this.setSaveDeleteViewEnabled(true);
            }
        },

        setRefreshInterval: function (e) {

            var self = this;
            var val = parseInt(e.currentTarget.value);

            if (val === -1) {
                if (this.refreshInterval !== null) {
                    // Clear old interval function
                    clearInterval(this.refreshInterval);
                }
                $('#refresh-counter', this.advancedOptionsPanel).html('');
            } else {
                // Clear old interval function
                clearInterval(this.refreshInterval);
                var counter = val * 60;

                // Create a refresh interval function which dispatches a
                // refresh event to the GraphView when the counter reaches 0
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

        resetRefreshControls: function () {

            this.currentView.refreshTrafficOnly = false;
            this.$('#refresh-interval input[type=checkbox]',
                this.advancedOptionsPanel).attr('checked', false);

            this.$('#refresh-interval input[type=radio]')[0].checked = true;

            clearInterval(this.refreshInterval);
            this.$('#refresh-counter', this.advancedOptionsPanel).html('');
        },

        setRefreshTrafficOnly: function (e) {
            this.currentView.refreshTrafficOnly = e.currentTarget.checked;
        },


        setUpdateFavoriteViewEnables: function (enabled) {

            this.updateFavoriteViewEnabled = enabled;
            var setFavoriteViewButton = $('#netmap-view-default', this.netmapViewPanel);
            setFavoriteViewButton.toggleClass('disabled', !enabled);
        },

        setSaveDeleteViewEnabled: function (enabled) {

            this.saveDeleteViewEnabled = enabled;
            var saveViewButton = $('#netmap-view-save', this.netmapViewPanel);
            var deleteViewButton = $('#netmap-view-delete', this.netmapViewPanel);
            saveViewButton.toggleClass('disabled', !enabled);
            deleteViewButton.toggleClass('disabled', !enabled);
        }
    });

    return ControlView;
});
