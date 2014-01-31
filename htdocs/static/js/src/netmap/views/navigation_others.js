define([
    'netmap/views/widget_mixin',
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/navigation_others.html',
    'netmap/views/widgets/position',
    'netmap/views/widgets/algorithm',
    'netmap/views/widgets/topology_error',
    'netmap/views/widgets/mouseover',
    'netmap/views/widgets/data_refresh',
    'netmap/views/widgets/traffic_gradient',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, NetmapHelpers, netmapTemplate, PositionView, AlgorithmView, TopologyErrorView, MouseOverView, DataRefreshView, TrafficGradientView) {

    var NavigationFiltersOptionsSubView = Backbone.View.extend(_.extend({}, WidgetMixin, {
        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click .netmapWidget.hideSubWidgets > div.header': 'toggleWidget'
        },
        initialize: function () {
            this.isContentVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(netmapTemplate);
        },
        render: function () {
            var out = this.template({
                isVisible: this.isContentVisible,
                isViewEnabled: this.isViewEnabled,
                isWidgetVisible: this.isWidgetVisible,
                isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                imagePath: NAV.imagePath
            });
            this.$el.html(out);
            this.positionView = this.attachSubView(this.positionView, PositionView, {el: '#position_view'});
            this.algorithmView = this.attachSubView(this.algorithmView, AlgorithmView, {el: '#algorithm_view'});
            this.mouseOverView = this.attachSubView(this.mouseOverView, MouseOverView, {el: '#mouseover_view'});
            this.dataRefreshView = this.attachSubView(this.dataRefreshView, DataRefreshView, {el: '#datarefresh_view'});
            this.trafficGradientView = this.attachSubView(this.trafficGradientView, TrafficGradientView, {el: '#traffic_gradient_view'});

            return this;
        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();
            this.broker.trigger('netmap:resize:animate', {marginLeft: margin});
        },
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));
    return NavigationFiltersOptionsSubView;
});





