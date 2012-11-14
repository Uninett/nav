define([
    'netmap/models/layer_toggler',
    'libs-amd/text!netmap/templates/layer_toggler.html',
    'plugins/netmap-extras',
    'libs/handlebars',
    'libs/jquery',
    'libs/underscore',
    'libs/backbone',
    'libs/backbone-eventbroker'
], function (Model, Template, NetmapHelpers) {
    var LayerView = Backbone.View.extend({

        broker: Backbone.EventBroker,
        events: {
            'click input[name="topology[]"]': 'changeTopology',
            'change:layer': 'updateSelection' // for template logic!
        },
        initialize: function () {
            this.template = Handlebars.compile(Template);
            if (!this.model) {
                this.model = new Model();
            }

            this.model.bind("change:layer", this.updateSelection, this);
            //this.model.bind("change", this.render, this);

            return this;
        },

        render: function () {
            this.$el.html(
                this.template({model: this.model.toJSON()})
            );

            return this;
        },

        updateSelection: function () {
            // Method for telling which radio button is selected.
            // We change attributes with silent:true to not resend events!

            // Clear template state on helpers
            this.model.unset('layer2_active', {silent: true});
            this.model.unset('layer3_active', {silent: true});

            var active_layer = "layer{0}_active".format(this.model.get('layer'));
            // Update template state
            this.model.set(active_layer, true);
            this.render();
        },

        changeTopology: function (e) {
            this.broker.trigger("map:topology_change:loading");
            //e.stopPropagation();
            this.model.set({layer: $(e.currentTarget).val()});
            // todo: next one needed? should be triggered by the model itself ...
            //this.broker.trigger('map:topology_change', this.model.get('topology'));
        },

        close:function () {
            $(this.el).unbind();
            $(this.el).remove();
        }
    });

    return LayerView;
});
