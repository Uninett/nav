define([
    'libs-amd/text!netmap/templates/widget_container.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function () {

    var WidgetContaierMixin = {
        toggleWidget: function () {
            this.$el.find(".body").toggle();
            this.isWidgetVisible = !this.isWidgetVisible;
        },
        isWidgetVisible: function () {
            return this.isWidgetVisible;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        }
    };
    WidgetContaierMixin.isWidgetVisible = false;
    return WidgetContaierMixin;
});
