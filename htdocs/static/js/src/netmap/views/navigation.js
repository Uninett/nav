define([
    'netmap/views/widget_mixin',
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/navigation.html',
    'netmap/views/widgets/searchbox',
    'netmap/views/navigation_filters_options',
    'netmap/views/navigation_others',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, NetmapHelpers, netmapTemplate, SearchView, FiltersOptionsContainerView, OthersContainerView) {

    var NavigationView = Backbone.View.extend(_.extend({}, WidgetMixin, {
        broker: Backbone.EventBroker,
        interests: {
            'headerFooterMinimize:trigger': 'headerFooterMinimizeRequest',
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click #toggle_view':      'toggleView'
        },
        initialize: function () {
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

            this.searchWidget = this.attachSubView(this.searchWidget,
                SearchView,
                {
                    el: '#search_view',
                    isWidgetCollapsible: true,
                    isWidgetVisible: true
                }
            );

            this.containerFilterOptions = this.attachSubView(this.containerFilterOptions,
                FiltersOptionsContainerView,
                {
                    el: '#widget_container_filter_options',
                    isWidgetCollapsible: true
                }
            );
            this.containerOthers = this.attachSubView(this.containerOthers,
                OthersContainerView,
                {
                    el: '#widget_container_others',
                    isWidgetCollapsible: true
                }
            );

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
                $helper.animate({'width': "{0}px".format(margin-15) }, 400);

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
        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));
    return NavigationView;
});





