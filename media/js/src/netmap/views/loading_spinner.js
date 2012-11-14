define([
    //'libs-amd/text!netmap/templates/loading_spinner.html',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/spin.min'
], function (Model, Template, NetmapHelpers) {
    var SpinnerView = Backbone.View.extend({
        broker: Backbone.EventBroker,
        events: {
        },
        initialize: function () {
            this.$el.append("<div id='loading_spinner'></div>");
            this.spinner = new Spinner();
            return this;
        },

        render: function () {
            console.log("SPINNING");
            this.spinner.spin(this.el);
            /*this.$el.html(
                this.template({model: this.model.toJSON()})
            );*/
            return this;
        },
        start: function () {
            this.render();
        },
        stop: function () {
            this.spinner.stop();
        },

        close:function () {
            this.spinner.stop();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return SpinnerView;
});
