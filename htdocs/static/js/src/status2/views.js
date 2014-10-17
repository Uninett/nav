define([
    'status/collections',
    'libs-amd/text!resources/status2/event_template.hbs',
    'moment',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate, moment) {


    var alertsToChange = new Collections.EventCollection();


    /** The main view containing the panel and the results list */
    var StatusView = Backbone.View.extend({
        el: '#status-page',

        events: {
            'click .set-default': 'setDefaultStatusOptions'
        },

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new EventsView({ collection: eventCollection });
            new PanelView({ collection: eventCollection });
            new ActionView();

            this.setDefaultButton = this.$el.find('.set-default');

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
        }

    });


    /** The main panel for filtering events */
    var PanelView = Backbone.View.extend({
        el: '#status-panel',

        initialize: function () {
            console.log('Initializing panel view');
            this.fetchData();
        },
        events: {
            'change': 'fetchData',
            'submit': 'preventSubmit'
        },

        /* Event driven methods */
        fetchData: function () {
            /* TODO: Inform user that we are trying to fetch data */
            console.log('Fetching data...');
            this.collection.url = NAV.urls.status2_api_alerthistory + '?' + this.$el.serialize();
            console.log(this.collection.url);
            var request = this.collection.fetch({ reset: true });
            request.done(function () {
                console.log('data fetched');
                $(document).foundation({dropdown: {}});
            });
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
            'click .clear-alerts': 'clearAlerts',
            'click .cancel-alerts-action': 'cancelAlertsAction'
        },

        initialize: function () {
            this.listenTo(alertsToChange, 'add remove reset', this.toggleState);
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

        },

        clearAlerts: function () {
            alertsToChange.each(function (model) {
                model.destroy({
                    wait: true,
                    success: function () {
                        console.log('model removed');
                    },
                    error: function () {
                        console.log('model not removed');
                    }
                });
            });
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
            1: 'subject',
            2: 'alert_type',
            3: 'start_time'
        },

        initialize: function () {
            console.log('Initializing events view');

            this.body = this.$('tbody');
            this.headers = this.$('thead th');
            this.applySort();

            this.listenTo(this.collection, 'sort', this.updateSortIndicators);
            this.listenTo(this.collection, 'reset', this.render);
            this.checkBox = this.$el.find('.alert-action');
        },

        applySort: function () {
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
            this.body.html('');
            this.collection.each(this.renderEvent, this);
        },

        renderEvent: function (nav_event) {
            var nav_event_view = new EventView({model: nav_event});
            this.body.append(nav_event_view.el);
        },

        toggleCheckboxes: function () {
            if (this.checkBox.prop('checked')) {
                alertsToChange.reset(this.collection.models);
            } else {
                alertsToChange.reset();
            }
        }

    });


    /** The view displaying a single status event */
    var compiledEventTemplate = Handlebars.compile(EventTemplate);
    var EventView = Backbone.View.extend({
        tagName: 'tr',

        events: {
            'click .alert-action': 'toggleChangeState'
        },

        template: compiledEventTemplate,

        initialize: function () {
            this.render();
            this.checkBox = this.$el.find('.alert-action');
            this.listenTo(this.model, 'destroy', this.unRender);
            this.listenTo(alertsToChange, 'reset', this.toggleSelect);
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
            if (alertsToChange.contains(this.model)) {
                this.checkBox.prop('checked', true);
                this.highlight(true);
            } else {
                this.checkBox.prop('checked', false);
                this.highlight(false);
            }
        },

        render: function () {
            this.model.set('formatted_start_time',
                moment(this.model.get('start_time')).format('YYYY-MM-DD HH:mm:ss'));
            this.$el.html(this.template(this.model.attributes));
        },

        unRender: function () {
            console.log('Unrender called');
            this.$el.fadeOut(function () {
                this.remove();
            });
        },

        highlight: function (flag) {
            this.$el.toggleClass('highlight', flag);
        }

    });

    return StatusView;

});
