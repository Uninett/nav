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
            Handlebars.registerHelper('round', function (value) {
                return (value && typeof value === 'number') ? Math.round(value) : 0;
            });

            // Same as each, just including index
            Handlebars.registerHelper('iter', function(context, options) {
                var fn = options.fn, inverse = options.inverse;
                var ret = "";

                if(context && context.length > 0) {
                    for(var i=0, j=context.length; i<j; i++) {
                        ret = ret + fn(_.extend({}, context[i], { percent: context.length - 1 - i, isDecade: i%10==0 }));
                    }
                } else {
                    ret = inverse(this);
                }
                return ret;
            });

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