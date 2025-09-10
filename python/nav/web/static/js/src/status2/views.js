define([
    'libs/spin.min',
    'status/collections',
    'libs-amd/text!resources/status2/event_template.hbs',
    'moment',
    'libs/handlebars',
    'status/handlebars-helpers',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Spinner, Collections, EventTemplate, moment, Handlebars) {

    // This collection contains all the event-models that are to be cleared/acknowledged etc.
    var alertsToChange = new Collections.ChangeCollection();

    var spinner = new Spinner({position: 'relative', top: '0.5em', left: '-1em', scale: 0.5});

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
            $('#status-page').show();

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
                this.$el.find('#status-panel form').serialize()
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

    function startSpinner() {
        spinner.spin();
        $('#fetch-spinner').append(spinner.el);
    }

    function stopSpinner() {
        spinner.stop();
    }

    /** The main panel for filtering events */
    var PanelView = Backbone.View.extend({
        el: '#status-panel',

        refreshInterval: 1000 * 60 * 5,  // 5 minutes

        initialize: function () {
            console.log('Initializing panel view');
            // This is not the "correct" way of doing this.
            this.alertBox = $('#status-page-fetch-alert');
            this.fieldList = this.$el.find('.field_list > div');
            this.presentFilters();
            this.fetchData();
            this.updateRefreshInterval();
            this.listenTo(this.collection, 'reset', this.updateRefreshInterval);
        },

        events: {
            'change #id_status_filters': 'toggleFilters',
            'change form': 'fetchData',
            'submit form': 'preventSubmit'
        },

        /**
         * When the page loads hide all filters then display all filters that
         * the user has selected options in
         */
        presentFilters: function () {
            this.fieldList.hide();
            var selectedOptions = this.fieldList.find('[selected]');
            selectedOptions.closest('.ctrlHolder').show();
            var filtersWithValue = $.map(selectedOptions.closest('select'), function (element) {
                return element.name;
            });
            $('#id_status_filters').select2('val', filtersWithValue);
        },

        /* Event driven methods */
        /**
         * Toggle filters based on the user selecting and deselecting filters.
         * When removing a filter also unselect the selected options from that
         * filter.
         */
        toggleFilters: function (event) {
            event.stopPropagation();
            if ('added' in event) {
                this.$el.find('#id_' + event.added.id).closest('.ctrlHolder').show();
            }
            if ('removed' in event) {
                var removed = this.$el.find('#id_' + event.removed.id);
                removed.closest('.ctrlHolder').hide();
                removed.select2('val', '');  // Unselect all options
                // Unselecting does not trigger the change-event that again
                // triggers fetching data, so we have to do it ourself
                this.fetchData();
            }
        },

        fetchData: function () {
            var self = this;
            console.log('Fetching data...');
            startSpinner();
            this.alertBox.addClass('hidden');
            this.collection.url = NAV.urls.status2_api_alerthistory + '?' + this.$('form').serialize();
            console.log(this.collection.url);
            var request = this.collection.fetch({ reset: true, data: {page_size: 1000} });
            request.done(function () {
                console.log('data fetched');
                stopSpinner();
            });
            request.fail(function () {
                console.log('Failed to fetch data');
                self.alertBox.removeClass('hidden');
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
        el: '#action-panel-revised',

        events: {
            'click .submit-action': 'submitAction',
            'change select': 'showOrHideCommentField',
            'click .help-toggle': 'toggleHelp'
        },
        helpToggleText: {
            show: 'Show action details',
            hide: 'Hide action details'
        },
        initialize: function () {
            this.actionSelect = this.$('select');
            this.comment = this.$('.usercomment');
            this.commentWrapper = this.$('.usercomment-wrapper');
            this.feedback = this.$('.feedback');
            this.helpContent = this.$('#action-help-content');
            this.helpToggle = this.$('.help-toggle');
            this.helpText = this.$('.help-text');
        },
        toggleHelp: function(event) {
            event.preventDefault();
            const self = this;

            this.helpContent.slideToggle(200, function() {
                if (self.helpContent.is(':visible')) {
                    self.helpText.text(self.helpToggleText.hide);
                    self.helpToggle.attr('aria-expanded', 'true');
                } else {
                    self.helpText.text(self.helpToggleText.show);
                    self.helpToggle.attr('aria-expanded', 'false');
                }
            });
        },
        submitAction: function() {
            var self = this,
                action = this.actionSelect.val();

            console.log('Action:' + action);
            this.feedback.hide(); // Hide previous feedback

            var actions = {
                'acknowledge': this.acknowledgeAlerts,
                'clear': this.resolveAlerts,
                'maintenance': this.putOnMaintenance,
                'delete': this.deleteModuleOrChassis
            };

            if (action && alertsToChange.length > 0) {
                actions[action].call(this);
            } else if (!action) {
                this.give_warning_feedback('You must choose an action');
            } else if (alertsToChange.length <= 0) {
                this.give_warning_feedback('You must choose one or more alerts');
            }

            console.log(alertsToChange);

        },

        showOrHideCommentField: function() {
            var actionsWithComment = ['acknowledge', 'maintenance'];
            if (actionsWithComment.indexOf(this.actionSelect.val()) >= 0) {
                this.commentWrapper.show();
            } else {
                this.commentWrapper.hide();
            }
        },

        give_feedback: function(msg, klass) {
            klass = typeof klass !== 'undefined' ? klass : 'success';
            this.feedback.removeClass('alert warning').addClass(klass).html(msg);
            this.feedback.fadeIn();
        },

        give_error_feedback: function(msg) {
            this.give_feedback(msg, 'alert');
        },

        give_warning_feedback: function(msg) {
            this.give_feedback(msg, 'warning');
        },

        acknowledgeAlerts: function () {
            var self = this;

            var request = $.post(NAV.urls.status2_acknowledge_alert, {
                id: alertsToChange.pluck('id'),
                comment: this.comment.val(),
                csrfmiddlewaretoken: $('#action-panel-revised [name=csrfmiddlewaretoken]').val()
            });

            request.done(function () {
                self.collection.fetch();
                self.give_feedback('Alerts acknowledged');
                Backbone.EventBroker.trigger('eventsview:reset');
            });

            request.fail(function () {
                self.give_error_feedback('Error acknowledging alerts');
            });
        },

        resolveAlerts: function () {
            console.log('resolveAlerts');
            var self = this;

            var request = $.post(NAV.urls.status2_clear_alert, {
                id: alertsToChange.pluck('id'),
                csrfmiddlewaretoken: $('#action-panel-revised [name=csrfmiddlewaretoken]').val()
            });

            request.done(function () {
                self.collection.remove(alertsToChange.models);
                self.give_feedback('Alerts cleared');
                Backbone.EventBroker.trigger('eventsview:reset');
            });

            request.fail(function () {
                self.give_error_feedback('Error clearing alerts');
            });
        },

        putOnMaintenance: function () {
            console.log('putOnMaintenance');
            var ids = [],
                self = this,
                description = this.$('.usercomment').val();
            alertsToChange.each(function (model) {
                if (model.get('subject_type') === 'Netbox') {
                    ids.push(model.get('id'));
                }
            });

            if (ids.length > 0) {
                var request = $.post(NAV.urls.status2_put_on_maintenance, {
                    id: ids,
                    description: description,
                    csrfmiddlewaretoken: this.$('[name=csrfmiddlewaretoken]').val()
                });

                request.done(function () {
                    self.collection.fetch();
                    self.give_feedback('Maintenances created');
                    Backbone.EventBroker.trigger('eventsview:reset');
                });

                request.fail(function () {
                    self.give_error_feedback('Error putting on maintenance');
                });
            } else {
                self.give_error_feedback('None of the subjects are netboxes or services');
            }
        },

        deleteModuleOrChassis: function() {
            console.log('putOnMaintenance');
            var ids = [],
                self = this,
                description = this.$('.usercomment').val();
            alertsToChange.each(function (model) {
                if (['Module', 'NetboxEntity'].indexOf(model.get('subject_type')) >= 0) {
                    ids.push(model.get('id'));
                }
            });

            if (ids.length > 0) {
                var request = $.post(NAV.urls.status2_delete_module_or_chassis, {
                    id: ids,
                    description: description,
                    csrfmiddlewaretoken: this.$('[name=csrfmiddlewaretoken]').val()
                });

                request.done(function () {
                    self.collection.fetch();
                    self.give_feedback('Modules or chassis deleted');
                    Backbone.EventBroker.trigger('eventsview:reset');
                });

                request.fail(function () {
                    self.give_error_feedback('Error deleting module or chassis');
                });
            } else {
                self.give_error_feedback('None of the subjects are modules or chassis');
            }

        }

    });


    /** The list of status events */
    var EventsView = Backbone.View.extend({
        el: '#events-list',

        // Used in EventBroker
        interests: {
            'eventsview:reset': 'reset'
        },

        events: {
            'click thead .alert-action': 'toggleCheckboxes',
            'click thead .header': 'headerSort'
        },

        // Map columnindex to model attribute for sorting
        sortMap: {
            3: 'subject',
            4: 'alert_type.name',
            5: 'start_time'
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

            Backbone.EventBroker.register(this); // Register interests
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
        },

        reset: function() {
            alertsToChange.reset();
            this.checkBox.prop('checked', false);
        }

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
            var $container = this.$el.find('.api-html');
            if ($container.is(':empty')) {
                this.loadApiHtml($container).show();
            }
        },

        loadApiHtml: function($container) {
            var url = NAV.urls.alert_endpoint + this.model.get('id') + '/';
            var request = $.ajax(url, {
                headers: { accept: 'text/x-nav-html' }
            });
            request.done(function (response) {
                $container.html(response);
            });
            request.error(function () {
                $container.html('<div class="alert-box alert">Error fetching status details</div>');
            });
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
