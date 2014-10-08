define([
    'status/collections',
    'libs-amd/text!status/templates/event_template.html',
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

        },

        setDefaultStatusOptions: function () {
            /* TODO: Inform user about success and error */
            var request = $.post(
                NAV.urls.status2_save_preferences,
                this.$el.find('form').serialize()
            );
            request.done(function(){
                console.log('Default status set');
            });
            request.fail(function(){
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
            var request = this.collection.fetch();
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
            'click thead .clear-alert': 'clearAlerts'
        },

        initialize: function () {
            console.log('Initializing events view');

            this.body = this.$el.find('tbody');
            this.clearButton = this.$el.find('thead .clear-alert');

            this.collection.on('change reset', this.render, this);
            alertsToClear.on('change add remove reset', this.updateClearButton, this);
        },

        render: function () {
            this.body.html('');
            this.collection.each(this.renderEvent, this);
        },

        renderEvent: function (nav_event) {
            var nav_event_view = new EventView({model: nav_event});
            this.body.append(nav_event_view.el);
        },

        updateClearButton: function () {
            if (alertsToClear.length > 0) {
                this.clearButton.removeClass('hidden');
            } else {
                this.clearButton.addClass('hidden');
            }
        },

        clearAlerts: function () {
            console.log('Clearing alerts');
            var self = this;
            alertsToClear.each(function (model) {
                /* TODO: Do the clearing request here */
                self.collection.remove(model);
            });
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
            this.model.on('remove', this.unRender, this);
        },

        toggleClearAlert: function () {
            if (alertsToClear.contains(this.model)) {
                alertsToClear.remove(this.model);
                this.clearButton.removeClass('alert').addClass('secondary');
            } else {
                alertsToClear.add(this.model);
                this.clearButton.removeClass('secondary').addClass('alert');
            }
        },

        render: function () {
            this.$el.html(this.template(this.model.attributes));
        },

        unRender: function () {
            this.model.off();
            this.$el.fadeOut(function () {
                this.remove();
            });
        }
    });

    return StatusView;

});
