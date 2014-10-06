define([
    'status/collections',
    'libs-amd/text!status/templates/event_template.html',
    'libs/backbone',
    'libs/handlebars',
], function (Collections, EventTemplate) {

    var StatusView = Backbone.View.extend({
        el: '#status-page',

        initialize: function () {
            var eventCollection = new Collections.EventCollection();

            new PanelView({ collection: eventCollection});
            new EventsView({ collection: eventCollection});

        }

    });

    /* The main panel for filtering events */
    var PanelView = Backbone.View.extend({
        el: '#status-panel',

        initialize: function () {
            console.log('Initializing panel view');
        },

        events: {
            'change .event-dropdown': 'onEventDropDownChange'
        },

        /* Event driven methods */
        onEventDropDownChange: function () {
            console.log('User selected something from event dropdown');
            var request = this.collection.fetch();
            request.done(function () {
                console.log('events fetched');
            });
        }
    });

    var EventsView = Backbone.View.extend({
        el: '#events-list',

        initialize: function () {
            console.log('Initializing events view');
            this.collection.on('change add reset remove', this.render, this);
            this.body = this.$el.find('tbody');
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

    var CompiledEventTemplate = Handlebars.compile(EventTemplate);

    var EventView = Backbone.View.extend({
        tagName: 'tr',
        template: CompiledEventTemplate,
        initialize: function () {
            console.log(this.model);
            this.render();
        },
        render: function () {
            this.$el.html(this.template(this.model.attributes));
        }
    });

    return StatusView;

});
