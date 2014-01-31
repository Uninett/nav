define([
    'netmap/views/widget_mixin',
    'netmap/resource',
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs-amd/text!netmap/templates/widgets/data_refresh.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Resources, Collection, Template, TemplateDataRefresh) {
    var LayerView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeActiveMapProperty": "setRefreshIntervalFromChangedActiveMapProperty",
            "netmap:refreshIntervalCounter": 'updateCounter'
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="dataRefreshInterval[]"]': 'setRefreshIntervalFromDom'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);
            this.templateCounter = Handlebars.compile(TemplateDataRefresh);

            if (!this.collection) {
                this.collection = new Collection([
                    {name:"No refresh", value: -1},
                    {name:"Every 2 minute", value: 2},
                    {name:"Every 10 minute", value: 10}
                ]);
            }
            this.collection.get(Resources.getActiveMapModel().get('dataRefreshInterval', -1)).set("is_selected", true);
            this.counter = Resources.getActiveMapModel().get('dataRefreshInterval', -1);
            this.counter = (this.counter !== -1 ? this.counter*60 : 0);
            this.collection.bind("change", this.broadcastRefreshIntervalChange, this);

            return this;
        },
        updateCounter: function (newValue) {
            this.counter = newValue;
            this.render();
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Refresh',
                    type: 'radio',
                    identifier: 'dataRefreshInterval',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
                }) +
                this.templateCounter({counter: this.counter })
            );


            return this;
        },

        broadcastRefreshIntervalChange: function (model) {
            // layer number/value is stored in Graph model, so broadcast
            // so user's using graph model can update selected topology
            this.broker.trigger("netmap:changeDataRefreshInterval", model.get('value'));
        },
        setRefreshIntervalFromChangedActiveMapProperty: function (newActiveMapProperty) {
            this.setRefreshInterval(newActiveMapProperty.get("dataRefreshInterval"));
        },
        setRefreshIntervalFromDom: function (e) {
            var intervalValueFromDom = $(e.currentTarget).val();
            this.setRefreshInterval(intervalValueFromDom);
        },
        setRefreshInterval: function (refreshIntervalValue) {
            this.broker.trigger("netmap:changeDataRefreshInterval", refreshIntervalValue);
            var itemInCollection = this.collection.get(refreshIntervalValue);
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
