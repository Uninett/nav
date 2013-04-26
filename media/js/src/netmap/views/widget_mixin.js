define([
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function () {

    var WidgetContaierMixin = {
        initWidget: function (options) {
            // widget default value should always be visible if widget isn't collapsable
            this.isWidgetVisible = !!(!!options && (!options.isWidgetCollapsible || options.isWidgetVisible));
        },
        toggleWidget: function () {
            if (!!this.options && !!this.options.isWidgetCollapsible) {
                this.$el.find(".body:first").toggle();
                this.isWidgetVisible = !this.isWidgetVisible;
            }
            return true;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        }
    };
    return WidgetContaierMixin;
});
