define([
    'netmap/views/widget_mixin',
    'libs-amd/text!netmap/templates/widgets/algorithm.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Template) {
    var AlgorithmView = Backbone.View.extend(
        _.extend({}, WidgetMixin, {
        broker: Backbone.EventBroker,
        interests: {
            'netmap:forceRunning': 'updateStatus',
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click div.header .title': 'toggleWidget',
            'click input[name="freezeNodes"]': 'pauseLayoutAlgorithm',
            'click input[name="nodesFixed"]': 'onNodesFixedClick'
        },
        initialize: function () {
            this.isLayoutEngineRunning = true;
            this.isContentVisible = false;
            this.broker.register(this);
            this.template = Handlebars.compile(Template);

            return this;
        },
        updateStatus: function (status) {
            this.isLayoutEngineRunning = status;
            this.render();
        },
        pauseLayoutAlgorithm: function () {
            this.broker.trigger('netmap:stopLayoutForceAlgorithm', true);
            this.isLayoutEngineRunning = false;
            this.render();
        },
        onNodesFixedClick: function (e) {
            var val = $(e.currentTarget).val();
            if (val === 'Fix') {
                this.broker.trigger('netmap:nodes:setFixed', true);
            } else if (val === 'UnFix') {
                this.broker.trigger('netmap:nodes:setFixed', false);
            }
        },
        render: function () {
            this.$el.html(
                this.template({
                    isLayoutEngineRunning: this.isLayoutEngineRunning,
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible,
                    isWidgetCollapsible: !!this.options.isWidgetCollapsible,
                    imagePath: NAV.imagePath
                })
            );

            return this;
        }
    }));

    return AlgorithmView;
});
