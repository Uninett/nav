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
            'click .header': 'toggleWidget',
            "click #searchbox_search": "searchMap",
            "click #center_graph": "centerGraph"
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(netmapTemplate);
            this.isWidgetVisible = true;

            //this.searchbox = this.options.node;
            /*this.model.bind("change", this.render, this);
             this.model.bind("destroy", this.close, this);*/

        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        searchMap: function (e) {
            e.preventDefault();
            this.broker.trigger('netmap:search', $("input#searchbox_query", this.$el).val());
        },
        centerGraph: function (e) {
            e.preventDefault();
            this.broker.trigger('netmap:centerGraph');
        },
        render: function () {
            var out = this.template({ node: this.node, isViewEnabled: this.isViewEnabled, isWidgetVisible: this.isWidgetVisible});
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





