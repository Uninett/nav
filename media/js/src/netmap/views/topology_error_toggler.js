define([
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Template) {
    var TopologyErrorView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="topologyErrors[]"]': 'setDisplayTopologyErrors'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);

            if (!this.collection) {
                this.collection = new Collection({name: "Show topology errors", value: "topologyErrors", is_selected:false});
            }
            return this;
        },

        render: function () {
            this.$el.html(
                this.template({
                    title: 'Topology errors',
                    type: 'checkbox',
                    identifier: 'topologyErrors',
                    collection: this.collection.toJSON()
                })
            );
            return this;
        },
        setDisplayTopologyErrors: function (event) {
            this.collection.at(0).set({'is_selected': $(event.currentTarget).prop('checked')});
            this.broker.trigger('netmap:changeDisplayTopologyErrors', $(event.currentTarget).prop('checked'));
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return TopologyErrorView;
});
