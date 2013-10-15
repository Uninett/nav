define([
    'netmap/views/widget_mixin',
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/widgets/searchbox.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, NetmapHelpers, netmapTemplate) {

    var SearchboxView = Backbone.View.extend(_.extend({}, WidgetMixin, {
        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click .header .title': 'toggleWidget',
            'click #searchbox_search': 'searchMap',
            'click #center_graph': 'centerGraph'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(netmapTemplate);
            this.isWidgetVisible = true;
        },
        searchMap: function (e) {
            e.preventDefault();
            this.broker.trigger('netmap:search', $("input#searchbox_query", this.$el).val());
            return true;
        },
        centerGraph: function (e) {
            e.preventDefault();
            this.broker.trigger('netmap:centerGraph');
            return true;
        },
        render: function () {
            var out = this.template({
                node: this.node,
                isViewEnabled: this.isViewEnabled,
                isWidgetVisible: this.isWidgetVisible,
                isWidgetCollapsible: !!this.options.isWidgetCollapsible
            });
            this.$el.html(out);
            return this;
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));
    return SearchboxView;
});





