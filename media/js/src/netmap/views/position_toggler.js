define([
    'netmap/collections/position',
    'libs-amd/text!netmap/templates/position_toggler.html',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Collection, Template) {
    var PositionView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="group_position[]"]': 'setPosition'
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);

            if (!this.collection) {
                this.collection = new Collection([
                    {marking:"none", "is_selected":true},
                    {marking:"room"},
                    {marking:"location"}
                ]);
            }

            Handlebars.registerHelper('capitalize', function (type) {
                return type.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
            });
            this.collection.bind("change", this.broadcastPositionFilter, this);
            return this;
        },

        render: function () {
            this.$el.html(
                this.template({collection: this.collection.toJSON()})
            );
            return this;
        },
        broadcastPositionFilter: function () {
            this.broker.trigger("netmap:changePositionFilter", this.collection);
        },
        setPosition: function (event) {

            positionToUpdate = this.collection.get($(event.currentTarget).val().toLowerCase());
            if (positionToUpdate) {
                this.collection.setAllUnselectedSilently();
                positionToUpdate.set({'is_selected': $(event.currentTarget).prop('checked')}, {'error': function (error) {
                    console.log(error);
                }});
            }
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return PositionView;
});
