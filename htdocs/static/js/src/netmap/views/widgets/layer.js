define([
    'netmap/views/widget_mixin',
    'netmap/resource',
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'plugins/netmap-extras',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Resources, Collection, Template, NetmapHelpers) {
    var LayerView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeActiveMapProperty": "setTopologyFromChangedActiveMapProperty"
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="topology[]"]': 'setTopologyFromDOM'

        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);

            if (!this.collection) {
                this.collection = new Collection([
                    {name:"Layer 2", value: 2},
                    {name:"Layer 3", value: 3}
                ]);
            }
            this.collection.get(Resources.getActiveMapModel().get('topology', 2)).set("is_selected", true);

            this.collection.bind("change", this.broadcastTopologyChange, this);

            return this;
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Layer',
                    type: 'radio',
                    identifier: 'topology',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
                })
            );

            return this;
        },

        broadcastTopologyChange: function (model) {
            // layer number/value is stored in Graph model, so broadcast
            // so user's using graph model can update selected topology
            this.broker.trigger("netmap:changeTopology", model.get('value'));
        },
        setTopologyFromChangedActiveMapProperty: function (newActiveMapProperty) {
            this.setTopology(newActiveMapProperty.get("topology"));
        },
        setTopologyFromDOM: function (e) {
            this.broker.trigger("map:topology_change:loading");
            this.setTopology($(e.currentTarget).val());
        },
        setTopology: function (layerID) {
            var itemInCollection = this.collection.get(layerID);
            if (itemInCollection) {
                this.collection.clearIsSelectedStatus();
                itemInCollection.set({'is_selected': true});
                this.render();
            }
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return LayerView;
});
