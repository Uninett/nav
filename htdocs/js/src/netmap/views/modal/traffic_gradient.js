define([
    'plugins/netmap-extras',
    'netmap/models/traffic_gradient',
    'libs-amd/text!netmap/templates/modal/traffic_gradient.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/jquery-ui-1.8.21.custom.min'
], function (NetmapHelpers, TrafficGradientModel, template) {

    var trafficGradientView = Backbone.View.extend({

        initialize: function () {

            this.template_post = Handlebars.compile(template);

            var self = this;
            self.el = $(self.template_post({'collection': self.collection.toJSON().reverse()})).dialog({autoOpen: false, width: 'auto'});
            self.$el = $(self.el);

        },
        render: function () {
            this.el.dialog('open');
            return this;
        },
        close: function () {
            $('#modal_traffic_gradient').dialog('destroy').remove();
            $(this.el).unbind();
            $(this.el).remove();
        }
    });
    return trafficGradientView;
});