define([
    'status/collections',
    'libs-amd/text!status/templates/event_template.hbs',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate) {


    var alertsToClear = new Collections.EventCollection();


    /** The main view containing the panel and the results list */
    var StatusView = Backbone.View.extend({
        el: '#status-page',

        events: {
            'click .set-default': 'setDefaultStatusOptions'
        },

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new PanelView({ collection: eventCollection });
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


    /** The list of status events */
    var EventsView = Backbone.View.extend({
        el: '#events-list',

        events: {
            'click #clear-alerts-ok': 'clearAlerts',
            'click #clear-alerts-cancel': 'cancelClearAlerts'
        },

        initialize: function () {
            console.log('Initializing events view');

            this.body = this.$el.find('tbody');
            this.clearButton = this.$el.find('#clear-alerts-button');
            this.clearAlertContent = this.$el.find('#clear-alerts-content');

            this.listenTo(this.collection, 'change reset', this.render);
            this.listenTo(alertsToClear, 'change add remove reset destroy', this.updateClearButton);
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

        updateClearButton: function () {
            if (alertsToClear.length > 0) {
                this.clearButton.removeClass('notvisible');
            } else {
                this.clearButton.addClass('notvisible');
            }
        },

        clearAlerts: function () {
            console.log('Clearing alerts');
            this.hideClearAlertContent();
            alertsToClear.each(function (model) {
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

        hideClearAlertContent: function () {
            $(document).foundation('dropdown', 'close', this.clearAlertContent);
        },

        cancelClearAlerts: function () {
            this.hideClearAlertContent();
            /* TODO: Should we also reset the activated buttons on each row? */
            alertsToClear.reset();
        }
    });


    /** The view displaying a single status event */
    var compiledEventTemplate = Handlebars.compile(EventTemplate);
    var EventView = Backbone.View.extend({
        tagName: 'tr',

        events: {
            'click .action-cell .clear-alert': 'toggleClearAlert'
        },

        template: compiledEventTemplate,

        initialize: function () {
            this.render();
            this.clearButton = this.$el.find('.clear-alert');
            this.listenTo(alertsToClear, 'reset add remove', this.toggleClearButtonState);
            this.listenTo(this.model, 'destroy', this.unRender);
        },

        toggleClearAlert: function () {
            if (alertsToClear.contains(this.model)) {
                alertsToClear.remove(this.model);
            } else {
                alertsToClear.add(this.model);
            }
        },

        toggleClearButtonState: function () {
            if (alertsToClear.contains(this.model)) {
                this.clearButton.removeClass('secondary').addClass('alert');
            } else {
                this.clearButton.removeClass('alert').addClass('secondary');
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
        }
    });

    return StatusView;

});
