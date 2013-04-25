define([
    'netmap/views/widget_mixin',
    'netmap/collections/traffic_gradient',
    'netmap/views/modal/traffic_gradient',
    'libs-amd/text!netmap/templates/widgets/traffic_gradient.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Collection, ModalView, Template) {
    var TrafficGradientView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        events: {
            'click .header': 'toggleWidget',
            'click input[name="trafficGradient"]': 'onTrafficGradientClick'
        },
        initialize: function () {
            this.gradientView = null;
            this.template = Handlebars.compile(Template);
            this.isWidgetVisible = true; // default
            return this;
        },
        onTrafficGradientClick: function (e) {
            var self = this;
            if (this.gradientView) {
                this.gradientView.close();
            }

            var gradientModel = new Collection();
            gradientModel.fetch({
                success: function (model) {
                    self.gradientView = new ModalView({collection: model});
                    self.gradientView.render();
                }
            });

        },
        render: function () {
            this.$el.html(
                this.template({
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible
                })
            );
            return this;
        },
        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return TrafficGradientView;
});
