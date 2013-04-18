define([
    'netmap/views/widget_mixin',
    'netmap/collections/position',
    'libs-amd/text!netmap/templates/checkradio.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (WidgetMixin, Collection, Template) {
    var PositionView = Backbone.View.extend(_.extend({}, WidgetMixin, {

        broker: Backbone.EventBroker,
        interests: {
            "netmap:graph:isDoneLoading": "setIsViewEnabled"
        },
        events: {
            'click .header': 'toggleWidget',
            'click input[name="group_position[]"]': 'setPosition'
        },
        initialize: function () {
            this.broker.register(this);
            this.template = Handlebars.compile(Template);

            if (!this.collection) {
                this.collection = new Collection([
                    {name:"none", "is_selected":true},
                    {name:"room"},
                    {name:"location"}
                ]);
            }

            this.collection.bind("change", this.broadcastPositionFilter, this);
            return this;
        },
        setIsViewEnabled: function (boolValue) {
            this.isViewEnabled = boolValue;
            this.render();
        },
        render: function () {
            this.$el.html(
                this.template({
                    title: 'Mark by position',
                    type: 'radio',
                    identifier: 'group_position',
                    collection: this.collection.toJSON(),
                    isViewEnabled: this.isViewEnabled,
                    isWidgetVisible: this.isWidgetVisible
                })
            );
            return this;
        },
        broadcastPositionFilter: function () {
            this.broker.trigger("netmap:changePosition", this.collection);
        },
        setPosition: function (event) {

            positionToUpdate = this.collection.get($(event.currentTarget).val().toLowerCase());
            if (positionToUpdate) {
                this.collection.setAllUnselectedSilently();
                positionToUpdate.set({'is_selected': $(event.currentTarget).prop('checked')}, {'error': function (error) {
                    alert(error);
                }});
            }
        },

        close:function () {
            this.broker.unregister(this);
            $(this.el).unbind();
            $(this.el).remove();
        }
    }));

    return PositionView;
});
