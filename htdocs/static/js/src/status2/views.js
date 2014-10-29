define([
    'status/collections',
    'libs-amd/text!resources/status2/event_template.hbs',
    'libs-amd/text!resources/status2/event_info_template.hbs',
    'moment',
    'status/handlebars-helpers',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate, EventInfoTemplate, moment) {

    // This collection contains all the event-models that are to be cleared/acknowledged etc.
    var alertsToChange = new Collections.ChangeCollection();

    /** The main view containing the panel and the results list */
    var StatusView = Backbone.View.extend({
        el: '#status-page',

        localStorageShowPanelKey: 'nav.web.status.showPanel',
        toggleButtonText: {
            show: 'Show status filter',
            hide: 'Hide status filter'
        },

        events: {
            'click .set-default': 'setDefaultStatusOptions',
            'click .toggle-panel': 'togglePanel'
        },

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new EventsView({ collection: eventCollection });
            this.panelView = new PanelView({ collection: eventCollection });
            new ActionView({ collection: eventCollection });

            this.setDefaultButton = this.$el.find('.set-default');
            this.toggleButton = this.$('.toggle-panel');
            this.checkStorage();

        },

        checkStorage: function () {
            if (localStorage.getItem(this.localStorageShowPanelKey) === 'yes') {
                this.panelView.$el.show().removeClass('hidden');
                this.toggleButton.html(this.toggleButtonText.hide);
            } else {
                this.toggleButton.html(this.toggleButtonText.show);
            }
        },

        setDefaultStatusOptions: function () {
            var self = this;
            var request = $.post(
                NAV.urls.status2_save_preferences,
                this.$el.find('form').serialize()
            );

            self.setDefaultButton.removeClass('alert');  // Remove errorclass if an error occured on last try

            request.done(function(){
                self.setDefaultButton.addClass('success').removeClass('secondary');
                setTimeout(function () {
                    self.setDefaultButton.addClass('secondary').removeClass('success');
                }, 1000);
                console.log('Default status set');
            });
            request.fail(function(){
                self.setDefaultButton.addClass('alert').removeClass('secondary');
                console.log('Setting status failed');
            });
        },

        togglePanel: function () {
            var self = this;
            this.panelView.$el.slideToggle(function () {
                if (self.panelView.$el.is(':visible')) {
                    localStorage.setItem(self.localStorageShowPanelKey, 'yes');
                    self.toggleButton.html(self.toggleButtonText.hide);
                } else {
                    localStorage.setItem(self.localStorageShowPanelKey, 'no');
                    self.toggleButton.html(self.toggleButtonText.show);
                }
            });
        }

    });


    /** The main panel for filtering events */
    var PanelView = Backbone.View.extend({
        el: '#status-panel',

        refreshInterval: 1000 * 60 * 5,  // 5 minutes

        initialize: function () {
            console.log('Initializing panel view');
            this.fetchData();
            this.updateRefreshInterval();
            this.listenTo(this.collection, 'reset', this.updateRefreshInterval);
        },

        events: {
            'change form': 'fetchData',
            'submit form': 'preventSubmit'
        },

        /* Event driven methods */
        fetchData: function () {
            /* TODO: Inform user that we are trying to fetch data */
            console.log('Fetching data...');
            this.collection.url = NAV.urls.status2_api_alerthistory + '?' + this.$('form').serialize();
            console.log(this.collection.url);
            var request = this.collection.fetch({ reset: true });
            request.done(function () {
                console.log('data fetched');
            });
        },

        updateRefreshInterval: function () {
            console.log('Updating refresh interval');
            var self = this;
            clearTimeout(this.refreshCounterId);
            this.refreshCounterId = setTimeout(function () {
                self.fetchData();
            }, this.refreshInterval);
        },

        preventSubmit: function (event) {
            event.preventDefault();
        }
    });


    /** The action panel for manipulation alerts */
    var ActionView = Backbone.View.extend({
        el: '#action-panel',

        events: {
            'click .acknowledge-alerts': 'acknowledgeAlerts',
            'click .resolve-alerts .button': 'resolveAlerts',
            'click .maintenance .button': 'putOnMaintenance',
            'click .cancel-alerts-action': 'cancelAlertsAction'
        },

        htmlSnippets: {
            errorbox: '<div class="alert-box alert"></div>'
        },

        initialize: function () {
            this.listenTo(alertsToChange, 'add remove reset', this.toggleState);
            this.resolvePanel = this.$('.panel.resolve-alerts');
            this.ackPanel = this.$('.panel.acknowledge');
            this.maintenancePanel = this.$('.panel.maintenance');
        },

        toggleState: function () {
            console.log('alertsToChange: ' + alertsToChange.length);
            if (alertsToChange.length > 0) {
                this.$el.slideDown();
            } else {
                this.$el.slideUp();
            }
        },

        acknowledgeAlerts: function () {
            var comment = this.$('.acknowledge .usercomment').val(),
                self = this;

            this.ackPanel.find('.alert-box.alert').remove();

            var request = $.post(NAV.urls.status2_acknowledge_alert, {
                id: alertsToChange.pluck('id'),
                comment: comment
            });

            request.done(function () {
                self.collection.fetch();
                self.cancelAlertsAction();
            });

            request.fail(function () {
                self.ackPanel.append(
                    $(self.htmlSnippets.errorbox).html('Error acknowledging alerts'));
            });
        },

        resolveAlerts: function () {
            var self = this;

            // Clear existing alert-box
            this.resolvePanel.find('.alert-box.alert').remove();

            var request = $.post(NAV.urls.status2_clear_alert, {
                id: alertsToChange.pluck('id')
            });

            request.done(function () {
                self.collection.remove(alertsToChange.models);
                self.cancelAlertsAction();
            });

            request.fail(function () {
                self.resolvePanel.append(
                    $(self.htmlSnippets.errorbox).html('Error resolving alerts'));
            });
        },

        putOnMaintenance: function () {
            var ids = [],
                self = this,
                description = this.$('.maintenance .usercomment').val();
            alertsToChange.each(function (model) {
                if (model.get('subject_type') === 'Netbox') {
                    ids.push(model.get('id'));
                }
            });

            this.maintenancePanel.find('.alert-box.alert').remove();

            if (ids.length > 0) {
                var request = $.post(NAV.urls.status2_put_on_maintenance, {
                    id: ids,
                    description: description
                });

                request.done(function () {
                    self.collection.fetch();
                    self.cancelAlertsAction();
                });

                request.fail(function () {
                    self.maintenancePanel.append(
                        $(self.htmlSnippets.errorbox).html('Error putting on maintenance'));
                });
            }

        },

        cancelAlertsAction: function () {
            alertsToChange.reset();
        }

    });


    /** The list of status events */
    var EventsView = Backbone.View.extend({
        el: '#events-list',

        events: {
            'click thead .alert-action': 'toggleCheckboxes',
            'click thead .header': 'headerSort'
        },

        // Map columnindex to model attribute for sorting
        sortMap: {
            2: 'subject',
            3: 'alert_type',
            4: 'start_time'
        },

        initialize: function () {
            console.log('Initializing events view');

            this.body = this.$('tbody');
            this.headers = this.$('thead th');
            this.checkBox = this.$('thead .alert-action');

            this.applySort();

            this.listenTo(this.collection, 'sort', this.updateSortIndicators);
            this.listenTo(this.collection, 'reset', this.updateSortIndicators);
            this.listenTo(this.collection, 'reset', this.render);
        },

        applySort: function () {
            /** Add the header class to all cells that should be sortable */
            var self = this;
            this.$('thead th').each(function (index, element) {
                if (self.sortMap[index]) {
                    $(element).addClass('header');
                }
            });
        },

        updateSortIndicators: function () {
            /** Update sort indicators on sort */
            console.log('updateSortIndicators');

            var cellIndex = -1;

            // It's worth noting that this requires unique values in sortMap
            for (var index in this.sortMap) {
                if (this.sortMap.hasOwnProperty(index)) {
                    if (this.sortMap[index] === this.collection.sortAttribute) {
                        cellIndex = index;
                    }
                }
            }

            if (cellIndex >= 0) {
                var $element = $(this.headers[cellIndex]);
                this.headers.removeClass('headerSortUp headerSortDown');
                if (this.collection.sortDirection === -1) {
                    $element.addClass('headerSortUp');
                } else {
                    $element.addClass('headerSortDown');
                }
            }
        },

        headerSort: function (event) {
            /** Sort collection when sort-cell is clicked */
            console.log('headerSort');
            var direction = 1;

            // If we sort on the same cell twice, reverse direction
            if (this.sortMap[event.currentTarget.cellIndex] === this.collection.sortAttribute) {
                direction = this.collection.sortDirection * -1;  // Reverse direction
            }
            this.collection.sortEvents(
                this.sortMap[event.currentTarget.cellIndex], direction);
            this.render();
        },

        render: function () {
            console.log('Rendering table');
            this.$('.last-changed').html(moment().format('YYYY-MM-DD HH:mm:ss'));
            this.body.html('');
            this.collection.each(this.renderEvent, this);
        },

        renderEvent: function (nav_event) {
            var nav_event_view = new EventView({model: nav_event});
            this.body.append(nav_event_view.el);
        },

        toggleCheckboxes: function () {
            /** Toggle all checkboxes when 'main' checkbox in thead is toggled */
            if (this.checkBox.prop('checked')) {
                alertsToChange.reset(this.collection.models);
            } else {
                alertsToChange.reset();
            }
        }

    });


    var compiledEventInfoTemplate = Handlebars.compile(EventInfoTemplate);
    var EventInfoView = Backbone.View.extend({
        tagName: 'tr',

        attributes: {
            class: 'expanded hidden'
        },

        template: compiledEventInfoTemplate,

        initialize: function () {
            this.listenTo(this.model, 'remove', this.unRender);
            this.listenTo(this.model, 'change', this.render);
        },

        render: function () {
            this.$el.html(this.template(this.model.attributes));
        },

        unRender: function (model, collection) {
            /* Remove the html element associated with the view. We need to
               check that the correct collection sends the event */
            if (collection.constructor === Collections.EventCollection) {
                console.log('Unrender for subview called');
                this.remove();
            }
        },

    });


    /** The view displaying a single status event */
    var compiledEventTemplate = Handlebars.compile(EventTemplate);
    var EventView = Backbone.View.extend({
        tagName: 'tr',

        events: {
            'click .alert-action': 'toggleChangeState',
            'click .toggle-info-cell': 'renderExpandedInfo'
        },

        attributes: {
            class: 'master'
        },

        template: compiledEventTemplate,

        initialize: function () {
            this.render();
            this.markStatus();

            this.infoView = new EventInfoView({ model: this.model });

            this.listenTo(this.model, 'remove', this.unRender);
            this.listenTo(this.model, 'change', this.render);
            this.listenTo(alertsToChange, 'reset', this.toggleSelect);
        },

        markStatus: function () {
            var statuses = ['on_maintenance', 'acknowledgement'];
            for (var i = 0, l = statuses.length; i < l; i++) {
                if (this.model.get(statuses[i])) {
                    this.$el.addClass('hasStatus');
                    return;
                }
            }
        },

        renderExpandedInfo: function () {
            if (!this.$el.next().hasClass('expanded')) {
                console.log('Adding new row after this one');
                this.infoView.render();
                this.$el.after(this.infoView.el);
                this.infoView.$el.fadeIn();
            } else {
                this.infoView.$el.fadeToggle();
            }
        },

        toggleChangeState: function (event) {
            /** React to click on checkbox and add/remove from change-collection. */
            event.stopImmediatePropagation();
            if (alertsToChange.contains(this.model)) {
                alertsToChange.remove(this.model);
            } else {
                alertsToChange.add(this.model);
            }
            this.toggleSelect();
        },

        toggleSelect: function () {
            /** Highlight row and tick/untick checkbox. We separate this from
             *  the click event so that this can be run on change-collection
             *  changes */
            var checkBox = this.$('.alert-action');

            if (alertsToChange.contains(this.model)) {
                checkBox.prop('checked', true);
                this.highlight(true);
            } else {
                checkBox.prop('checked', false);
                this.highlight(false);
            }
        },

        render: function () {
            this.$el.html(this.template(this.model.attributes));
        },

        unRender: function (model, collection) {
            /* Remove the html element associated with the view. We need to
               check that the correct collection sends the event */
            var self = this;
            if (collection.constructor === Collections.EventCollection) {
                this.$el.fadeOut(function () {
                    self.remove();
                });
            }
        },

        highlight: function (flag) {
            this.$el.toggleClass('highlight', flag);
        }

    });

    return StatusView;

});
