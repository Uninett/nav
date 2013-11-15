define([
    'netmap/views/widget_mixin',
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Collection, Template) {
    var TopologyErrorView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="topologyErrors[]"]': 'setDisplayTopologyErrorsFromDOM'
        },
        initialize: function () {
            this.broker.register(this);
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
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
                })
            );
            return this;
        },
        setDisplayTopologyErrorsFromDOM: function (event) {
            this.setDisplayTopology($(event.currentTarget).prop('checked'));
            this.broker.trigger('netmap:changeDisplayTopologyErrors', $(event.currentTarget).prop('checked'));
        },
        setDisplayTopology: function (boolValue) {
            this.collection.at(0).set({'is_selected': boolValue});
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return TopologyErrorView;
});
