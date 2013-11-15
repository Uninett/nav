define([
    'netmap/views/widget_mixin',
    'plugins/netmap-extras',
    'libs-amd/text!netmap/templates/navigation_filters_options.html',
    'netmap/views/widgets/layer',
    'netmap/views/widgets/categories',
    'netmap/views/widgets/orphans',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, NetmapHelpers, netmapTemplate, LayerView, CategoryView, OrphanView) {

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
            this.layerView = this.attachSubView(this.layerView, LayerView, {el: '#layer_view'});
            this.categoriesView = this.attachSubView(this.categoriesView, CategoryView, {el: '#categories_view'});
            this.orphansView = this.attachSubView(this.orphansView, OrphanView, {el: '#orphan_view'});

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





