define([
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/navigation.html',
    'netmap/collections/traffic_gradient',
    'netmap/views/modal/traffic_gradient',
    'netmap/views/widgets/searchbox',
    'netmap/views/widgets/layer',
    'netmap/views/widgets/categories',
    'netmap/views/widgets/orphans',
    'netmap/views/widgets/position',
    'netmap/views/widgets/algorithm',
    'netmap/views/widgets/topology_error',
    'netmap/views/widgets/mouseover',
    'netmap/views/widgets/data_refresh',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (NetmapHelpers, netmapTemplate, TrafficGradientCollection, TrafficGradientView, SearchView, LayerView, CategoryView, OrphanView, PositionView, AlgorithmView, TopologyErrorView, MouseOverView, DataRefreshView) {

    var NavigationView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        interests: {
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest',
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click #toggle_view':      'toggleView',
            'click input[name="trafficGradient"]': 'onTrafficGradientClick'
        },
        initialize: function () {
            this.gradientView = null;
            this.searchView = null;
            this.categoriesView = null;
            this.orphansView = null;
            this.positionView = null;
            this.layerView = null;
            this.algorithmView = null;

            this.isContentVisible = true;
            this.broker.register(this);

            this.template = Handlebars.compile(netmapTemplate);
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        render: function () {
            var out = this.template({ isVisible: this.isContentVisible, isViewEnabled: this.isViewEnabled });
            this.$el.html(out);

            this.searchView = this.attachSubView(this.searchView, SearchView, '#search_view');
            this.layerView = this.attachSubView(this.layerView, LayerView, '#layer_view');
            this.categoriesView = this.attachSubView(this.categoriesView, CategoryView, '#categories_view');
            this.orphansView = this.attachSubView(this.orphansView, OrphanView, '#orphan_view');
            this.positionView = this.attachSubView(this.positionView, PositionView, '#position_view');
            this.algorithmView = this.attachSubView(this.algorithmView, AlgorithmView, '#algorithm_view');
            this.topologyErrorsView = this.attachSubView(this.topologyErrorsView, TopologyErrorView, '#topology_errors_view');
            this.mouseOverView = this.attachSubView(this.mouseOverView, MouseOverView, '#mouseover_view');
            this.dataRefreshView = this.attachSubView(this.dataRefreshView, DataRefreshView, '#datarefresh_view');

            return this;
        },
        alignView: function () {
            var $helper = $(this.$el);
            var $helper_content = $(".inner_wrap.left_sidebar", this.$el);

            var margin;

            if (!this.isContentVisible) {
                margin = 30;
                $helper.animate({'width': "{0}px".format(12) }, 400);
                $helper_content.fadeOut('fast');

                $("a#toggle_view", this.$el).html("&gt;&gt;");

            } else {
                margin = 170;

                $helper_content.fadeIn('fast');
                $helper.animate({'width': "{0}px".format(margin-40) }, 400);

                $("a#toggle_view", this.$el).html("&lt;&lt;");

            }

            return margin;
            //$("#netmap_main_view").animate({'margin-left': "{0}px".format(margin)}, 400);

        },
        headerFooterMinimizeRequest: function (options) {
            if (options && options.name === 'header' && (options.isShowing !== this.isContentVisible)) {
                this.toggleView();
            }
        },
        toggleView: function (e) {
            this.isContentVisible = !this.isContentVisible;
            var margin = this.alignView();
            this.broker.trigger('netmap:resize:animate', {marginLeft: margin});
        },
        onTrafficGradientClick: function (e) {
            var self = this;
            if (this.gradientView) {
                this.gradientView.close();
            }

            var gradientModel = new TrafficGradientCollection();
            gradientModel.fetch({
                success: function (model) {
                    self.gradientView = new TrafficGradientView({collection: model});
                    self.gradientView.render();
                }
            });

        },
        close:function () {
            this.layerView.close();
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return NavigationView;
});





