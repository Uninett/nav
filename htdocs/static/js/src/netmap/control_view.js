define([
    'netmap/collections',
    'netmap/models',
    'netmap/graph',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/jquery-ui.min'
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
            'click #netmap-view-create': 'displayCreateView',
            'submit #filter-room-location-form': 'filterByRoomOrLocation',
            'change #graph-layer-select': 'changeTopologyLayer',
            'change #graph-view-select': 'changeNetmapView',
            'click .filter-category': 'updateCategoryFilter',
            'click .filter-string-remove': 'removeRoomOrLocationFilter',
            'click #filter-orphan-nodes': 'updateOrphanNodesFilter',
            'click #netmap-view-save': 'saveCurrentView',
            'click #netmap-view-edit': 'displayEditView',
            'click #netmap-view-delete': 'deleteCurrentView',
            'click #netmap-view-default': 'setCurrentViewDefault',
            'click #netmap-view-panel-toggle': 'toggleNetmapViewPanel',
            'click #netmap-view-zoom-to-extent': 'fireZoomToExtent',
            'click #netmap-view-reset-zoom': 'fireResetZoom',
            'click #netmap-view-reset-transparency': 'fireResetTransparency',
            'click #refresh-interval input[type=radio]': 'setRefreshInterval',
            'click #refresh-interval input[type=checkbox]': 'setRefreshTrafficOnly',
            'click #netmap-view-unfix-nodes': 'fireUnfixNodes',
            'click #netmap-view-fix-nodes': 'fireFixNodes',
            'click #netmap-view-toggle-force': 'fireToggleForce'
        },

        filterLabelTemplate: _.template('' +
            '<span class="label secondary" data-string="<%= filter %>">' +
            '<%= filter %> <i class="fa fa-times filter-string-remove"></i>' +
            '</span>'),

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

            this.refreshInterval = null;
            this.updateFavoriteViewEnabled = true;
            this.saveDeleteViewEnabled = true;

            this.initializeDOM();
            this.initializeDialogs();

            Backbone.EventBroker.register(this);
        },

        /** Initializes and/or caches any necessary DOM elements. */
        initializeDOM: function () {

            this.netmapViewPanel = this.$('#netmap-view-panel');
            this.middleAlertContainer = this.$('#netmap-middle-alert-container');
            this.leftAlertContainer = this.$('#netmap-left-alert-container');

            this.$('#filter-room-location-form input[type=text]', this.netmapViewPanel).autocomplete({
                source: window.netmapData.roomsAndLocations,
                autoFocus: true
            });

            this.$('#graph-view-select option[value="' + this.currentView.id + '"]').prop(
                'selected',
                true
            );

            this.updateControlsForCurrentView();
        },

        initializeDialogs: function () {
            var self = this;

            /** Create dialog */
            this.createNewViewForm = $('#netmap-view-create-form');
            this.createNewViewForm.dialog({
                autoOpen: false,
                modal: true,
                title: 'Create new view'
            });

            this.createNewViewForm.submit(function(e){
                e.preventDefault();
                self.createView.call(self);
            });

            /** Edit dialog */
            this.editViewForm = $('#netmap-view-edit-form');
            this.editViewForm.dialog({
                autoOpen: false,
                modal: true,
                title: 'Edit ' + this.currentView.get('title')
            });

            this.editViewForm.submit(function(e){
                e.preventDefault();
                self.editCurrentView.call(self);
            });


        },

        toggleNetmapViewPanel: function (e) {
            $('#netmap-view-panel').toggle(function () {
                $(document).foundation('equalizer', 'reflow');
            });
            this.$(e.currentTarget.children).toggleClass('fa-caret-down fa-caret-up');
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

        fireFixNodes: function () {
            Backbone.EventBroker.trigger('netmap:fixNodes');
        },

        /**
         * Triggers when the topology layer is changed. Updates the
         * view and fires an event to the graph model
         */
        changeTopologyLayer: function (e) {
            var layer = parseInt(e.currentTarget.value);
            this.currentView.set('topology', layer);
            this.currentView.trigger('attributeChange');
            Backbone.EventBroker.trigger('netmap:topologyLayerChanged', layer);
        },

        /**
         * Change the controls to reflect view change and notify the GraphView
         */
        changeNetmapView: function (e) {
            var viewId = $(e.currentTarget).find(':selected').val();
            this.currentView = this.netmapViews.get(viewId);

            if (!this.currentView) {
                // This clause is not needed for Backbone>=0.9.9, but should
                // cause no harm after upgrade.
                this.currentView = this.netmapViews.getByCid(viewId);
            }

            this.updateControlsForCurrentView();

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

            this.currentView.trigger('attributeChange');
            Backbone.EventBroker.trigger('netmap:filterCategoriesChanged', categoryId, checked);
        },

        updateOrphanNodesFilter: function (e) {
            this.currentView.set('display_orphans', e.currentTarget.checked);
            this.currentView.trigger('attributeChange');
            Backbone.EventBroker.trigger('netmap:updateGraph');
        },

        saveCurrentView: function () {
            console.log('saveCurrentView');

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
                        self.saveSuccessful.call(self, model, {'isNew': isNew}, self.middleAlertContainer);
                    },
                    error: function (model, resp) {
                        self.saveError.call(self, resp.responseText);
                    }
                }
            );
        },

        displayEditView: function () {
            console.log('displayEditView');

            $('input:text', this.editViewForm).val(this.currentView.get('title'));
            $('textarea', this.editViewForm).val(this.currentView.get('description'));
            $('input:checkbox', this.editViewForm).attr('checked', this.currentView.get('is_public'));
            this.editViewForm.dialog('open');

        },

        editCurrentView: function () {
            console.log('editCurrentView');
            if (!this.saveDeleteViewEnabled) {
                // This control is disabled
                return;
            }

            // Set all necessary attributes
            var self = this,
                form = $('#netmap-view-edit-form');

            var data = {
                title: $('input:text', form).val(),
                description: $('textarea', form).val(),
                is_public: $('input:checkbox', form).is(':checked')
            };

            this.currentView.save(data, {
                success: function (model) {
                    console.log(model);
                    self.saveSuccessful.call(self, model, {'isUpdated': true}, self.leftAlertContainer);
                },
                error: function (model, resp) {
                    self.saveError.call(self, resp.responseText);
                }
            });

            this.editViewForm.dialog('close');

        },

        deleteCurrentView: function () {

            if (!this.saveDeleteViewEnabled) {
                // This control is disabled
                return;
            }

            if(confirm('Delete this view?')) {
                if (!this.currentView.isNew()) {
                    var self = this;
                    console.log('We want to delete view with id ' + this.currentView.id);
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
                var alert = self.leftAlertContainer.html(
                    '<span class="alert-box success">View set as default</span>'
                );
                setTimeout(function () {
                    $('span', alert).fadeOut(function () {
                        this.remove();
                    });
                }, 3000);
            })
            .fail(function () {
                var alert = self.leftAlertContainer.html(
                    '<span class="alert-box alert">Error setting default view' +
                    '<a href="#" class="close">&times;</a></span>'
                );
                $(alert).click(function () {
                    $(alert).fadeOut(function () {
                        this.remove();
                    }) ;
                });
            });
        },

        displayCreateView: function () {
            console.log('displayCreateView');
            this.createNewViewForm.dialog('open');
        },

        createView: function () {
            var newView = new Models.NetmapView(_.omit(
                this.currentView.attributes, 'viewid', 'title', 'description', 'is_public'));
            newView.set({owner: window.netmapData.userLogin});
            this.netmapViews.add(newView);
            this.currentView = newView;

            // Set all necessary attributes
            var form = $('#netmap-view-create-form');
            this.currentView.set('title', $('input:text', form).val());
            this.currentView.set('description', $('textarea', form).val());
            this.currentView.set('is_public', $('input:checkbox', form).is(':checked'));

            var viewSelect = this.$('#graph-view-select');
            viewSelect.append(new Option(this.currentView.get('title') + ' (' +
                window.netmapData.userLogin + ')',
                this.currentView.cid, true, true));

            this.updateControlsForCurrentView();
            this.saveCurrentView();
            this.createNewViewForm.dialog('close');

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
            $('#filter-labels', this.netmapViewPanel).append(this.filterLabelTemplate({filter: query}));
            Backbone.EventBroker.trigger('netmap:filterByRoomOrLocation', query);
        },


        removeRoomOrLocationFilter: function (e) {
            e.preventDefault();
            var elem = $(e.currentTarget).parent();
            var filterString = elem.data('string');
            elem.remove();
            Backbone.EventBroker.trigger('netmap:removeFilter', filterString);
        },

        saveSuccessful: function (model, state, alertContainer) {

            Backbone.EventBroker.trigger('netmap:saveNodePositions');

            if (state.isNew) {
                /* If the model was new we need to set its value as
                 * the id given by the database.
                 */
                this.$('#graph-view-select option[value="' + model.cid + '"]')
                    .attr('id', model.id)
                    .attr('value', model.id)
                    .html(model.get('title') + ' (' + model.get('owner') + ')');
            } else if (state.isUpdated) {
                this.$('#graph-view-select option[value="' + model.id + '"]')
                    .html(model.get('title') + ' (' + model.get('owner') + ')');
            }

            this.setUpdateFavoriteViewEnables(true);

            var alert = alertContainer.html('<span class="alert-box success">View saved successfully</span>');
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
            this.updateControlsForCurrentView();

            Backbone.EventBroker.trigger('netmap:netmapViewChanged', this.currentView);

            var alert = this.leftAlertContainer.html('<span class="alert-box success">Successfully deleted view</span>');
            setTimeout(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                });
            }, 3000);
        },

        saveError: function (resp) { console.log(resp);

            var alert = this.leftAlertContainer.html(
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

            var alert = this.leftAlertContainer.html(
                '<span class="alert-box alert">Delete unsuccessful!' +
                    '<a href="#" class="close">&times;</a></span>'
            );
            $('span a', alert).click(function () {
                $('span', alert).fadeOut(function () {
                    this.remove();
                }) ;
            });
        },

        updateControlsForCurrentView: function () {
            this.setCategoriesForCurrentView();
            this.setLocationRoomFilterForCurrentView();
            this.setTopologySelectForCurrentView();
            this.setViewButtonsForCurrentView();
            this.resetRefreshControls();
        },

        fireToggleForce: function (e) {
            var targetElem = this.$(e.currentTarget);
            var statusOn = targetElem.data('status') === 'on';
            if (statusOn) {
                targetElem.data('status', 'off');
                targetElem.html('Start animation <i class="fa fa-play"></i>');
            } else { // off
                targetElem.data('status', 'on');
                targetElem.html('Stop animation <i class="fa fa-stop"></i>');
            }
            Backbone.EventBroker.trigger('netmap:toggleForce', statusOn);
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

            var self = this;
            var elem = $('#filter-labels', this.netmapViewPanel).empty();
            var filters = this.currentView.get('location_room_filter');

            if (filters) {
                filters = filters.split('|');
                _.each(filters, function (filter) {
                    elem.append(self.filterLabelTemplate({filter: filter}));
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
                $('#refresh-counter').html('');
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
                    $('#refresh-counter').html(
                        '<small>Refreshing in ' + counter + ' sec</small>'
                    );
                }, 1000);
            }
        },

        resetRefreshControls: function () {

            this.currentView.refreshTrafficOnly = false;
            this.$('#refresh-interval input[type=checkbox]').attr('checked', false);

            this.$('#refresh-interval input[type=radio]')[0].checked = true;

            clearInterval(this.refreshInterval);
            this.$('#refresh-counter').html('');
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
