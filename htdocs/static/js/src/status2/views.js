define([
    'status/collections',
    'libs-amd/text!status/templates/event_template.hbs',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate) {


    var alertsToChange = new Collections.EventCollection();


    /** The main view containing the panel and the results list */
    var StatusView = Backbone.View.extend({
        el: '#status-page',

        events: {
            'click .set-default': 'setDefaultStatusOptions'
        },

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new PanelView({ collection: eventCollection });
            new ActionView();
            new EventsView({ collection: eventCollection });

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
            this.listenTo(alertsToChange, 'add remove reset', this.checkState);
        },

        checkState: function () {
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
            'click thead .alert-action': 'toggleCheckboxes'
        },

        initialize: function () {
            console.log('Initializing events view');

            this.body = this.$el.find('tbody');
            this.listenTo(this.collection, 'change reset', this.render);
            this.checkBox = this.$el.find('.alert-action');
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
            'click .alert-action': 'toggleChangeAlert'
        },

        template: compiledEventTemplate,

        initialize: function () {
            this.render();
            this.checkBox = this.$el.find('.alert-action');
            this.listenTo(this.model, 'destroy', this.unRender);
            this.listenTo(alertsToChange, 'reset', this.toggleSelect);
        },

        toggleChangeAlert: function () {
            if (alertsToChange.contains(this.model)) {
                alertsToChange.remove(this.model);
                this.highlight(false);
            } else {
                alertsToChange.add(this.model);
                this.highlight(true);
            }
        },

        toggleSelect: function () {
            if (alertsToChange.contains(this.model)) {
                this.checkBox.prop('checked', true);
                this.highlight(true);
            } else {
                this.checkBox.prop('checked', false);
                this.highlight(false);
            }
        },

        render: function () {
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
            console.log(this.$el);
        }

    });

    return StatusView;

});
