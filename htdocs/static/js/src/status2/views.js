define([
    'status/collections',
    'libs-amd/text!status/templates/event_template.html',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate) {


    /** The main view containing the panel and the results list */
    var StatusView = Backbone.View.extend({
        el: '#status-page',

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new PanelView({
                collection: eventCollection,
                attributes: { data_api_url: this.$el.attr('data-api-url') }
            });
            new EventsView({ collection: eventCollection});

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
            console.log('Fetching data...');
            this.collection.url = this.attributes.data_api_url + '?' + this.$el.serialize();
            console.log(this.collection.url);
            var request = this.collection.fetch();
            request.done(function () {
                console.log('data fetched');
            });
        },
        preventSubmit: function (event) {
            event.preventDefault();
        }
    });


    /** The list of status events */
    var EventsView = Backbone.View.extend({
        el: '#events-list',

        initialize: function () {
            console.log('Initializing events view');
            this.body = this.$el.find('tbody');
            this.collection.on('change add reset remove', this.render, this);
        },

        render: function () {
            this.body.html('');
            this.collection.each(this.renderEvent, this);
        },

        renderEvent: function (nav_event) {
            var nav_event_view = new EventView({model: nav_event });
            this.body.append(nav_event_view.el);
        }
    });


    /** The view displaying a single status event */
    var compiledEventTemplate = Handlebars.compile(EventTemplate);
    var EventView = Backbone.View.extend({
        tagName: 'tr',
        template: compiledEventTemplate,
        initialize: function () {
            this.render();
        },
        render: function () {
            this.$el.html(this.template(this.model.attributes));
        }
    });

    return StatusView;

});
