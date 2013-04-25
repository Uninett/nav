define([
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function () {

    var WidgetContaierMixin = {
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
    // widget default value should always be visible if widget isn't collapsable
    WidgetContaierMixin.isWidgetVisible = (!!this.options && !!this.options.isWidgetCollapsible && this.options.isWidgetCollapsible ? false : true);
    return WidgetContaierMixin;
});
