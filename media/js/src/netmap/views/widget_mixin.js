define([
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function () {

    var WidgetContaierMixin = {
        toggleWidget: function () {
            this.$el.find(".body").toggle();
            this.isWidgetVisible = !this.isWidgetVisible;
            return true;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        }
    };
    WidgetContaierMixin.isWidgetVisible = false;
    return WidgetContaierMixin;
});
