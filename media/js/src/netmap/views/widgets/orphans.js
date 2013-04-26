define([
    'netmap/views/widget_mixin',
    'netmap/resource',
    'libs-amd/text!netmap/templates/widgets/orphans.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Resource, Template) {
    var OrphanView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled",
            "netmap:changeActiveMapProperty": "setOrphansFilterFromChangedActiveMapProperty"
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="filter_orphans"]': 'setOrphansFilterFromDOM'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);
            // todo: fetch collection from api.
            if (!this.model) {
                this.model = Resource.getActiveMapModel();
            }
            this.model.bind("change:displayOrphans", this.render, this);
            return this;
        },
        render: function () {
            this.$el.html(
                this.template({model: this.model.toJSON()})
            );

            return this;
        },
        setOrphansFilterFromChangedActiveMapProperty: function (newActiveMapProperty) {
            this.model = newActiveMapProperty;
        },
        setOrphansFilterFromDOM: function (e) {
            this.model.set({'displayOrphans': !($(e.currentTarget).prop('checked'))});
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return OrphanView;
});
