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
                if (this.isWidgetVisible) {
                    this.$el.find('.title:first i').removeClass('fa-toggle-down').addClass('fa-toggle-up');
                } else {
                    this.$el.find('.title:first i').removeClass('fa-toggle-up').addClass('fa-toggle-down');
                }
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
