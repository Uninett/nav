define([
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'plugins/netmap-extras',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Template, NetmapHelpers) {
    var LayerView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click input[name="topology[]"]': 'setTopology'

        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);
            if (!this.collection) {
                this.collection = new Collection([
                    {name:"Layer 2", value: 2, "is_selected":true},
                    {name:"Layer 3", value: 3}
                ]);
            }

            this.collection.bind("change", this.broadcastTopologyChange, this);

            return this;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Layer',
                    type: 'radio',
                    identifier: 'topology',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled
                })
            );

            return this;
        },

        broadcastTopologyChange: function (model) {
            // layer number/value is stored in Graph model, so broadcast
            // so user's using graph model can update selected topology
            this.broker.trigger("netmap:changeTopology", model.get('value'));
        },

        setTopology: function (e) {
            this.broker.trigger("map:topology_change:loading");

            var itemInCollection = this.collection.get($(e.currentTarget).val());
            if (itemInCollection) {
                this.collection.clearIsSelectedStatus();
                itemInCollection.set({'is_selected': $(e.currentTarget).prop('checked')});
                this.render();
            }
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return LayerView;
});
