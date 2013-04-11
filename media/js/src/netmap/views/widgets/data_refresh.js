define([
    'netmap/resource',
    'netmap/collections/checkradio',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs-amd/text!netmap/templates/widgets/data_refresh.html',
    'plugins/netmap-extras',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Resources, Collection, Template, TemplateDataRefresh, NetmapHelpers) {
    var LayerView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeActiveMapProperty": "setRefreshIntervalFromChangedActiveMapProperty",
            "netmap:refreshIntervalCounter": 'updateCounter'
        },
        events: {
            'click input[name="dataRefreshInterval[]"]': 'setRefreshIntervalFromDom'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);
            this.templateCounter = Handlebars.compile(TemplateDataRefresh);

            if (!this.collection) {
                this.collection = new Collection([
                    {name:"No refresh", value: 0},
                    {name:"Every 2 minute", value: 2},
                    {name:"Every 10 minute", value: 10}
                ]);
            }
            this.collection.get(Resources.getActiveMapModel().get('dataRefreshInterval', 0)).set("is_selected", true);
            this.counter = Resources.getActiveMapModel().get('dataRefreshInterval', 0)*60;

            this.collection.bind("change", this.broadcastRefreshIntervalChange, this);

            return this;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        updateCounter: function (newValue) {
            this.counter = newValue;
            this.render();
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Refresh intervals',
                    type: 'radio',
                    identifier: 'dataRefreshInterval',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled
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
            this.setRefreshInterval(parseInt($(e.currentTarget).val(),10));
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
    });

    return LayerView;
});
