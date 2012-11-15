define([
    //'libs-amd/text!netmap/templates/loading_spinner.html',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker',
    'libs/spin.min'
], function (Model, Template, NetmapHelpers) {
    var SpinnerView = Backbone.View.extend({
        tagName: "div",
        id: "loading_chart",
        broker: Backbone.EventBroker,
        events: {
        },
        initialize: function () {
            var opts = {
                lines: 13, // The number of lines to draw
                length: 7, // The length of each line
                width: 6, // The line thickness
                radius: 20, // The radius of the inner circle
                corners: 1, // Corner roundness (0..1)
                rotate: 0, // The rotation offset
                color: '#000', // #rgb or #rrggbb
                speed: 1, // Rounds per second
                trail: 60, // Afterglow percentage
                shadow: true, // Whether to render a shadow
                hwaccel: true, // Whether to use hardware acceleration
                className: 'spinner', // The CSS class to assign to the spinner
                zIndex: 2e9, // The z-index (defaults to 2000000000)
                top: 'auto', // Top position relative to parent in px
                left: 'auto' // Left position relative to parent in px
            };
            this.spinner = new Spinner(opts);
            return this;
        },

        render: function () {
            this.spinner.spin(this.el);
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
